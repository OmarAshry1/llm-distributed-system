import argparse
import json
import os
from pathlib import Path

from client.load_generator import run_load_test
from common.metrics import print_summary
from lb.load_balancer import LoadBalancer
from lb.strategies import LeastConnections, LoadAware, RoundRobin
from master.scheduler import Scheduler

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PDF_PATHS = "data/sample.pdf"
STRATEGY_CHOICES = ["round_robin", "least_connections", "load_aware"]


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def env_positive_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return positive_int(value)
    except (ValueError, argparse.ArgumentTypeError):
        print(f"[Config] Invalid {name}={value!r}; using default {default}.")
        return default


def env_strategy(default):
    value = os.getenv("LB_STRATEGY", default)
    if value not in STRATEGY_CHOICES:
        print(f"[Config] Invalid LB_STRATEGY={value!r}; using default {default}.")
        return default
    return value


def build_strategy(name, threshold):
    strategies = {
        "round_robin": RoundRobin,
        "least_connections": LeastConnections,
        "load_aware": lambda: LoadAware(threshold=threshold),
    }
    return strategies[name]()


def parse_pdf_paths(raw_paths):
    return [
        path.strip()
        for path in raw_paths.split(",")
        if path.strip()
    ]


def parse_worker_capacities(raw_capacities):
    if not raw_capacities:
        return []

    capacities = []
    for raw in raw_capacities.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            capacities.append(positive_int(raw))
        except (ValueError, argparse.ArgumentTypeError):
            print(f"[Config] Ignoring invalid worker capacity {raw!r}.")
    return capacities


def build_workers(num_workers, default_capacity):
    from workers.gpu_worker import Worker

    configured = parse_worker_capacities(os.getenv("WORKER_CAPACITIES", ""))
    if configured:
        print(f"[Config] Using heterogeneous worker capacities: {configured}")
        return [Worker(i, capacity=capacity) for i, capacity in enumerate(configured)]

    return [Worker(i, capacity=default_capacity) for i in range(num_workers)]


def resolve_existing_pdf_paths(raw_paths):
    existing_paths = []
    missing_paths = []

    for raw_path in parse_pdf_paths(raw_paths):
        path = Path(raw_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        if path.exists() and path.is_file():
            existing_paths.append(str(path))
        else:
            missing_paths.append(str(path))

    return existing_paths, missing_paths


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the distributed LLM/RAG load-balancing simulation."
    )
    parser.add_argument(
        "--num-users",
        type=positive_int,
        default=env_positive_int("NUM_USERS", 100),
        help="Number of concurrent simulated users.",
    )
    parser.add_argument(
        "--requests-per-user",
        type=positive_int,
        default=env_positive_int("REQUESTS_PER_USER", 3),
        help="Number of requests each simulated user sends.",
    )
    parser.add_argument(
        "--num-workers",
        type=positive_int,
        default=env_positive_int("NUM_WORKERS", 4),
        help="Number of simulated GPU workers.",
    )
    parser.add_argument(
        "--strategy",
        choices=STRATEGY_CHOICES,
        default=env_strategy("round_robin"),
        help="Load-balancing strategy.",
    )
    parser.add_argument(
        "--load-threshold",
        type=positive_int,
        default=env_positive_int("LOAD_THRESHOLD", 5),
        help="Preferred max active connections for load-aware routing.",
    )
    parser.add_argument(
        "--worker-capacity",
        type=positive_int,
        default=env_positive_int("WORKER_CAPACITY", 8),
        help="Simulated concurrent capacity per GPU worker.",
    )
    parser.add_argument(
        "--max-retries",
        type=positive_int,
        default=env_positive_int("MAX_RETRIES", 2),
        help="Retries per request after worker failure.",
    )
    parser.add_argument(
        "--pdf-paths",
        default=os.getenv("PDF_PATHS", DEFAULT_PDF_PATHS),
        help="Comma-separated PDF paths for RAG ingestion.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-request log lines (LB, workers, clients, scheduler).",
    )
    parser.add_argument(
        "--metrics-json",
        default=None,
        metavar="PATH",
        help="Write the metrics summary dict to this JSON file after the run.",
    )
    return parser.parse_args()


def main():
    if load_dotenv:
        load_dotenv(BASE_DIR / ".env")

    args = parse_args()
    if args.quiet:
        os.environ["DISTRIBUTED_QUIET"] = "1"

    pdf_paths, missing_paths = resolve_existing_pdf_paths(args.pdf_paths)
    if not pdf_paths and not missing_paths:
        print("[Config] No PDF files configured. Set PDF_PATHS or pass --pdf-paths.")
        return 1

    if missing_paths:
        print("[Config] Missing PDF file(s):")
        for path in missing_paths:
            print(f"  - {path}")
        print("[Config] Set PDF_PATHS or pass --pdf-paths with existing PDF files.")
        return 1

    try:
        import workers.gpu_worker
    except ModuleNotFoundError as error:
        print(f"[Config] Missing Python dependency: {error.name}")
        print("[Config] Install requirements with: py -m pip install -r requirements.txt")
        return 1

    try:
        from rag.rag_engine import initialize_rag
    except ModuleNotFoundError as error:
        print(f"[Config] Missing Python dependency: {error.name}")
        print("[Config] Install requirements with: py -m pip install -r requirements.txt")
        return 1
    try:
        initialize_rag(pdf_paths=pdf_paths)
    except Exception as error:
        print(f"[RAG] Failed to initialize: {error}")
        return 1

    workers = build_workers(args.num_workers, args.worker_capacity)
    strategy = build_strategy(args.strategy, args.load_threshold)
    load_balancer = LoadBalancer(workers, strategy, max_retries=args.max_retries)
    scheduler = Scheduler(load_balancer)

    print(
        "[Config] Running load test: "
        f"users={args.num_users}, "
        f"requests_per_user={args.requests_per_user}, "
        f"workers={len(workers)}, "
        f"worker_capacities={[worker.capacity for worker in workers]}, "
        f"strategy={args.strategy}, "
        f"max_retries={args.max_retries}"
    )

    summary = run_load_test(
        scheduler,
        num_users=args.num_users,
        requests_per_user=args.requests_per_user,
        workers=workers,
    )
    print_summary(summary)
    print(f"[Health] {load_balancer.health_check()}")
    if args.metrics_json:
        out = Path(args.metrics_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"[Config] Wrote metrics to {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
