# AGENTS.md

The guidelines for this workspace are in [CLAUDE.md](CLAUDE.md) and apply to any agent (Claude, Hermes, Codex,
local qwen). Summary: **Claude orchestrates; the local models execute via `tools/rea/rea_worker.py` and
`tools/workers/local_worker.py`; nothing from the game (dump, keys, extracted code) goes into git.**
Everything written to the repo is in English; agents may reply to the developer in any language they prefer.
