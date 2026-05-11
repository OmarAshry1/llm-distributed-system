import os
import threading
import time
from common.models import Request
from common.metrics import MetricsCollector
from common.quiet import dprint

DEFAULT_QUERIES = [
    "What is a distributed system, and what are its main characteristics?",
    "How do processes communicate in a distributed system?",
    "What are the main challenges in distributed systems?",
    "How does fault tolerance work in distributed systems?",
    "What is the role of consensus in distributed systems?",
    "How do distributed systems handle coordination between nodes?",
    "What are common failure types in distributed systems?",
    "How do replication and consistency relate in distributed systems?",
    "What is the difference between synchronous and asynchronous distributed systems?",
    "How do distributed algorithms handle node or network failures?",
]


def _load_query_pool():
    raw = os.getenv("LOAD_TEST_QUERIES", "")
    queries = [item.strip() for item in raw.split("||") if item.strip()]
    return queries or DEFAULT_QUERIES


def _query_for(user_id, request_index, queries):
    index = (user_id + request_index) % len(queries)
    return queries[index]


def simulate_user(scheduler, user_id, requests_per_user=3, metrics=None, queries=None):
    queries = queries or _load_query_pool()
    for i in range(requests_per_user):
        req = Request(
            id=f"{user_id}_{i}",
            query=_query_for(user_id, i, queries),
            client_id=user_id
        )
        response = scheduler.handle_request(req)
        if metrics:
            metrics.record(response)
        dprint(f"[Client {user_id}] {response}")

def run_load_test(scheduler, num_users=100, requests_per_user=3, metrics=None, workers=None, queries=None):
    metrics = metrics or MetricsCollector()
    metrics.started_at = time.time()
    threads = []
    queries = queries or _load_query_pool()

    for i in range(num_users):
        t = threading.Thread(
            target=simulate_user,
            args=(scheduler, i, requests_per_user, metrics, queries)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    metrics.finish()
    return metrics.summary(workers=workers)
