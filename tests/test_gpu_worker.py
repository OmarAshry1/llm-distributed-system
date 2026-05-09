import time

from common.models import Request
from workers.gpu_worker import Worker


def test_worker_process_uses_injected_llm(monkeypatch):
    import llm.inference as inf

    monkeypatch.setattr(inf, "run_llm", lambda q, session_id: "synthetic result")
    w = Worker(3, capacity=4)
    req = Request("id-1", "what is the load test?", 99)
    resp = w.process(req)
    assert resp.success
    assert resp.worker_id == 3
    assert "synthetic" in resp.result
    assert resp.latency >= 0


def test_utilization_percent_bounded():
    w = Worker(0, capacity=2)
    time.sleep(0.01)
    u = w.utilization_percent()
    assert 0.0 <= u <= 100.0


def test_queue_length_when_over_capacity():
    w = Worker(0, capacity=1)
    w.active_connections = 3
    assert w.queue_length() == 2
