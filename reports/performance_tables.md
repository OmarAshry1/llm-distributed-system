# Performance tables - distributed load-balancing simulation

**Setup:** single process; Chroma vector DB and LangChain RAG were initialized once before scenarios. Requests used the configured Ollama model through the RAG chain. `DISTRIBUTED_QUIET=1` suppresses per-request logs.

## Latency, throughput, failures

| Concurrent users | Strategy | Avg latency (s) | p95 (s) | Throughput (req/s) | Failed | Total req | Duration (s) |
|-------------------|----------|-----------------|---------|-------------------|--------|-----------|----------------|
| 100 | round_robin | 49.5669 | 92.3116 | 1.0317 | 0 | 100 | 96.9231 |
| 100 | least_connections | 41.5482 | 76.9698 | 1.2326 | 0 | 100 | 81.127 |
| 100 | load_aware | 39.1805 | 72.8845 | 1.3137 | 0 | 100 | 76.1196 |
| 500 | round_robin | 216.3775 | 420.6535 | 1.126 | 0 | 500 | 444.0303 |
| 500 | least_connections | 190.7937 | 359.3231 | 1.3198 | 0 | 500 | 378.8498 |
| 500 | load_aware | 178.2407 | 337.635 | 1.4056 | 0 | 500 | 355.7293 |
| 1000 | round_robin | 373.915 | 746.6843 | 1.2638 | 0 | 1000 | 791.2874 |
| 1000 | least_connections | 359.8508 | 685.0245 | 1.3844 | 0 | 1000 | 722.331 |
| 1000 | load_aware | 341.7796 | 645.6546 | 1.468 | 0 | 1000 | 681.2011 |

## Per-worker distribution and simulated GPU utilization

Request counts are sticky-session weighted (same client tends to reuse a worker). Utilization is `total_busy_time / (elapsed * capacity) * 100`, capped at 100%.

### users=100, strategy=round_robin

- **per_worker_requests:** `{0: 25, 3: 25, 1: 25, 2: 25}`
- **worker_utilization_percent:** `{0: 84.62, 1: 87.44, 2: 86.61, 3: 80.52}`

### users=100, strategy=least_connections

- **per_worker_requests:** `{2: 25, 3: 25, 1: 25, 0: 25}`
- **worker_utilization_percent:** `{0: 83.99, 1: 86.53, 2: 84.98, 3: 84.28}`

### users=100, strategy=load_aware

- **per_worker_requests:** `{3: 25, 0: 24, 2: 26, 1: 25}`
- **worker_utilization_percent:** `{0: 83.37, 1: 83.55, 2: 87.41, 3: 86.77}`

### users=500, strategy=round_robin

- **per_worker_requests:** `{0: 124, 1: 126, 3: 125, 2: 125}`
- **worker_utilization_percent:** `{0: 95.95, 1: 97.41, 2: 96.64, 3: 97.28}`

### users=500, strategy=least_connections

- **per_worker_requests:** `{3: 126, 0: 124, 1: 125, 2: 125}`
- **worker_utilization_percent:** `{0: 96.11, 1: 96.85, 2: 97.2, 3: 97.56}`

### users=500, strategy=load_aware

- **per_worker_requests:** `{1: 125, 2: 125, 0: 125, 3: 125}`
- **worker_utilization_percent:** `{0: 97.2, 1: 96.88, 2: 96.69, 3: 97.05}`

### users=1000, strategy=round_robin

- **per_worker_requests:** `{0: 250, 2: 250, 1: 250, 3: 250}`
- **worker_utilization_percent:** `{0: 98.25, 1: 98.44, 2: 98.23, 3: 98.38}`

### users=1000, strategy=least_connections

- **per_worker_requests:** `{3: 250, 1: 250, 0: 250, 2: 250}`
- **worker_utilization_percent:** `{0: 98.48, 1: 98.24, 2: 98.45, 3: 98.5}`

### users=1000, strategy=load_aware

- **per_worker_requests:** `{2: 250, 3: 250, 1: 250, 0: 250}`
- **worker_utilization_percent:** `{0: 98.49, 1: 98.49, 2: 98.29, 3: 98.58}`
