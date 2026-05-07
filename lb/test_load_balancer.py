from load_balancer import LoadBalancer
from strategies import RoundRobin
import time
import random
import threading

# Dummy Classes
class Request:
    def __init__(self, client_id):
        self.client_id = client_id


class Worker:
    def __init__(self, id):
        self.id = id
        self.is_alive = True
        self.active_connections = 0

    def increment_load(self):
        self.active_connections += 1

    def decrement_load(self):
        self.active_connections -= 1

    def process(self, request):
        time.sleep(random.uniform(0.1, 0.3))
        return f"Worker {self.id} handled {request.client_id}"

# BASIC TEST
print("\n BASIC FUNCTIONAL TEST ")

workers = [Worker(i) for i in range(3)]
lb = LoadBalancer(workers, RoundRobin())

for i in range(6):
    print(lb.dispatch(Request(i)))

# STICKY SESSION TEST
print("\n STICKY SESSION TEST")

workers = [Worker(i) for i in range(3)]
lb = LoadBalancer(workers, RoundRobin())

print(lb.dispatch(Request(10)))
print(lb.dispatch(Request(10)))

# FAULT TOLERANCE TEST
print("\n FAULT TOLERANCE TEST")

workers = [Worker(i) for i in range(3)]
lb = LoadBalancer(workers, RoundRobin())

workers[0].is_alive = False
print("Worker 0 is DOWN")

for i in range(5):
    print(lb.dispatch(Request(i)))


# LOAD TEST
print("\n  LOAD TEST ")

workers = [Worker(i) for i in range(3)]
lb = LoadBalancer(workers, RoundRobin())

results = []

def task(i):
    start = time.time()
    lb.dispatch(Request(i))
    results.append(time.time() - start)

threads = []

for i in range(100):
    t = threading.Thread(target=task, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("\n RESULTS ")
print("Total Requests:", 100)
print("Avg Latency:", sum(results)/len(results))
print("Max Latency:", max(results))
print("Min Latency:", min(results))