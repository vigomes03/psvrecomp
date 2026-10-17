# Project agent skills

This directory contains the reusable, project-owned skills for this workspace.
They are versioned with the repository so an agent can load the same operating
rules in a fresh clone.

| Skill | Use it for |
|---|---|
| [`rea-local-lab`](rea-local-lab/SKILL.md) | REA/Ghidra investigation and local-worker evidence review. |
| [`switch-static-recompilation`](switch-static-recompilation/SKILL.md) | Extraction, static recompilation, Vulkan builds, tests, and PSV Recomp runtime work. |

These are the two maintained skills developed for this project. Generic Hermes
skills remain provided by Hermes and are intentionally not copied here.

## Conventions

- Read the relevant `SKILL.md` before changing code or running an investigation.
- `CLAUDE.md` is the workspace authority when it conflicts with a skill.
- Never place ROMs, keys, dumps, generated game code, or raw analysis outputs in
  this directory.
- Keep all project-skill text in English and repository-relative.
