# Local LLM Setup Guide with Ollama

## Problem
You hit the Groq API rate limit (6000 TPM). Using a local LLM provides unlimited inference at the cost of speed.

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

Your code is already updated! It now:
- Uses local Ollama by default
- Falls back to Groq if you prefer

**Option A: Use Local Model (Default)**
```bash
python main.py
```

The system will use Mistral by default. To use a different model:
```bash
export OLLAMA_MODEL=neural-chat
export OLLAMA_BASE_URL=http://localhost:11434
python main.py
```

**Option B: Switch to Groq Again**
Modify `main.py` to pass `use_local_llm=False` to `initialize_rag()`

## Performance Expectations

### Latency Comparison
| Model | CPU Speed | GPU Speed | Tokens/sec |
|-------|-----------|-----------|-----------|
| Mistral 7B | 3-5 tok/s | 20-50 tok/s | ~100-150 |
| Neural-Chat 7B | 2-4 tok/s | 15-40 tok/s | ~50-100 |
| Groq (llama-3.1-8b) | N/A (remote) | N/A | **600+ tok/s** |

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
  - Switching back to Groq for production

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

## Switching Back to Groq

If you want to use Groq again:

1. Export API key:
```bash
export GROQ_API_KEY=your_key_here
```

2. Modify initialization (in your caller code):
```python
initialize_rag(
    pdf_paths=pdf_files,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    use_local_llm=False  # Switch to Groq
)
```

## Cost Analysis

- **Local LLM**: $0 (electricity only, ~$0.10-0.50/day for laptop CPU)
- **Groq (on_demand)**: ~$0.50-2.00 per 1M tokens (varies by model)

## Recommended Setup for Your Use Case

For your distributed system with 4 workers and 100+ concurrent clients:

**Development/Testing:**
- Use local Ollama (mistral)
- 1-2 concurrent requests per worker
- Latency won't matter much

**Production:**
- Keep Groq (better latency and throughput)
- Or use Ollama cluster with multiple servers
- Or use GPU-accelerated Ollama

## Next Steps

1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Start server: `ollama serve`
3. Pull model: `ollama pull mistral`
4. Run app: `python main.py`

That's it! Your RAG system will now use local Ollama instead of Groq.
