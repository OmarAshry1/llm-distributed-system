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
        return min(workers, key=lambda w: w.active_connections)


# Load-Aware: Prefers workers below a certain load threshold to prevent overload and falls back to least connections when all workers are busy to prevent overload
# Uses random tie-breaking for fairness when multiple workers have the same load
class LoadAware:
    def __init__(self, threshold=5):
        self.threshold = threshold        # max preferred load per worker

    def get_worker(self, workers):
        # filter workers under threshold
        under_threshold = [
            w for w in workers if w.active_connections < self.threshold
        ]

        # choose least loaded among them if available 
        if under_threshold:
            return min(under_threshold, key=lambda w: w.active_connections)

        # to maintain fairness under equal load
        min_load = min(w.active_connections for w in workers)
        candidates = [
            w for w in workers if w.active_connections == min_load
        ]

        return random.choice(candidates)  # fairness when equal load