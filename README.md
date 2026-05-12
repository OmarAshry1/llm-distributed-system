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

Install [Ollama](https://ollama.com/) and pull a model, for example:

```powershell
ollama pull mistral
```

Add the real knowledge-base PDF at `data/sample.pdf`, or point `PDF_PATHS` to the correct file.

## Run

Start Ollama first:

```powershell
ollama serve
```

Then run the simulation:

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
- `WORKER_CAPACITIES` (optional comma-separated capacities, e.g. `4,8,8,16`)
- `MAX_RETRIES`
- `PDF_PATHS`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_KEEP_ALIVE`
- `OLLAMA_NUM_PREDICT`
- `OLLAMA_NUM_CTX`
- `OLLAMA_NUM_THREAD`
- `OLLAMA_TEMPERATURE`
- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`
- `RAG_RETRIEVER_K`
- `RAG_PERSIST_DIR`
- `RAG_FORCE_REBUILD`
- `LOAD_TEST_QUERIES` (`||`-separated query pool for simulated users)

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

- **`DISTRIBUTED_QUIET=1`** suppresses per-request LB/worker/client logs (also **`--quiet`** on `main.py`).

Example end-to-end RAG + Ollama run (four workers, eight simulated GPUs capacity each):

```powershell
py main.py --num-users 500 --requests-per-user 3 --strategy least_connections --quiet --metrics-json reports\run.json
```

Recommended real-LLM benchmark settings for an 8 GB VRAM machine:

```powershell
$env:OLLAMA_KEEP_ALIVE="-1m"
$env:OLLAMA_NUM_PREDICT="128"
$env:OLLAMA_NUM_CTX="2048"
$env:OLLAMA_TEMPERATURE="0"
$env:RAG_RETRIEVER_K="2"
$env:REQUESTS_PER_USER="1"
$env:DISTRIBUTED_QUIET="1"
```

Use `LOAD_TEST_QUERIES` to make simulated users ask questions that match your PDF:

```powershell
$env:LOAD_TEST_QUERIES="What failure model does the paper assume?||How does the protocol recover after coordinator failure?||What are the phases of the algorithm?"
py main.py --num-users 5 --requests-per-user 1 --strategy load_aware
```

Full scenario matrix (**100 / 500 / 1000 users**, three strategies), JSON per scenario, and **`reports/performance_tables.md`** (latency avg/p95, throughput, failures, per-worker counts, simulated GPU utilization):

```powershell
py scripts\benchmark.py
```

Optional: `BENCHMARK_USER_COUNTS=50,100` to shorten runs.

These runs require LangChain + Chroma dependencies, an available `data/sample.pdf`, and Ollama running with the configured `OLLAMA_MODEL`.
Startup checks Ollama before the load test begins; if the configured model is missing, run `ollama pull <model>` or update `OLLAMA_MODEL`.

Optional heterogeneous-worker scenario for evaluating adaptive routing under uneven capacity:

```powershell
$env:WORKER_CAPACITIES="4,8,8,16"
py scripts\benchmark.py
```

Focused fault-tolerance demo:

```powershell
py scripts\fault_tolerance_demo.py --num-users 20 --requests-per-user 1 --strategy load_aware --fail-worker 0 --fail-after 0.5 --metrics-json reports\fault_tolerance_demo.json
```

Docker GPU deployment scaffold is provided in `docker-compose.gpu.yml` and `docker/README.md`. It is intended as a path toward real multi-node GPU deployment; on a single 8 GB VRAM GPU, multiple Ollama containers may compete for memory.

## Notes

Installing **`chromadb`** may require Microsoft C++ Build Tools on Windows if no binary wheel exists for your Python version. Python **3.10** or **3.11** is recommended for the full RAG stack per dependency wheels.
