import time
import threading
from llm.inference import run_llm


class Worker:
    def __init__(self, id):
        self.id = id
        self.is_alive = True   # used by load balancer health check
        self.active_connections = 0      # used by Least Connections strategy
        self._lock = threading.Lock()

    def process(self, request):
        start = time.time()

        print(f"[Worker {self.id}] Processing request {request.id}")

        # Session persistence based on client identity to maintain context across requests
        session_id = f"client_{request.client_id}"

        result = run_llm(
            request.query,
            session_id = session_id
        )

        latency = time.time() - start

        return {
            "id": request.id,
            "worker_id": self.id,
            "result": result,
            "latency": latency
        }

    def increment_load(self):
        with self._lock:
            self.active_connections += 1

    def decrement_load(self):
        with self._lock:
            self.active_connections -= 1

    # Fault tolerance
    def simulate_failure(self):
        self.is_alive = False
        print(f"[Worker {self.id}] Node failure simulated")

    def recover(self):
        self.is_alive = True
        print(f"[Worker {self.id}] Node recovered")