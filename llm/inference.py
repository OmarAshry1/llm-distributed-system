import os
import time


def _mock_llm_enabled():
    return os.getenv("MOCK_LLM", "").strip().lower() in {"1", "true", "yes", "on"}


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

    if _mock_llm_enabled():
        return f"[mock-llm] session={session_id} query_chars={len(query)}"

    from rag.rag_engine import query_rag_with_memory

    return query_rag_with_memory(query, session_id)
