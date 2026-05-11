import time
import threading
from common.models import Response
from common.quiet import dprint


class Worker:
    def __init__(self, id, capacity=8):
        self.id = id
        self.is_alive = True   # used by load balancer health check
        self.active_connections = 0      # used by Least Connections strategy
        self.capacity = max(1, capacity)
        self._capacity_slots = threading.Semaphore(self.capacity)
        self.max_queue_length = 0
        self.total_busy_time = 0.0
        self.started_at = time.time()
        self._lock = threading.Lock()

    def process(self, request):
        start = time.time()
        busy_start = None

        if not self.is_alive:
            raise RuntimeError(f"Worker {self.id} is down")

        self._capacity_slots.acquire()
        try:
            busy_start = time.time()
            dprint(f"[Worker {self.id}] Processing request {request.id}")

            # Session persistence based on client identity to maintain context across requests
            session_id = f"client_{request.client_id}"

            from llm.inference import run_llm

            result = run_llm(
                request.query,
                session_id=session_id
            )

            if not self.is_alive:
                raise RuntimeError(f"Worker {self.id} failed while processing request {request.id}")
        finally:
            if busy_start is not None:
                with self._lock:
                    self.total_busy_time += time.time() - busy_start
            self._capacity_slots.release()

        latency = time.time() - start

        return Response(
            id=request.id,
            worker_id=self.id,
            result=result,
            latency=latency,
            success=True,
        )

    def increment_load(self):
        with self._lock:
            self.active_connections += 1
            self.max_queue_length = max(
                self.max_queue_length,
                max(0, self.active_connections - self.capacity)
            )

    def decrement_load(self):
        with self._lock:
            self.active_connections = max(0, self.active_connections - 1)

    def queue_length(self):
        with self._lock:
            return max(0, self.active_connections - self.capacity)

    def utilization_percent(self):
        elapsed = max(time.time() - self.started_at, 0.000001)
        with self._lock:
            return min(100.0, (self.total_busy_time / (elapsed * self.capacity)) * 100)

    # Fault tolerance
    def simulate_failure(self):
        self.is_alive = False
        print(f"[Worker {self.id}] Node failure simulated")

    def recover(self):
        self.is_alive = True
        print(f"[Worker {self.id}] Node recovered")
