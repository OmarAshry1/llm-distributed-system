import threading
from common.models import Request

def simulate_user(scheduler, user_id):
    request = Request(user_id, f"Question {user_id}")
    response = scheduler.route_request(request)
    print(f"[Client] Got response: {response['id']} | Latency: {response['latency']:.3f}s")


def run_load_test(scheduler, num_users=100):
    threads = []

    for i in range(num_users):
        t = threading.Thread(target=simulate_user, args=(scheduler, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()