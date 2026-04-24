import time
from llm.inference import run_llm


class Worker:
    def __init__(self, id):
        self.id = id

    def process(self, request):
        start = time.time()

        print(f"[Worker {self.id}] Processing request {request.id}")

        #Use client-based session badal worker based
        session_id = f"client_{request.client_id}"

        result = run_llm(
            request.query,
            session_id=session_id
        )

        latency = time.time() - start

        return {
            "id": request.id,
            "worker_id": self.id,
            "result": result,
            "latency": latency
        }