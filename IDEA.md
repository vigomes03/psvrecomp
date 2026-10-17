# IDEA: why this workspace exists

## The goal in one sentence
Decompile and statically recompile **Pokémon Scarlet/Violet** (Nintendo Switch) into a native Windows application,
for **personal use only**, and use that work to understand **how a modern triple-A game is built**.

## Two goals, in this order

### 1. A working native port: PSV Recomp
Do for Pokémon Violet what [LAS Recomp](https://github.com/peiikai/LASRecomp) did for *The Legend of Zelda: Link's
Awakening*:
- translate the game's ARM64 code to C **once, ahead of time** (static recompilation, no CPU emulation at runtime);
- run it on a native runtime that re-implements the Switch OS (Horizon: kernel, IPC, services) in C;
- re-implement the NVN graphics API on top of Vulkan and translate the Maxwell shaders to SPIR-V;
- ship it as a Windows app with its own settings menu, launcher, and quality-of-life features (resolution, frame
  pacing, upscaling, anti-aliasing).

The game must run from a dump of **my own cartridge**, decrypted with keys from **my own console**.

### 2. Study: how a AAA game works inside
Once the game runs, use the recompiled build as a laboratory:
- the engine architecture (threads, streaming, memory, job systems);
- the file formats (`trpfs`/`trpfd`, FlatBuffers `tr*` data) and how the open world is streamed;
- the rendering pipeline (passes, compute culling, shadows, fog, post-processing);
- the gameplay systems (battle, encounters, AI, save data).

Findings are written as **documentation of how things work**, with sources, never as copies of the game's code or
assets.

## Non-goals
- No piracy: no ROM, key, firmware, or game file is downloaded, shared, or committed.
- No redistribution: no builds, generated code, or game-derived data leave this machine.
- No online features: network services answer "offline".
- No CPU emulator: the CPU code is recompiled; only the GPU shaders are translated at runtime.

## How the work is done
- **Claude orchestrates; local models execute.** Claude plans, writes small verifiable work cards, reviews, and
  decides architecture. Local models (Ollama, see [CLAUDE.md](CLAUDE.md)) do the bounded work through harnesses that
  check their output in code.
- **Evidence over claims.** "Builds", "boots", and "phase done" only count with a `run_id` recorded by
  `tools/verify/gates.py`.
- **Reference implementations as oracles.** Unicorn for single instructions, Eden for expected game behavior and
  images, LAS Recomp for the recompilation process. Eden is GPL-3 and is read for understanding, never copied.

## What success looks like
| Milestone | Meaning |
|---|---|
| M0-M2 | Dump extracted, all code recompiles and links, the game boots headless to its main loop |
| M3-M4 | First pixel, then the title screen with sound and working input |
| M5-M6 | New game, character control, and 10 minutes in the open world without a crash |
| M7 | A real app: launcher, settings, extra features |
| Beyond | Documentation of the engine, formats, and systems (the study goal) |

Current status of each milestone: [docs/roadmap/README.md](docs/roadmap/README.md).
