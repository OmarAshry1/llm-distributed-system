# Performance tables - distributed load-balancing simulation

**Setup:** single process; Chroma vector DB and LangChain RAG were initialized once before scenarios. Requests used the configured Ollama model through the RAG chain. `DISTRIBUTED_QUIET=1` suppresses per-request logs.

## Latency, throughput, failures

| Concurrent users | Strategy | Avg latency (s) | p95 (s) | Throughput (req/s) | Failed | Total req | Duration (s) |
|-------------------|----------|-----------------|---------|-------------------|--------|-----------|----------------|
| 100 | round_robin | 45.4829 | 84.5147 | 1.1221 | 0 | 100 | 89.1191 |
| 100 | least_connections | 36.7291 | 69.7177 | 1.3699 | 0 | 100 | 73.0007 |
| 100 | load_aware | 34.0901 | 63.8794 | 1.4732 | 0 | 100 | 67.8786 |

## Per-worker distribution and simulated GPU utilization

Request counts are sticky-session weighted (same client tends to reuse a worker). Utilization is `total_busy_time / (elapsed * capacity) * 100`, capped at 100%.

### users=100, strategy=round_robin

- **per_worker_requests:** `{3: 25, 2: 25, 1: 25, 0: 25}`
- **worker_utilization_percent:** `{0: 99.87, 1: 84.15, 2: 57.22, 3: 58.04}`

### users=100, strategy=least_connections

- **per_worker_requests:** `{2: 25, 3: 25, 0: 25, 1: 25}`
- **worker_utilization_percent:** `{0: 99.56, 1: 85.6, 2: 59.27, 3: 56.36}`

### users=100, strategy=load_aware

- **per_worker_requests:** `{0: 21, 3: 28, 2: 28, 1: 23}`
- **worker_utilization_percent:** `{0: 99.53, 1: 87.39, 2: 65.83, 3: 66.67}`
