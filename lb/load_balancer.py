import threading


class LoadBalancer:
    def __init__(self, workers, strategy):
        self.workers = workers
        self.strategy = strategy
        self.session_map = {}             # maps client_id to worker
        self.session_lock = threading.Lock()

    # Handles routing of incoming client requests
    def dispatch(self, request):
        client_id = request.client_id

        # Sticky Session + Fault Tolerance, ensures same client goes to same worker and reassigns if worker has failed
        with self.session_lock:
            if client_id in self.session_map:
                worker = self.session_map[client_id]

                # check if worker is still alive
                if not worker.is_alive:
                    worker = self._select_worker()
                    self.session_map[client_id] = worker
            else:
                # first-time client: assign worker
                worker = self._select_worker()
                self.session_map[client_id] = worker

        #  Load Tracking, increment load before processing request
        worker.increment_load()

        try:
            print(f"[LB] Client {client_id}: Worker {worker.id} | Load={worker.active_connections}")
            return worker.process(request)

        finally:
            # Ensure load is always decremented even on failure
            worker.decrement_load()

    # Select worker using current strategy
    def _select_worker(self):
        alive_workers = [w for w in self.workers if w.is_alive]

        if not alive_workers:
            # system-wide failure condition
            raise RuntimeError("All workers are down!")

        return self.strategy.get_worker(alive_workers)

    # Allows runtime switching of strategy
    def set_strategy(self, new_strategy):
        with self.session_lock:
            self.strategy = new_strategy

        print(f"[LB] Strategy updated to: {type(new_strategy).__name__}")
        