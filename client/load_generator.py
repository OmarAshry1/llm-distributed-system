import threading
import time
from common.models import Request
from common.metrics import MetricsCollector
from common.quiet import dprint

def simulate_user(scheduler, user_id, requests_per_user=3, metrics=None):
    for i in range(requests_per_user):
        req = Request(
            id=f"{user_id}_{i}",
            query=f"Question {i} from user {user_id}",
            client_id=user_id
        )
        response = scheduler.handle_request(req)
        if metrics:
            metrics.record(response)
        dprint(f"[Client {user_id}] {response}")

def run_load_test(scheduler, num_users=100, requests_per_user=3, metrics=None, workers=None):
    metrics = metrics or MetricsCollector()
    metrics.started_at = time.time()
    threads = []

    for i in range(num_users):
        t = threading.Thread(
            target=simulate_user,
            args=(scheduler, i, requests_per_user, metrics)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    metrics.finish()
    return metrics.summary(workers=workers)
