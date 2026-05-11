# Docker GPU Deployment Scaffold

This project normally runs as a single-process distributed-system simulation. The
Docker files provide a concrete path toward a real deployment where workers can
target separate Ollama endpoints.

## Single-GPU Smoke Run

Install NVIDIA Container Toolkit, then start Ollama:

```bash
docker compose -f docker-compose.gpu.yml up ollama-gpu0
```

In another terminal, pull the model inside the Ollama container:

```bash
docker compose -f docker-compose.gpu.yml exec ollama-gpu0 ollama pull gemma:2b
```

Run the app container:

```bash
docker compose -f docker-compose.gpu.yml run --rm app
```

## Multi-GPU / Multi-Machine Extension

For a true GPU cluster, run one Ollama service per GPU or machine and configure
workers to target different `OLLAMA_BASE_URL` values. With only one 8 GB VRAM GPU,
multiple Ollama GPU containers will compete for the same memory, so this compose
file is best treated as a deployment scaffold and report evidence rather than a
guarantee of higher local throughput.
