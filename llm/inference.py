# Context handling is owned by the RAG engine.
def run_llm(query, session_id):
    from rag.rag_engine import query_rag_with_memory

    return query_rag_with_memory(query, session_id)
