# Performance tables - distributed load-balancing simulation

No real RAG + Ollama benchmark has been generated after switching the project to the real inference path.

Start Ollama with the configured `OLLAMA_MODEL`, then run:

```powershell
py scripts\benchmark.py
```

The benchmark will initialize RAG from `data/sample.pdf`, write JSON metrics per scenario, and regenerate this table.
