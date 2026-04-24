import time
from rag.rag_engine import query_rag_with_memory

# no context handedling hena kolo m3molo handle fel rag engine
def run_llm(query, session_id):
    time.sleep(0.1)
    return query_rag_with_memory(query, session_id)