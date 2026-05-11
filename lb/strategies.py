# strategies.py

import random
import threading

# Round Robin Strategy, distributes requests evenly across workers in cyclic order to ensure fair distribution
# Thread-safe to support concurrent request handling without race conditions
class RoundRobin:
    def __init__(self):
        self.index = 0                   # pointer to next worker
        self._lock = threading.Lock()    # ensures thread safety

    def get_worker(self, workers):
        # select worker in circular manner
        with self._lock:
            worker = workers[self.index % len(workers)]
            self.index = (self.index + 1) % len(workers)
        return worker

# Least Connections: Selects the worker with the minimum number of active requests to balance load more effectively
# choose worker with lowest current load
class LeastConnections:
    def get_worker(self, workers):
        min_load = min(w.active_connections for w in workers)
        candidates = [w for w in workers if w.active_connections == min_load]
        return random.choice(candidates)


def _capacity(worker):
    return max(1, getattr(worker, "capacity", 1))


def _load_ratio(worker):
    return worker.active_connections / _capacity(worker)


def _queue_length(worker):
    if hasattr(worker, "queue_length"):
        return worker.queue_length()
    return max(0, worker.active_connections - _capacity(worker))


# Load-Aware: Prefers workers below a certain load threshold to prevent overload and falls back to least connections when all workers are busy to prevent overload
# Uses random tie-breaking for fairness when multiple workers have the same load
class LoadAware:
    def __init__(self, threshold=5):
        self.threshold = threshold        # max preferred load per worker

    def get_worker(self, workers):
        # filter workers under threshold and below their own capacity
        under_threshold = [
            w for w in workers
            if w.active_connections < self.threshold and w.active_connections < _capacity(w)
        ]

        # choose lowest load ratio among them if available
        if under_threshold:
            min_load = min(_load_ratio(w) for w in under_threshold)
            candidates = [
                w for w in under_threshold if _load_ratio(w) == min_load
            ]
            return random.choice(candidates)

        # when every worker is busy, prefer the shortest queue and lowest load ratio
        min_queue = min(_queue_length(w) for w in workers)
        queue_candidates = [
            w for w in workers if _queue_length(w) == min_queue
        ]
        min_load = min(_load_ratio(w) for w in queue_candidates)
        candidates = [
            w for w in queue_candidates if _load_ratio(w) == min_load
        ]

        return random.choice(candidates)  # fairness when equal load
