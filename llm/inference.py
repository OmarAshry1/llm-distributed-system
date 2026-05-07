import os
import time
from rag.rag_engine import query_rag_with_memory


def _simulation_delay():
    try:
        return max(0.0, float(os.getenv("SIMULATED_LLM_DELAY", "0")))
    except ValueError:
        print("[LLM] Invalid SIMULATED_LLM_DELAY; using 0.")
        return 0.0


# Context handling is owned by the RAG engine.
def run_llm(query, session_id):
    delay = _simulation_delay()
    if delay:
        time.sleep(delay)

    return query_rag_with_memory(query, session_id)
