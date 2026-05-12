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

## Metrics comparison

Latest benchmark reports are stored in `reports/metrics_u*_*.json`. The current run used the real RAG + Ollama path with `REQUESTS_PER_USER=1` and completed without failed requests.

| Users | Strategy | Avg latency (s) | p95 latency (s) | Throughput (req/s) | Duration (s) | Failed |
|---:|---|---:|---:|---:|---:|---:|
| 100 | round_robin | 49.5669 | 92.3116 | 1.0317 | 96.9231 | 0 |
| 100 | least_connections | 41.5482 | 76.9698 | 1.2326 | 81.1270 | 0 |
| 100 | load_aware | 39.1805 | 72.8845 | 1.3137 | 76.1196 | 0 |
| 500 | round_robin | 216.3775 | 420.6535 | 1.1260 | 444.0303 | 0 |
| 500 | least_connections | 190.7937 | 359.3231 | 1.3198 | 378.8498 | 0 |
| 500 | load_aware | 178.2407 | 337.6350 | 1.4056 | 355.7293 | 0 |
| 1000 | round_robin | 373.9150 | 746.6843 | 1.2638 | 791.2874 | 0 |
| 1000 | least_connections | 359.8508 | 685.0245 | 1.3844 | 722.3310 | 0 |
| 1000 | load_aware | 341.7796 | 645.6546 | 1.4680 | 681.2011 | 0 |

Compared with Round Robin, Load-Aware improved throughput by about **27.3%** at 100 users, **24.8%** at 500 users, and **16.2%** at 1000 users. It also reduced p95 latency by about **21.0%**, **19.7%**, and **13.5%** for the same user counts.

Least Connections also improved over Round Robin because it reacts to active load, while Round Robin only balances request count. Load-Aware performed best because it considers current load and worker capacity, which matters when local Ollama/RAG inference becomes the bottleneck.

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
