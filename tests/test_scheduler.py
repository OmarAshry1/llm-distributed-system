from common.models import Request, Response
from master.scheduler import Scheduler


def test_scheduler_delegates_to_load_balancer():
    class FakeLB:
        def __init__(self):
            self.seen = None

        def dispatch(self, request):
            self.seen = request
            return Response(
                id=request.id,
                worker_id=0,
                result="ok",
                latency=0.02,
                success=True,
            )

    lb = FakeLB()
    sched = Scheduler(lb)
    req = Request("r1", "q", 7)
    out = sched.handle_request(req)
    assert lb.seen is req
    assert out.success and out.worker_id == 0


def test_route_request_alias():
    class FakeLB:
        def dispatch(self, request):
            return Response(
                id=request.id,
                worker_id=1,
                result="x",
                latency=0.0,
                success=True,
            )

    s = Scheduler(FakeLB())
    r = s.route_request(Request("a", "b", 0))
    assert r.worker_id == 1
