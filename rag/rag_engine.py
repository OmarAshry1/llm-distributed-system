import hashlib
import os
import threading
import json
import warnings
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlopen

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

try:
    from chromadb.config import Settings as ChromaSettings
except Exception:
    ChromaSettings = None


os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
warnings.filterwarnings(
    "ignore",
    message=".*RunnableWithMessageHistory.*deprecated.*",
    category=Warning,
)

# el state da shared 3ashan el rag yinitialize mara wa7da
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


def _env_optional_int(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        return None

    try:
        number = int(value)
        if number < 1:
            raise ValueError
        return number
    except ValueError:
        print(f"[RAG] Ignoring invalid {name}={value!r}; expected a positive integer.")
        return None


def _env_optional_float(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        return None

    try:
        return float(value)
    except ValueError:
        print(f"[RAG] Ignoring invalid {name}={value!r}; expected a number.")
        return None


def _env_ollama_keep_alive():
    value = os.getenv("OLLAMA_KEEP_ALIVE")
    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    # ollama by7eb el duration teb2a zay -1m mesh -1 bas
    if value.lstrip("-").isdigit() and value != "0":
        return f"{value}m"
    return value


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
        "model_name": model_name or os.getenv("OLLAMA_MODEL", "mistral"),
        "embedding_model": embedding_model
        or os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        "chunk_size": chunk_size or _env_int("RAG_CHUNK_SIZE", 1000),
        "chunk_overlap": chunk_overlap or _env_int("RAG_CHUNK_OVERLAP", 200),
        "retriever_k": retriever_k or _env_int("RAG_RETRIEVER_K", 4),
        "force_rebuild": force_rebuild or _env_bool("RAG_FORCE_REBUILD"),
        "ollama_num_predict": _env_optional_int("OLLAMA_NUM_PREDICT"),
        "ollama_num_ctx": _env_optional_int("OLLAMA_NUM_CTX"),
        "ollama_num_thread": _env_optional_int("OLLAMA_NUM_THREAD"),
        "ollama_temperature": _env_optional_float("OLLAMA_TEMPERATURE"),
        "ollama_keep_alive": _env_ollama_keep_alive(),
    }


def _ollama_options(config):
    options = {
        "num_predict": config["ollama_num_predict"],
        "num_ctx": config["ollama_num_ctx"],
        "num_thread": config["ollama_num_thread"],
        "temperature": config["ollama_temperature"],
        "keep_alive": config["ollama_keep_alive"],
    }
    return {key: value for key, value in options.items() if value is not None}


def _chroma_settings():
    if ChromaSettings is None:
        return None
    return ChromaSettings(anonymized_telemetry=False)


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
            client_settings=_chroma_settings(),
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
        client_settings=_chroma_settings(),
    )

    persist = getattr(store, "persist", None)
    if persist:
        persist()

    return store


def _check_ollama_model_available(base_url, model_name):
    tags_url = urljoin(base_url.rstrip("/") + "/", "api/tags")
    try:
        with urlopen(tags_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(
            f"Ollama server at {base_url} returned HTTP {error.code} while checking installed models."
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"Cannot connect to Ollama at {base_url}. Start Ollama with `ollama serve`."
        ) from error
    except TimeoutError as error:
        raise RuntimeError(
            f"Timed out connecting to Ollama at {base_url}. Check that Ollama is running."
        ) from error

    installed = {
        item.get("name") or item.get("model")
        for item in payload.get("models", [])
    }
    installed.discard(None)
    accepted_names = {model_name}
    if ":" not in model_name:
        accepted_names.add(f"{model_name}:latest")

    if installed.isdisjoint(accepted_names):
        available = ", ".join(sorted(installed)) or "none"
        raise RuntimeError(
            f"Ollama model {model_name!r} is not installed. "
            f"Run `ollama pull {model_name}` or set OLLAMA_MODEL to one of: {available}."
        )


# el function de btzbot el rag pipeline men el pdf lel ollama chain
def initialize_rag(
    pdf_paths,
    persist_directory=None,
    model_name=None,
    embedding_model=None,
    chunk_size=None,
    chunk_overlap=None,
    retriever_k=None,
    force_rebuild=False,
    ollama_base_url=None,
):
    global vectorstore, rag_chain, _rag_ready

    with _init_lock:
        if _rag_ready and rag_chain is not None:
            print("[RAG] Already initialized")
            return rag_chain

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

        embeddings = HuggingFaceEmbeddings(
            model_name=config["embedding_model"]
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"]
        )

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

        base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = config["model_name"]
        _check_ollama_model_available(base_url, model)
        print(f"[RAG] Using Ollama model: {model} at {base_url}")
        ollama_options = _ollama_options(config)
        if ollama_options:
            print(f"[RAG] Ollama options: {ollama_options}")
        llm = ChatOllama(
            base_url=base_url,
            model=model,
            **ollama_options,
        )

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


# el function de betnady el chain bel memory beta3 kol session
def query_rag_with_memory(query, session_id):
    chain = get_conversational_chain()

    result = chain.invoke(
        {"input": query},
        config={"configurable": {"session_id": session_id}}
    )

    return result.get("answer", "I do not know.")
