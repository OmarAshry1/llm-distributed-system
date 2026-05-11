# Local LLM Setup Guide with Ollama

## Overview
This project uses a **local LLM via Ollama** for RAG. Inference runs on your machine (no cloud LLM API key required).

## Prerequisites
- **RAM**: 8GB minimum, 16GB+ recommended
- **Disk**: 10-20GB free (model size)
- **CPU**: Any modern multi-core processor
- **GPU**: Optional (speeds up inference 5-10x)

## Step-by-Step Setup

### 1. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
# Download from https://ollama.ai/download
# Or use homebrew
brew install ollama
```

**Windows:**
Download from https://ollama.ai/download

### 2. Start Ollama Server

Open a terminal and run:
```bash
ollama serve
```

This starts Ollama on `http://localhost:11434` (keep this running in background)

### 3. Pull a Local Model

Open **another terminal** and pull a model. Recommended options for laptops:

**Option A: Mistral 7B (Best balance, ~4.1GB)**
```bash
ollama pull mistral
```

**Option B: Neural-Chat 7B (Optimized for chat, ~4.1GB)**
```bash
ollama pull neural-chat
```

**Option C: Zephyr 7B (Better quality, ~4.2GB)**
```bash
ollama pull zephyr
```

**Option D: Llama 2 7B (Very good quality, ~3.8GB)**
```bash
ollama pull llama2
```

### 4. Install Python Package

```bash
pip install langchain-ollama
```

### 5. Run Your Application

Run the app (Ollama must be running):

```bash
python main.py
```

The default model name is `mistral` unless you set `OLLAMA_MODEL`. To use a different model:

```bash
export OLLAMA_MODEL=neural-chat
export OLLAMA_BASE_URL=http://localhost:11434
python main.py
```

## Performance Expectations

### Latency Comparison
| Model | CPU Speed | GPU Speed | Tokens/sec |
|-------|-----------|-----------|-----------|
| Mistral 7B | 3-5 tok/s | 20-50 tok/s | ~100-150 |
| Neural-Chat 7B | 2-4 tok/s | 15-40 tok/s | ~50-100 |

**Note**: Local models are 4-10x slower but unlimited throughput.

## Environment Variables

You can customize via environment variables:

```bash
# Model to use
export OLLAMA_MODEL=neural-chat

# Ollama server URL
export OLLAMA_BASE_URL=http://localhost:11434

# RAG settings
export RAG_CHUNK_SIZE=1000
export RAG_CHUNK_OVERLAP=200
export RAG_RETRIEVER_K=4

# Ollama generation/performance tuning
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_NUM_PREDICT=128
export OLLAMA_NUM_CTX=2048
export OLLAMA_TEMPERATURE=0
```

For 100/500/1000-user real-LLM evaluation on an 8 GB VRAM machine, use short responses and a small retrieval context:

```bash
export OLLAMA_MODEL=gemma:2b
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_NUM_PREDICT=128
export OLLAMA_NUM_CTX=2048
export OLLAMA_TEMPERATURE=0
export RAG_RETRIEVER_K=2
export REQUESTS_PER_USER=1
export DISTRIBUTED_QUIET=1
export BENCHMARK_USER_COUNTS=100,500,1000
python scripts/benchmark.py
```

Round robin can be best in a homogeneous single-GPU setup because every simulated worker ultimately shares the same Ollama backend. To evaluate adaptive strategies under uneven capacity, run an additional scenario:

```bash
export WORKER_CAPACITIES=4,8,8,16
python scripts/benchmark.py
```

## Troubleshooting

### "Connection refused" error
- Make sure Ollama is running: `ollama serve` in another terminal
- Check URL: default is `http://localhost:11434`

### Model downloads too slow
- Models are large (4-7GB)
- You need good internet connection
- Can take 10-30 minutes depending on speed

### Out of memory error
- Stop Ollama: `pkill ollama`
- Use smaller model or increase RAM
- Mistral 7B is most memory-efficient

### Laptop gets too hot/slow
- This is normal for CPU inference
- Consider:
  - Using GPU if available (NVIDIA/AMD)
  - Reducing concurrent requests
  - Using smaller batches

## GPU Support

To enable GPU acceleration:

**NVIDIA (CUDA):**
```bash
# Download CUDA from nvidia.com
# Then reinstall ollama (will auto-detect CUDA)
ollama serve
```

**AMD (ROCm):**
```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export GPU_VRAM=8  # Your GPU VRAM in GB
ollama serve
```

**macOS (Metal):**
Automatically enabled on M1/M2/M3 chips

## Docker GPU Scaffold

The repository includes `docker-compose.gpu.yml` as a deployment scaffold. On Linux with NVIDIA Container Toolkit:

```bash
docker compose -f docker-compose.gpu.yml up ollama-gpu0
docker compose -f docker-compose.gpu.yml exec ollama-gpu0 ollama pull gemma:2b
docker compose -f docker-compose.gpu.yml run --rm app
```

With only one 8 GB VRAM GPU, this should be documented as a single-GPU deployment path. A true GPU cluster would run separate Ollama endpoints on separate GPUs or machines and route workers to those endpoints.

## Cost

- **Local LLM (Ollama)**: no per-token API cost (electricity only for your hardware).

## Recommended setup

For the distributed load-balancing simulation with multiple workers:

- Use Ollama with a model that fits your RAM (for example `mistral`).
- For heavier load, run Ollama with GPU acceleration or spread inference across machines.

## Next Steps

1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Start server: `ollama serve`
3. Pull model: `ollama pull mistral`
4. Run app: `python main.py`

That's it! The RAG stack talks to Ollama at `OLLAMA_BASE_URL` using `OLLAMA_MODEL`.
