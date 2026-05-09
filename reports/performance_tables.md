# Performance tables — distributed load-balancing simulation

**Setup:** single process; RAG init was unavailable (missing LangChain/Chroma build); scenarios used `MOCK_LLM` only—same load balancer and metrics path as production, without retrieval. `MOCK_LLM=1` bypasses Ollama inference; `DISTRIBUTED_QUIET=1` suppresses per-request logs; `SIMULATED_LLM_DELAY=0`. For full LLM+RAG latency, install deps on Python 3.10/3.11, unset `MOCK_LLM`, and run Ollama.

## Latency, throughput, failures

| Concurrent users | Strategy | Avg latency (s) | p95 (s) | Throughput (req/s) | Failed | Total req | Duration (s) |
|-------------------|----------|-----------------|---------|-------------------|--------|-----------|----------------|
| 100 | round_robin | 0.0003 | 0.0 | 2646.0316 | 0 | 300 | 0.1134 |
| 100 | least_connections | 0.0 | 0.0 | 3445.7211 | 0 | 300 | 0.0871 |
| 100 | load_aware | 0.0 | 0.0 | 3563.3429 | 0 | 300 | 0.0842 |
| 500 | round_robin | 0.0 | 0.0 | 2885.0891 | 0 | 1500 | 0.5199 |
| 500 | least_connections | 0.0 | 0.0 | 3434.5627 | 0 | 1500 | 0.4367 |
| 500 | load_aware | 0.0 | 0.0 | 4183.0572 | 0 | 1500 | 0.3586 |
| 1000 | round_robin | 0.0 | 0.0 | 6398.2036 | 0 | 3000 | 0.4689 |
| 1000 | least_connections | 0.0 | 0.0 | 6358.9756 | 0 | 3000 | 0.4718 |
| 1000 | load_aware | 0.0 | 0.0 | 5211.1571 | 0 | 3000 | 0.5757 |

## Per-worker distribution and simulated GPU utilization

Request counts are sticky-session weighted (same client tends to reuse a worker). Utilization is `total_busy_time / (elapsed * capacity) * 100`, capped at 100%.

### users=100, strategy=round_robin

- **per_worker_requests:** `{0: 75, 1: 75, 2: 75, 3: 75}`
- **worker_utilization_percent:** `{0: 2.79, 1: 2.67, 2: 2.61, 3: 1.37}`

### users=100, strategy=least_connections

- **per_worker_requests:** `{1: 75, 2: 45, 0: 102, 3: 78}`
- **worker_utilization_percent:** `{0: 0.25, 1: 0.2, 2: 0.11, 3: 0.19}`

### users=100, strategy=load_aware

- **per_worker_requests:** `{0: 69, 1: 75, 2: 84, 3: 72}`
- **worker_utilization_percent:** `{0: 0.17, 1: 0.18, 2: 0.21, 3: 0.18}`

### users=500, strategy=round_robin

- **per_worker_requests:** `{0: 375, 1: 375, 2: 375, 3: 375}`
- **worker_utilization_percent:** `{0: 0.18, 1: 0.17, 2: 0.17, 3: 0.17}`

### users=500, strategy=least_connections

- **per_worker_requests:** `{2: 405, 0: 372, 1: 354, 3: 369}`
- **worker_utilization_percent:** `{0: 0.19, 1: 0.18, 2: 0.22, 3: 0.18}`

### users=500, strategy=load_aware

- **per_worker_requests:** `{0: 366, 1: 405, 2: 330, 3: 399}`
- **worker_utilization_percent:** `{0: 0.12, 1: 0.14, 2: 0.11, 3: 0.13}`

### users=1000, strategy=round_robin

- **per_worker_requests:** `{0: 750, 1: 750, 2: 750, 3: 750}`
- **worker_utilization_percent:** `{0: 0.17, 1: 0.17, 2: 0.18, 3: 0.18}`

### users=1000, strategy=least_connections

- **per_worker_requests:** `{0: 771, 2: 750, 1: 756, 3: 723}`
- **worker_utilization_percent:** `{0: 0.2, 1: 0.2, 2: 0.22, 3: 0.19}`

### users=1000, strategy=load_aware

- **per_worker_requests:** `{0: 765, 3: 768, 1: 627, 2: 840}`
- **worker_utilization_percent:** `{0: 0.16, 1: 0.13, 2: 0.18, 3: 0.16}`
