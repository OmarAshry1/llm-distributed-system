import random
import threading


# el strategy de btlef 3ala el workers bel dor w lazm teb2a thread-safe
class RoundRobin:
    def __init__(self):
        self.index = 0
        self._lock = threading.Lock()

    def get_worker(self, workers):
        with self._lock:
            worker = workers[self.index % len(workers)]
            self.index = (self.index + 1) % len(workers)
        return worker


# el strategy de btekhtar a2al worker 3aleh active requests
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


# el strategy de btbos 3ala el load w capacity 3ashan matzawedsh worker mesh fady
class LoadAware:
    def __init__(self, threshold=5):
        self.threshold = threshold

    def get_worker(self, workers):
        under_threshold = [
            w for w in workers
            if w.active_connections < self.threshold and w.active_connections < _capacity(w)
        ]

        if under_threshold:
            min_load = min(_load_ratio(w) for w in under_threshold)
            candidates = [
                w for w in under_threshold if _load_ratio(w) == min_load
            ]
            return random.choice(candidates)

        min_queue = min(_queue_length(w) for w in workers)
        queue_candidates = [
            w for w in workers if _queue_length(w) == min_queue
        ]
        min_load = min(_load_ratio(w) for w in queue_candidates)
        candidates = [
            w for w in queue_candidates if _load_ratio(w) == min_load
        ]

        return random.choice(candidates)
