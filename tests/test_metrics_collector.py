from common.metrics import MetricsCollector
from common.models import Response


def test_metrics_records_success_latency_and_worker():
    m = MetricsCollector()
    m.record(
        Response(
            id="1",
            worker_id=2,
            result="ok",
            latency=0.05,
            success=True,
            attempts=1,
        )
    )
    s = m.summary()
    assert s["successful_requests"] == 1
    assert s["failed_requests"] == 0
    assert s["total_requests"] == 1
    assert s["avg_latency_seconds"] == 0.05
    assert s["per_worker_requests"] == {2: 1}


def test_metrics_records_failure_without_latency():
    m = MetricsCollector()
    m.record(Response(id="2", worker_id=1, result="", latency=0.1, success=False))
    s = m.summary()
    assert s["successful_requests"] == 0
    assert s["failed_requests"] == 1
    assert s["avg_latency_seconds"] == 0


def test_metrics_p95_matches_sorted_percentile():
    m = MetricsCollector()
    latencies = [0.01 * i for i in range(1, 101)]
    for i, lat in enumerate(latencies):
        m.record(Response(id=str(i), worker_id=0, result="x", latency=lat, success=True))
    s = m.summary()
    sorted_lat = sorted(latencies)
    idx = max(0, int(len(sorted_lat) * 0.95) - 1)
    assert s["p95_latency_seconds"] == round(sorted_lat[idx], 4)


def test_metrics_worker_utilization_pass_through():
    class W:
        def __init__(self, wid):
            self.id = wid

        def utilization_percent(self):
            return 42.5 + self.id

    workers = [W(0), W(1)]
    m = MetricsCollector()
    m.finish()
    s = m.summary(workers=workers)
    assert s["worker_utilization_percent"] == {0: 42.5, 1: 43.5}
