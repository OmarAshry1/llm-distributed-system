from workers.gpu_worker import Worker
from lb.load_balancer import LoadBalancer
from master.scheduler import Scheduler
from client.load_generator import run_load_test

def main():
    workers = [Worker(i) for i in range(4)]
    lb = LoadBalancer(workers)
    scheduler = Scheduler(lb)

    run_load_test(lb, num_users=100)


if __name__ == "__main__":
    main()