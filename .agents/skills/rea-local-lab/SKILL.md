---
name: rea-local-lab
description: Use REA and local workers with verified evidence.
version: 1.0.0
author: [USER] (project-contributor), Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [rea, ghidra, ollama, qwen, worker, evidence]
    related_skills: [switch-static-recompilation]
---

# REA local lab

Use this skill for reverse-engineering work performed through REA/Ghidra or a
local worker. It defines the project contract: Claude orchestrates and verifies;
local qwen workers investigate or implement only through the checked harnesses.
It does not authorize handling private game content outside ignored directories.

## When to Use

- Investigating an executable with REA/Ghidra: callers, callees, strings,
  functions, imports, or control flow.
- Writing, dispatching, or reviewing a card for the local qwen worker.
- Reviewing a worker report, a REA report, or an evidence claim.
- Preparing a reproducible RE finding for `docs/`.

Do not use this as a substitute for the static-recompilation workflow; load
`switch-static-recompilation` for extraction, generation, runtime, or Vulkan work.

## Prerequisites

- Read `CLAUDE.md` before acting; it is the authority for roles and privacy.
- Confirm the required target is local and belongs under an ignored `lab/` path.
- Use `tools/rea/rea_worker.py` for binary investigation and
  `tools/workers/local_worker.py` for bounded code-generation cards.
- Keep MSYS2 off the persistent shell `PATH`; add its toolchain only to the
  command that needs it so REA keeps a valid Windows temporary directory.

## Procedure

1. **Establish the task boundary.** Read the relevant source, existing card, and
   nearest prior report. Name the exact output path under `lab/` or `work/`.
   Completion criterion: the request, target, output, and acceptance check are
   explicit before dispatch.
2. **Use the matching harness.** Run the RE worker for a binary question or the
   code worker for a narrowly scoped artifact. Never use a broad Hermes subagent
   as the RE worker. Completion criterion: the harness creates the requested
   output and its machine-readable evidence log.
3. **Review evidence, not prose.** Spot-check at least two substantive claims
   against the report's `.log.jsonl` or equivalent REA output. Check that any
   address, symbol, or function name actually appears in the evidence.
   Completion criterion: `docs/rea-worker-reviews.md` records accept/reject and
   concrete evidence for the verdict.
4. **Record only verified findings.** Put durable conclusions in `docs/` with a
   source path or evidence identifier. Keep raw game-derived outputs in ignored
   directories. Completion criterion: no private bytes, keys, or generated game
   code enter tracked files.
5. **Close with the project gate.** If the work changes tracked project files,
   run the applicable `tools/verify/gates.py` command and record its real
   `run_id`. Completion criterion: the claimed result has a reproducible command
   and evidence, or is plainly marked unverified.

## Pitfalls

- Local workers can fabricate plausible reports; an existing evidence identifier
  does not prove the claim attached to it is correct.
- The full REA MCP catalog is too large for a local model. Keep worker tools
  constrained through the supplied harnesses.
- `hactool` warnings can include key material. Never copy raw extractor output
  into cards, docs, commit messages, or chat summaries.
- A successful compilation or static analysis result is not a runtime proof.

## Verification

- Use `python tools/verify/gates.py score -v` to inspect recorded worker claims.
- Run the relevant gate rather than accepting a worker statement about build,
  link, boot, or gameplay status.
- Before a commit, run `python tools/verify/gates.py lint --staged` and inspect
  `git diff --cached` for private or generated content.
