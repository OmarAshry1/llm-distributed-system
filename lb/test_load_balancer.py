from common.models import Response
from lb.load_balancer import LoadBalancer
from lb.strategies import LeastConnections, LoadAware, RoundRobin


class Request:
    def __init__(self, request_id, client_id):
        self.id = request_id
        self.client_id = client_id
        self.query = "test"


class DummyWorker:
    def __init__(self, worker_id, fail=False, fail_after=False, capacity=8):
        self.id = worker_id
        self.is_alive = True
        self.active_connections = 0
        self.capacity = capacity
        self.handled = 0
        self.fail = fail
        self.fail_after = fail_after

    def increment_load(self):
        self.active_connections += 1

    def decrement_load(self):
        self.active_connections = max(0, self.active_connections - 1)

    def queue_length(self):
        return 0

    def utilization_percent(self):
        return 0

    def process(self, request):
        if self.fail:
            self.is_alive = False
            raise RuntimeError("worker failed")

        self.handled += 1

        if self.fail_after:
            self.is_alive = False
            raise RuntimeError("worker failed during processing")

        return Response(
            id=request.id,
            worker_id=self.id,
            result="ok",
            latency=0.01,
        )


def test_round_robin_distributes_requests():
    workers = [DummyWorker(0), DummyWorker(1), DummyWorker(2)]
    lb = LoadBalancer(workers, RoundRobin())

    worker_ids = [
        lb.dispatch(Request(str(i), client_id=i)).worker_id
        for i in range(6)
    ]

    assert worker_ids == [0, 1, 2, 0, 1, 2]


def test_sticky_session_routes_same_client_to_same_worker():
    workers = [DummyWorker(0), DummyWorker(1)]
    lb = LoadBalancer(workers, RoundRobin())

    first = lb.dispatch(Request("first", client_id=10))
    second = lb.dispatch(Request("second", client_id=10))

    assert first.worker_id == second.worker_id


def test_failed_sticky_worker_is_reassigned():
    workers = [DummyWorker(0), DummyWorker(1)]
    lb = LoadBalancer(workers, RoundRobin())

    first = lb.dispatch(Request("first", client_id=7))
    workers[first.worker_id].is_alive = False
    second = lb.dispatch(Request("second", client_id=7))

    assert second.success is True
    assert second.worker_id != first.worker_id


def test_inflight_failure_retries_another_worker():
    workers = [DummyWorker(0, fail_after=True), DummyWorker(1)]
    lb = LoadBalancer(workers, RoundRobin(), max_retries=2)

    response = lb.dispatch(Request("retry", client_id=99))

    assert response.success is True
    assert response.worker_id == 1
    assert response.attempts == 2


def test_all_workers_down_returns_structured_failure():
    workers = [DummyWorker(0), DummyWorker(1)]
    for worker in workers:
        worker.is_alive = False

    lb = LoadBalancer(workers, RoundRobin())
    response = lb.dispatch(Request("down", client_id=1))

    assert response.success is False
    assert response.error == "All workers are down!"


def test_least_connections_selects_lowest_load():
    workers = [DummyWorker(0), DummyWorker(1)]
    workers[0].active_connections = 5
    workers[1].active_connections = 1

    assert LeastConnections().get_worker(workers).id == 1


def test_load_aware_prefers_worker_under_threshold():
    workers = [DummyWorker(0), DummyWorker(1)]
    workers[0].active_connections = 6
    workers[1].active_connections = 2

    assert LoadAware(threshold=5).get_worker(workers).id == 1


def test_load_aware_prefers_lower_capacity_ratio():
    small = DummyWorker(0, capacity=2)
    large = DummyWorker(1, capacity=8)
    small.active_connections = 1
    large.active_connections = 2

    assert LoadAware(threshold=8).get_worker([small, large]).id == 1
