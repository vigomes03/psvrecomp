# AGENTS.md

As diretrizes deste workspace estão em [CLAUDE.md](CLAUDE.md) e valem para qualquer agente (Claude, Hermes, Codex,
qwen local). Resumo: **Claude orquestra; os modelos locais executam via `tools/rea/rea_worker.py` e
`tools/workers/local_worker.py`; nada do jogo (dump, chaves, código extraído) entra no git.**
