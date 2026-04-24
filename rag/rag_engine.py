import os
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

#global variables
vectorstore = None
rag_chain = None

# initialize el rag -  run only once 
# Workflow dataa ->chunks -> embedding -> store in db -> retriever-> chains of llm + retriever with correct prompts
# session history memory is stored fa kol worker leh memory
def initialize_rag(pdf_paths, groq_api_key):
    global vectorstore, rag_chain

    print("Tam initialization el rag")

    # Load PDFs
    documents = []
    for path in pdf_paths:
        loader = PyPDFLoader(path)
        documents.extend(loader.load())

    # Split aw chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = splitter.split_documents(documents)

    # Embeddings -> sparse vectors
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # Vector DB
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings
    )

    retriever = vectorstore.as_retriever()

    # LLM
    llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="Gemma2-9b-It"
    )

    # Prompt
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the retrieved context to answer. "
        "If unknown, say you don't know. "
        "Max 3 sentences.\n\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"), 
        ("human", "{input}")
    ])

    qa_chain = create_stuff_documents_chain(llm, prompt)

    rag_chain = create_retrieval_chain(retriever, qa_chain)

    print("Rag Gahez")


## history-aware wrapper

_store ={}
def get_session_history(session_id):
    if session_id not in _store:
        _store[session_id] = ChatMessageHistory()
    return _store[session_id]

def get_conversational_chain():
    return RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

# invoking el llm aw el inference
def query_rag_with_memory(query, session_id):
    chain = get_conversational_chain()

    result = chain.invoke(
        {"input": query},
        config={"configurable": {"session_id": session_id}}
    )

    return result["answer"]