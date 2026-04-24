import threading
from common.models import Request

def simulate_user(scheduler, user_id):
    for i in range(3):  #simulate 3 convos
        req = Request(
            id=f"{user_id}_{i}",
            query=f"Question {i} from user {user_id}",
            client_id=user_id
        )
        response = scheduler.route_request(req)
        print(f"[Client {user_id}] {response}")

def run_load_test(scheduler, num_users=100):
    threads = []

    for i in range(num_users):
        t = threading.Thread(target=simulate_user, args=(scheduler, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()