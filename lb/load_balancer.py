import threading
import time

from common.models import Response
from common.quiet import dprint


class LoadBalancer:
    def __init__(self, workers, strategy, max_retries=2):
        self.workers = workers
        self.strategy = strategy
        self.max_retries = max_retries
        self.session_map = {}             # maps client_id to worker
        self.session_lock = threading.Lock()

    # Handles routing of incoming client requests
    def dispatch(self, request):
        client_id = request.client_id
        attempts = 0
        tried_worker_ids = set()
        start = time.time()

        while attempts <= self.max_retries:
            attempts += 1
            try:
                worker = self._get_worker_for_client(client_id, tried_worker_ids)
            except RuntimeError as error:
                return Response(
                    id=request.id,
                    worker_id=None,
                    result="",
                    latency=time.time() - start,
                    success=False,
                    error=str(error),
                    attempts=attempts,
                )

            tried_worker_ids.add(worker.id)
            worker.increment_load()

            try:
                dprint(f"[LB] Client {client_id}: Worker {worker.id} | Load={worker.active_connections}")
                response = worker.process(request)
                response.attempts = attempts
                return response
            except Exception as error:
                dprint(f"[LB] Worker {worker.id} failed request {request.id}: {error}")
                with self.session_lock:
                    if self.session_map.get(client_id) is worker:
                        del self.session_map[client_id]

                if attempts > self.max_retries:
                    return Response(
                        id=request.id,
                        worker_id=worker.id,
                        result="",
                        latency=time.time() - start,
                        success=False,
                        error=str(error),
                        attempts=attempts,
                    )

            finally:
                worker.decrement_load()

        return Response(
            id=request.id,
            worker_id=None,
            result="",
            latency=time.time() - start,
            success=False,
            error="Max retries exceeded",
            attempts=attempts,
        )

    def _get_worker_for_client(self, client_id, excluded_worker_ids=None):
        excluded_worker_ids = excluded_worker_ids or set()

        # Sticky Session + Fault Tolerance, ensures same client goes to same worker and reassigns if worker has failed
        with self.session_lock:
            worker = self.session_map.get(client_id)
            if (
                worker is not None
                and worker.is_alive
                and worker.id not in excluded_worker_ids
            ):
                return worker

            worker = self._select_worker(excluded_worker_ids)
            self.session_map[client_id] = worker
            return worker

    # Select worker using current strategy
    def _select_worker(self, excluded_worker_ids=None):
        excluded_worker_ids = excluded_worker_ids or set()
        alive_workers = [
            w for w in self.workers
            if w.is_alive and w.id not in excluded_worker_ids
        ]

        if not alive_workers:
            # system-wide failure condition
            raise RuntimeError("All workers are down!")

        return self.strategy.get_worker(alive_workers)

    def health_check(self):
        return {
            worker.id: {
                "alive": worker.is_alive,
                "active_connections": worker.active_connections,
                "queue_length": worker.queue_length() if hasattr(worker, "queue_length") else 0,
                "utilization_percent": round(worker.utilization_percent(), 2)
                if hasattr(worker, "utilization_percent")
                else 0,
            }
            for worker in self.workers
        }

    # Allows runtime switching of strategy
    def set_strategy(self, new_strategy):
        with self.session_lock:
            self.strategy = new_strategy

        dprint(f"[LB] Strategy updated to: {type(new_strategy).__name__}")
        
