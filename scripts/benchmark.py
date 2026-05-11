#!/usr/bin/env python3
"""
Run end-to-end scenarios (100 / 500 / 1000 users x three strategies) in one process
so RAG initializes once and every request uses the configured Ollama-backed RAG chain.

Writes JSON per scenario and reports/performance_tables.md.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ensure_sample_pdf() -> Path:
    pdf = ROOT / "data" / "sample.pdf"
    if pdf.exists():
        return pdf
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "create_sample_pdf.py")])
    return pdf


def _write_markdown(rows: list[tuple[int, str, dict]], path: Path) -> None:
    lines = [
        "# Performance tables - distributed load-balancing simulation",
        "",
        "**Setup:** single process; "
        "Chroma vector DB and LangChain RAG were initialized once before scenarios. "
        "Requests used the configured Ollama model through the RAG chain. "
        "`DISTRIBUTED_QUIET=1` suppresses per-request logs.",
        "",
        "## Latency, throughput, failures",
        "",
        "| Concurrent users | Strategy | Avg latency (s) | p95 (s) | Throughput (req/s) | Failed | Total req | Duration (s) |",
        "|-------------------|----------|-----------------|---------|-------------------|--------|-----------|----------------|",
    ]
    for n, strat, s in rows:
        lines.append(
            f"| {n} | {strat} | {s['avg_latency_seconds']} | {s['p95_latency_seconds']} | "
            f"{s['throughput_rps']} | {s['failed_requests']} | {s['total_requests']} | {s['duration_seconds']} |"
        )

    lines.extend(
        [
            "",
            "## Per-worker distribution and simulated GPU utilization",
            "",
            "Request counts are sticky-session weighted (same client tends to reuse a worker). "
            "Utilization is `total_busy_time / (elapsed * capacity) * 100`, capped at 100%.",
            "",
        ]
    )
    for n, strat, s in rows:
        lines.append(f"### users={n}, strategy={strat}")
        lines.append("")
        lines.append(f"- **per_worker_requests:** `{s.get('per_worker_requests')}`")
        lines.append(f"- **worker_utilization_percent:** `{s.get('worker_utilization_percent')}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))

    os.environ.setdefault("DISTRIBUTED_QUIET", "1")

    _ensure_sample_pdf()

    from client.load_generator import run_load_test
    from lb.load_balancer import LoadBalancer
    from main import build_strategy
    from master.scheduler import Scheduler
    from workers.gpu_worker import Worker

    try:
        from rag.rag_engine import initialize_rag

        initialize_rag(pdf_paths=[str(ROOT / "data" / "sample.pdf")])
    except Exception as exc:
        print(
            f"[benchmark] RAG initialization failed: {exc!s}\n"
            "[benchmark] Start Ollama, pull the configured OLLAMA_MODEL, and install requirements before running this benchmark."
        )
        return 1

    reports = ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    num_workers = int(os.environ.get("NUM_WORKERS", "4"))
    worker_capacity = int(os.environ.get("WORKER_CAPACITY", "8"))
    max_retries = int(os.environ.get("MAX_RETRIES", "2"))
    load_threshold = int(os.environ.get("LOAD_THRESHOLD", "5"))
    requests_per_user = int(os.environ.get("REQUESTS_PER_USER", "3"))

    raw = os.environ.get("BENCHMARK_USER_COUNTS", "100,500,1000")
    user_counts = [int(x.strip()) for x in raw.split(",") if x.strip()]
    strategies = ["round_robin", "least_connections", "load_aware"]
    rows: list[tuple[int, str, dict]] = []

    for num_users in user_counts:
        for strategy_name in strategies:
            print(f"Scenario: users={num_users} strategy={strategy_name}", flush=True)
            workers = [Worker(i, capacity=worker_capacity) for i in range(num_workers)]
            strategy = build_strategy(strategy_name, load_threshold)
            lb = LoadBalancer(workers, strategy, max_retries=max_retries)
            scheduler = Scheduler(lb)
            summary = run_load_test(
                scheduler,
                num_users=num_users,
                requests_per_user=requests_per_user,
                workers=workers,
            )
            json_path = reports / f"metrics_u{num_users}_{strategy_name}.json"
            json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            rows.append((num_users, strategy_name, summary))

    md_path = reports / "performance_tables.md"
    _write_markdown(rows, md_path)
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
