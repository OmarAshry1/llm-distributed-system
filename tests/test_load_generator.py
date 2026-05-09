import time

from client.load_generator import run_load_test, simulate_user
from common.models import Request, Response
from common.metrics import MetricsCollector
class CountingScheduler:
    def __init__(self):
        self.calls = []

    def handle_request(self, request):
        self.calls.append(request.id)
        return Response(
            id=request.id,
            worker_id=0,
            result="ok",
            latency=0.001,
            success=True,
        )


def test_run_load_test_invokes_expected_request_count():
    sched = CountingScheduler()
    run_load_test(sched, num_users=4, requests_per_user=2, workers=None)
    assert len(sched.calls) == 8


def test_simulate_user_records_metrics():
    sched = CountingScheduler()
    m = MetricsCollector()
    m.started_at = time.time()
    simulate_user(sched, user_id=5, requests_per_user=2, metrics=m)
    m.finish()
    s = m.summary()
    assert s["total_requests"] == 2
    assert s["successful_requests"] == 2
