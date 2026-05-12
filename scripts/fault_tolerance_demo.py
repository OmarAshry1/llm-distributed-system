#!/usr/bin/env python3
# el script da bytest failure worker w byekteb evidence lel report
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def non_negative_float(value):
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return number


def parse_args():
    parser = argparse.ArgumentParser(
        description="Demonstrate worker failure, reassignment, and retry behavior."
    )
    parser.add_argument("--num-users", type=positive_int, default=20)
    parser.add_argument("--requests-per-user", type=positive_int, default=1)
    parser.add_argument("--strategy", default=os.getenv("LB_STRATEGY", "load_aware"))
    parser.add_argument("--fail-worker", type=int, default=0)
    parser.add_argument("--fail-after", type=non_negative_float, default=0.5)
    parser.add_argument("--recover-after", type=non_negative_float, default=None)
    parser.add_argument("--metrics-json", default="reports/fault_tolerance_demo.json")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))

    args = parse_args()
    if args.quiet:
        os.environ["DISTRIBUTED_QUIET"] = "1"

    from client.load_generator import run_load_test
    from common.metrics import print_summary
    from lb.load_balancer import LoadBalancer
    from main import (
        DEFAULT_PDF_PATHS,
        build_strategy,
        build_workers,
        env_positive_int,
        resolve_existing_pdf_paths,
    )
    from master.scheduler import Scheduler
    from rag.rag_engine import initialize_rag

    pdf_paths, missing_paths = resolve_existing_pdf_paths(
        os.getenv("PDF_PATHS", DEFAULT_PDF_PATHS)
    )
    if missing_paths or not pdf_paths:
        print(f"[fault-demo] Missing PDF path(s): {missing_paths or 'none configured'}")
        return 1

    initialize_rag(pdf_paths=pdf_paths)

    num_workers = env_positive_int("NUM_WORKERS", 4)
    worker_capacity = env_positive_int("WORKER_CAPACITY", 8)
    max_retries = env_positive_int("MAX_RETRIES", 2)
    load_threshold = env_positive_int("LOAD_THRESHOLD", 5)

    workers = build_workers(num_workers, worker_capacity)
    if args.fail_worker < 0 or args.fail_worker >= len(workers):
        print(f"[fault-demo] --fail-worker must be between 0 and {len(workers) - 1}.")
        return 1

    strategy = build_strategy(args.strategy, load_threshold)
    load_balancer = LoadBalancer(workers, strategy, max_retries=max_retries)
    scheduler = Scheduler(load_balancer)

    events: list[dict] = []

    def fail_and_optionally_recover():
        time.sleep(args.fail_after)
        workers[args.fail_worker].simulate_failure()
        events.append({
            "time": round(time.time(), 4),
            "event": "worker_failed",
            "worker_id": args.fail_worker,
        })
        if args.recover_after is not None:
            time.sleep(args.recover_after)
            workers[args.fail_worker].recover()
            events.append({
                "time": round(time.time(), 4),
                "event": "worker_recovered",
                "worker_id": args.fail_worker,
            })

    failure_thread = threading.Thread(target=fail_and_optionally_recover, daemon=True)

    print(
        "[fault-demo] Running: "
        f"users={args.num_users}, requests_per_user={args.requests_per_user}, "
        f"strategy={args.strategy}, fail_worker={args.fail_worker}, "
        f"fail_after={args.fail_after}, recover_after={args.recover_after}"
    )
    initial_health = load_balancer.health_check()
    failure_thread.start()

    summary = run_load_test(
        scheduler,
        num_users=args.num_users,
        requests_per_user=args.requests_per_user,
        workers=workers,
    )
    failure_thread.join(timeout=0.1)

    final_health = load_balancer.health_check()
    print_summary(summary)
    print(f"[fault-demo] events: {events}")
    print(f"[fault-demo] final_health: {final_health}")

    payload = {
        "scenario": {
            "num_users": args.num_users,
            "requests_per_user": args.requests_per_user,
            "strategy": args.strategy,
            "failed_worker": args.fail_worker,
            "fail_after_seconds": args.fail_after,
            "recover_after_seconds": args.recover_after,
            "worker_capacities": [worker.capacity for worker in workers],
        },
        "events": events,
        "initial_health": initial_health,
        "final_health": final_health,
        "summary": summary,
    }
    out = ROOT / args.metrics_json
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[fault-demo] Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
