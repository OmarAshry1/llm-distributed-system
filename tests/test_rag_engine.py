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


def test_resolve_config_reads_ollama_tuning_env(monkeypatch, reset_rag_state):
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "128")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")
    monkeypatch.setenv("OLLAMA_NUM_THREAD", "8")
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "0")
    monkeypatch.setenv("OLLAMA_KEEP_ALIVE", "-1")
    from rag import rag_engine as re

    cfg = re._resolve_config(None, None, None, None, None, None, False)
    assert re._ollama_options(cfg) == {
        "num_predict": 128,
        "num_ctx": 2048,
        "num_thread": 8,
        "temperature": 0.0,
        "keep_alive": "-1m",
    }


def test_check_ollama_model_available_rejects_missing_model(monkeypatch, reset_rag_state):
    from rag import rag_engine as re

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"models": [{"name": "mistral:latest"}]}'

    monkeypatch.setattr(re, "urlopen", lambda url, timeout: FakeResponse())

    with pytest.raises(RuntimeError, match="gemma:2b.*not installed"):
        re._check_ollama_model_available("http://localhost:11434", "gemma:2b")


def test_check_ollama_model_available_accepts_latest_tag(monkeypatch, reset_rag_state):
    from rag import rag_engine as re

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"models": [{"name": "mistral:latest"}]}'

    monkeypatch.setattr(re, "urlopen", lambda url, timeout: FakeResponse())

    re._check_ollama_model_available("http://localhost:11434", "mistral")


def test_query_rag_with_memory_propagates_chain_errors(monkeypatch, reset_rag_state):
    from rag import rag_engine as re

    class BrokenChain:
        def invoke(self, payload, config):
            raise RuntimeError("model missing")

    monkeypatch.setattr(re, "get_conversational_chain", lambda: BrokenChain())

    with pytest.raises(RuntimeError, match="model missing"):
        re.query_rag_with_memory("hello", "session-1")
