import pytest

pytest.importorskip("langchain")


def test_initialize_rag_rejects_empty_paths(reset_rag_state):
    from rag.rag_engine import initialize_rag

    with pytest.raises(ValueError, match="At least one PDF path is required"):
        initialize_rag([])


def test_conversational_chain_requires_initialized_rag(reset_rag_state):
    import rag.rag_engine as re

    re.vectorstore = None
    re.rag_chain = None
    re._rag_ready = False
    from rag.rag_engine import get_conversational_chain

    with pytest.raises(RuntimeError, match="not initialized"):
        get_conversational_chain()


def test_resolve_config_reads_ollama_model_env(monkeypatch, reset_rag_state):
    monkeypatch.setenv("OLLAMA_MODEL", "test-model-xyz")
    from rag import rag_engine as re

    cfg = re._resolve_config(None, None, None, None, None, None, False)
    assert cfg["model_name"] == "test-model-xyz"
