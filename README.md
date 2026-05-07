# Distributed LLM/RAG Load Balancing Project

Simulates a distributed system for concurrent LLM requests with:

- Client load generation
- Master scheduler
- Load balancer with Round Robin, Least Connections, and Load-Aware routing
- Sticky sessions
- Simulated GPU workers
- Fault-tolerant retry/reassignment
- RAG + Groq LLM integration
- Metrics summary for latency, throughput, failures, retries, and worker utilization

## Setup

Recommended runtime: Python 3.10 or 3.11.

```powershell
py -m pip install -r requirements.txt
```

Create `.env`:

```env
GROQ_API_KEY=your_key_here
PDF_PATHS=data/sample.pdf
```

Add the real knowledge-base PDF at `data/sample.pdf`, or point `PDF_PATHS` to the correct file.

## Run

```powershell
py main.py
```

Useful options:

```powershell
py main.py --num-users 1000 --requests-per-user 3 --num-workers 4 --strategy load_aware
```

Strategies:

- `round_robin`
- `least_connections`
- `load_aware`

Environment/config options:

- `NUM_USERS`
- `REQUESTS_PER_USER`
- `NUM_WORKERS`
- `LB_STRATEGY`
- `WORKER_CAPACITY`
- `MAX_RETRIES`
- `PDF_PATHS`
- `GROQ_MODEL`
- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`
- `RAG_RETRIEVER_K`
- `RAG_PERSIST_DIR`
- `RAG_FORCE_REBUILD`
- `SIMULATED_LLM_DELAY`

## Tests

```powershell
py -m pytest lb\test_load_balancer.py -q
```

The current tests cover load-balancing strategies, sticky sessions, failed worker reassignment, in-flight retry, and all-workers-down behavior.

## Notes

On this machine, full dependency installation with Python 3.14 fails while building `chroma-hnswlib` because Microsoft C++ Build Tools are missing. Use Python 3.10/3.11 or install the required C++ build tools for the RAG dependency stack.
