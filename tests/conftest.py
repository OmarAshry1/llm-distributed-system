import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def reset_rag_state():
    import rag.rag_engine as re

    prev = (re.vectorstore, re.rag_chain, re._rag_ready)
    re.vectorstore = None
    re.rag_chain = None
    re._rag_ready = False
    yield
    re.vectorstore, re.rag_chain, re._rag_ready = prev
