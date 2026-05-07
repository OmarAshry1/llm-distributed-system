import hashlib
import os
import threading
from pathlib import Path

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# Global RAG state. Initialization happens once before workers start serving requests.
vectorstore = None
rag_chain = None
_rag_ready = False
_init_lock = threading.Lock()
_history_lock = threading.Lock()


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PERSIST_DIR = BASE_DIR / "rag" / "chroma_db"


def _env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    try:
        number = int(value)
        if number < 1:
            raise ValueError
        return number
    except ValueError:
        print(f"[RAG] Invalid {name}={value!r}; using default {default}.")
        return default


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_config(
    persist_directory,
    model_name,
    embedding_model,
    chunk_size,
    chunk_overlap,
    retriever_k,
    force_rebuild,
):
    return {
        "persist_directory": Path(
            persist_directory or os.getenv("RAG_PERSIST_DIR", DEFAULT_PERSIST_DIR)
        ),
        "model_name": model_name or os.getenv("GROQ_MODEL", "gemma2-9b-it"),
        "embedding_model": embedding_model
        or os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        "chunk_size": chunk_size or _env_int("RAG_CHUNK_SIZE", 1000),
        "chunk_overlap": chunk_overlap or _env_int("RAG_CHUNK_OVERLAP", 200),
        "retriever_k": retriever_k or _env_int("RAG_RETRIEVER_K", 4),
        "force_rebuild": force_rebuild or _env_bool("RAG_FORCE_REBUILD"),
    }


def _pdf_fingerprint(pdf_paths):
    digest = hashlib.sha256()
    for raw_path in sorted(str(Path(path).resolve()) for path in pdf_paths):
        path = Path(raw_path)
        stat = path.stat()
        digest.update(raw_path.encode("utf-8"))
        digest.update(str(stat.st_size).encode("utf-8"))
        digest.update(str(int(stat.st_mtime)).encode("utf-8"))
    return digest.hexdigest()[:16]


def _load_documents(pdf_paths):
    documents = []
    for path in pdf_paths:
        loader = PyPDFLoader(path)
        documents.extend(loader.load())
    return documents


def _build_or_load_vectorstore(pdf_paths, embeddings, splitter, persist_directory, force_rebuild):
    collection_dir = persist_directory / _pdf_fingerprint(pdf_paths)
    db_exists = (collection_dir / "chroma.sqlite3").exists()

    if db_exists and not force_rebuild:
        print(f"[RAG] Loading persisted vector DB from {collection_dir}")
        return Chroma(
            persist_directory=str(collection_dir),
            embedding_function=embeddings,
        )

    print("[RAG] Building vector DB from PDF documents")
    documents = _load_documents(pdf_paths)
    splits = splitter.split_documents(documents)

    if not splits:
        raise ValueError("No text chunks were extracted from the configured PDF files.")

    collection_dir.mkdir(parents=True, exist_ok=True)
    store = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=str(collection_dir),
    )

    persist = getattr(store, "persist", None)
    if persist:
        persist()

    return store


# initialize el rag - run once before serving requests.
# Workflow: PDFs -> chunks -> embeddings -> vector DB -> retriever -> LLM chain.
def initialize_rag(
    pdf_paths,
    groq_api_key,
    persist_directory=None,
    model_name=None,
    embedding_model=None,
    chunk_size=None,
    chunk_overlap=None,
    retriever_k=None,
    force_rebuild=False,
):
    global vectorstore, rag_chain, _rag_ready

    with _init_lock:
        if _rag_ready and rag_chain is not None:
            print("[RAG] Already initialized")
            return rag_chain

        if not groq_api_key:
            raise ValueError("GROQ_API_KEY is required to initialize RAG.")

        if not pdf_paths:
            raise ValueError("At least one PDF path is required to initialize RAG.")

        config = _resolve_config(
            persist_directory,
            model_name,
            embedding_model,
            chunk_size,
            chunk_overlap,
            retriever_k,
            force_rebuild,
        )

        print("[RAG] Initializing")

    # Embeddings -> sparse vectors
        embeddings = HuggingFaceEmbeddings(
            model_name=config["embedding_model"]
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"]
        )

    # Vector DB
        vectorstore = _build_or_load_vectorstore(
            pdf_paths=pdf_paths,
            embeddings=embeddings,
            splitter=splitter,
            persist_directory=config["persist_directory"],
            force_rebuild=config["force_rebuild"],
        )

        retriever = vectorstore.as_retriever(
            search_kwargs={"k": config["retriever_k"]}
        )

    # LLM
        llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name=config["model_name"]
        )

    # Prompt
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the retrieved context to answer. "
            "If the answer is not in the context, say you do not know. "
            "Keep the answer concise.\n\n{context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])

        qa_chain = create_stuff_documents_chain(llm, prompt)

        rag_chain = create_retrieval_chain(retriever, qa_chain)
        _rag_ready = True

        print("[RAG] Ready")
        return rag_chain


## history-aware wrapper

_store = {}
def get_session_history(session_id):
    with _history_lock:
        if session_id not in _store:
            _store[session_id] = ChatMessageHistory()
        return _store[session_id]

def get_conversational_chain():
    if rag_chain is None:
        raise RuntimeError("RAG chain is not initialized.")

    return RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

# invoking el llm aw el inference
def query_rag_with_memory(query, session_id):
    try:
        chain = get_conversational_chain()

        result = chain.invoke(
            {"input": query},
            config={"configurable": {"session_id": session_id}}
        )

        return result.get("answer", "I do not know.")
    except Exception as error:
        return f"RAG/LLM error: {error}"
