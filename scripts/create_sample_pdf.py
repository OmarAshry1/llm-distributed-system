#!/usr/bin/env python3
"""Create data/sample.pdf with extractable text for RAG ingestion."""
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / "sample.pdf"

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    lines = [
        "Distributed LLM / RAG Load Balancing — sample knowledge base.",
        "",
        "This document describes a simulated system with clients, a scheduler, a load balancer,",
        "and multiple GPU workers. Routing strategies include round robin (fair rotation),",
        "least connections (prefer the worker with fewest active sessions), and load-aware",
        "routing (prefer workers under a configurable connection threshold).",
        "",
        "Sticky sessions bind each client_id to a worker for conversation context until that",
        "worker fails; failed requests retry on alternate workers up to max_retries.",
        "",
        "Metrics collected include average and p95 latency, throughput in requests per second,",
        "failed requests, per-worker request counts, and simulated GPU utilization derived from",
        "busy time versus elapsed wall time per worker capacity.",
    ]
    y = 720
    for line in lines:
        c.drawString(72, y, line[:120])
        y -= 16
    c.save()

    out.write_bytes(buf.getvalue())
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
