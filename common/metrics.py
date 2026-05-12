import statistics
import threading
import time
from collections import Counter


class MetricsCollector:
    def __init__(self):
        self.started_at = time.time()
        self.finished_at = None
        self._lock = threading.Lock()
        self._latencies = []
        self._worker_counts = Counter()
        self._failure_errors = Counter()
        self._failures = 0
        self._successes = 0
        self._attempts = 0

    def record(self, response):
        with self._lock:
            self._attempts += getattr(response, "attempts", 1)
            if getattr(response, "success", False):
                self._successes += 1
                self._latencies.append(response.latency)
            else:
                self._failures += 1
                error = getattr(response, "error", None)
                if error:
                    self._failure_errors[str(error)] += 1

            worker_id = getattr(response, "worker_id", None)
            if worker_id is not None:
                self._worker_counts[worker_id] += 1

    def finish(self):
        self.finished_at = time.time()

    def counts(self):
        with self._lock:
            return {
                "successful_requests": self._successes,
                "failed_requests": self._failures,
                "total_requests": self._successes + self._failures,
                "total_attempts": self._attempts,
            }

    def summary(self, workers=None):
        finished_at = self.finished_at or time.time()
        duration = max(finished_at - self.started_at, 0.000001)
        total = self._successes + self._failures
        latencies = sorted(self._latencies)

        if latencies:
            p95_index = max(0, int(len(latencies) * 0.95) - 1)
            avg_latency = statistics.mean(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            p95_latency = latencies[p95_index]
        else:
            avg_latency = 0
            max_latency = 0
            min_latency = 0
            p95_latency = 0

        worker_utilization = {}
        if workers:
            worker_utilization = {
                worker.id: round(worker.utilization_percent(), 2)
                for worker in workers
            }

        return {
            "total_requests": total,
            "successful_requests": self._successes,
            "failed_requests": self._failures,
            "total_attempts": self._attempts,
            "duration_seconds": round(duration, 4),
            "throughput_rps": round(total / duration, 4),
            "avg_latency_seconds": round(avg_latency, 4),
            "p95_latency_seconds": round(p95_latency, 4),
            "min_latency_seconds": round(min_latency, 4),
            "max_latency_seconds": round(max_latency, 4),
            "per_worker_requests": dict(self._worker_counts),
            "worker_utilization_percent": worker_utilization,
            "failure_errors": dict(self._failure_errors.most_common(5)),
        }


def print_summary(summary):
    print("\n[Metrics] Summary")
    for key, value in summary.items():
        print(f"[Metrics] {key}: {value}")
