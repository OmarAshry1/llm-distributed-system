from workers.gpu_worker import Worker
from lb.load_balancer import LoadBalancer
from master.scheduler import Scheduler
from client.load_generator import run_load_test
from rag.rag_engine import initialize_rag

import os
groq_api = os.getenv("GROQ_API_KEY")
def main():
    initialize_rag(
        pdf_paths=["data/sample.pdf"],
        groq_api_key=groq_api
    )
    workers = [Worker(i) for i in range(4)]
    lb = LoadBalancer(workers)
    scheduler = Scheduler(lb)

    run_load_test(lb, num_users=100)


if __name__ == "__main__":
    main()