# Distributed LLM/RAG Load Balancing Project

Simulates a distributed system for concurrent LLM requests with:

- Client load generation
- Master scheduler
- Load balancer with Round Robin, Least Connections, and Load-Aware routing
- Sticky sessions
- Simulated GPU workers
- Fault-tolerant retry/reassignment
- RAG + local LLM via Ollama
- Metrics summary for latency, throughput, failures, retries, and worker utilization

## Setup

Recommended runtime: Python 3.10 or 3.11.

```powershell
py -m pip install -r requirements.txt
```

Create `.env`:

```env
PDF_PATHS=data/sample.pdf
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

Install [Ollama](https://ollama.com/) and pull a model (for example `ollama pull mistral`). Add the real knowledge-base PDF at `data/sample.pdf`, or point `PDF_PATHS` to the correct file.

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
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`
- `RAG_RETRIEVER_K`
- `RAG_PERSIST_DIR`
- `RAG_FORCE_REBUILD`
- `SIMULATED_LLM_DELAY`

## Tests

```powershell
py -m pytest tests lb -q
```

Coverage includes the load balancer (existing `lb/test_load_balancer.py`) plus **metrics collector**, **scheduler**, **load generator**, **GPU worker** (`tests/test_*.py`). RAG tests import LangChain when installed; they are skipped otherwise.

## Knowledge-base PDF

Generate `data/sample.pdf` (used by default `PDF_PATHS`):

```powershell
py scripts\create_sample_pdf.py
```

## Load testing, metrics export, and evaluation runs

- **`MOCK_LLM=1`** — returns a stub from `llm/inference.py` without calling Ollama/RAG retrieval (good for throughput experiments and machines without the full RAG stack).
- **`SIMULATED_LLM_DELAY`** — extra delay per request (seconds) to mimic slow inference.
- **`DISTRIBUTED_QUIET=1`** — suppresses per-request LB/worker/client logs (also **`--quiet`** on `main.py`).
- **`--skip-rag-init`** — skips PDF checks and vector DB build; use with **`MOCK_LLM=1`** if dependencies such as Chroma are unavailable.

Example end-to-end load-only run (four workers, eight simulated GPUs capacity each):

```powershell
$env:MOCK_LLM="1"
py main.py --num-users 500 --requests-per-user 3 --strategy least_connections --quiet --metrics-json reports\run.json
```

Full scenario matrix (**100 / 500 / 1000 users**, three strategies), JSON per scenario, and **`reports/performance_tables.md`** (latency avg/p95, throughput, failures, per-worker counts, simulated GPU utilization):

```powershell
$env:MOCK_LLM="1"
py scripts\benchmark.py
```

Optional: `BENCHMARK_USER_COUNTS=50,100` to shorten runs.

With LangChain + Chroma installed and Ollama running, omit **`MOCK_LLM`** for **full LLM + RAG** latency numbers.

**Sample console capture** (verbose scheduling path): see **`reports/demo_sample_run.txt`**.

## Notes

Installing **`chromadb`** may require Microsoft C++ Build Tools on Windows if no binary wheel exists for your Python version. Python **3.10** or **3.11** is recommended for the full RAG stack per dependency wheels.
