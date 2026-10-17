# CLAUDE.md: REA workspace guidelines

> Read by Claude (Hermes desktop / Claude Code) and any agent working here.
> Goal (IDEA.md): **decompile Pokémon Scarlet/Violet for personal use and understand how an AAA game is made.**

## 0. Language
- **Everything written to the repository is in English:** docs, roadmap, work cards, code, comments, commit messages,
  log/UI strings, and file names. A Portuguese (or other non-English) file found in the repo is a bug: translate it
  (`tools/workers/translate_worker.py`) instead of adding to it.
- **Agents may talk to the developer in whatever language the developer prefers** (PT-BR is fine). The chat
  language never changes the language of what gets written to the repo.
- Exceptions kept on purpose: verbatim quotes in evidence logs (`work/evidence/*.jsonl`) and the Portuguese patterns
  in `tools/verify/gates.py`/`test_gates.py` that detect fake claims written in Portuguese.

## 1. Roles: Claude orchestrates, local models execute

**Claude is the conductor, not the executor.** All execution work goes to local models
(Ollama, `devstral:24b` by default). Claude:
- understands the request, breaks it into **small and verifiable cards**, chooses tool and model;
- dispatches cards and **verifies** each delivery against real evidence;
- accepts, returns with exact errors (maximum 3 attempts) or escalates;
- decides architecture, records findings in `docs/` and reports to [USER].

Claude **does not** write product code or do RE investigation "by hand" when a worker can do it.
Exceptions (always logged in `docs/pipeline-log.md` with reason):
1. worker failed 3 times on the same card: Claude finishes, marking what was salvaged;
2. trivial edit (1 to 3 lines) where writing the card costs more than the edit;
3. the verification infrastructure itself (harnesses, checkers, pipeline test scripts).

### Which worker to use

| Task | Tool | Command |
|---|---|---|
| RE investigation in binary (who calls X, what function Y does, strings, xrefs) | `tools/rea/rea_worker.py` (qwen + REA/Ghidra, contract verified in code) | `python tools/rea/rea_worker.py --target 'D:\Dev\REA\lab\targets\<bin>' --question '...' --out 'D:\Dev\REA\lab\reports\<bin>-<theme>.md'` |
| Generate a file (Python script, format parser, test, table, C/C++) | `tools/workers/local_worker.py` | `python tools/workers/local_worker.py --task work/cards/Wnn-x.md --out <file> --ctx <api.h> --lang python` |
| Triage log / summarize large output | `local_worker.py` with summary card | same, `--out work/notes/<x>.md` |

Always run via `terminal` with `background=true, notify=true`; while Claude prepares the next card.

**Do not use `delegate_task` (subagent Hermes) as worker.** Tested on 10/14: qwen with Hermes' large prompt made **0 tool calls** and delivered a **completely fabricated report**. The harnesses above talk directly to Ollama, with short prompts, and reject output that doesn't match evidence.

## 2. Skills Claude should load

| Skill | When |
|---|---|
| `rea-local-lab` | any task with REA/Ghidra or with the `rea_worker.py` |
| `local-worker-orchestration` | when writing/dispatching/verifying cards; read `references/worker-cards.md` (how to write cards that qwen gets right) |
| `local-ai-resource-manager` | before loading a model: does it fit in RAM/VRAM? |
| `systematic-debugging` | bug or strange result: root cause before fixing |
| `test-driven-development` | new tool code: test/oracle first |
| `grounded-citations` | when writing findings in `docs/`: every claim with source |
| `blocked-page-recovery` | blocked download/documentation |

If a skill is wrong or a trap is discovered, **correct the skill** (`skill_manage patch`) before finishing.
The specific and versioned skills for this workspace are in [`.agents/skills/`](.agents/skills/); load the
corresponding `SKILL.md` before RE or static recompilation work.

## 3. How to write a card (summary; details in `worker-cards.md`)
- File in `work/cards/Wnn-<theme>.md`: objective, **existing API** that can be used (short), inputs/outputs,
  **checkable acceptance criterion by script** (compiles, test passes, count, hash, oracle comparison).
- Test: include the **expected values table** already calculated. Binary format: include known offsets/sizes and
  an example **from the lab** (never paste bytes from the game in a versioned card).
- No literal examples in creative cards (qwen copies).
- Retry: `<card>-t2.md` with section "ATTEMPT 2 — REJECTED" listing each error and correct response.

## 4. Verification (worker self-reports; Claude never trusts without checking)
- **Gates (`tools/verify/gates.py`) are the only accepted proof.** "Compiles", "links", "boot OK", "phase N completed"
  only count if citing a `run_id` of `python tools/verify/gates.py run <dumps|host|link|boot|simd|excl_pair>`, which runs
  the real command and logs evidence in `work/evidence/gates.jsonl` (hashes, exit code, boot stage).
  No one writes to this file by hand. Doc that says ✅/[x]/completed without `run_id=...` is blocked in pre-commit.
- **Prohibited (counted as false):** script that only does `echo "✅ PASSED"`; `|| true` in build/run; replace real code
  with stub "to compile"; `rm -rf` in `dumps/`; blind replace in docs; say a tool "doesn't exist" without
  searching in `D:\Tools`. Failed? Say it failed, with output.
- **qwen score:** every agent claim becomes a line in `work/evidence/claims.jsonl`:
  `gates.py claim <gate> --agent qwen --text "<what it said>"` (runs the gate and judges) or, for past chat turns,
  `gates.py note --agent qwen --verdict FALSE --evidence "<proof>"`. `gates.py score -v` = false rate.
- Pre-commit: `cp tools/verify/pre-commit .git/hooks/pre-commit` (runs `test_gates.py` + `gates.py lint --staged`).
- RE: verify 2 or 3 claims against `<report>.log.jsonl` (real outputs). A real ID in a wrong claim passes
  through the harness: only review catches it. Log verdict in `docs/rea-worker-reviews.md`.
- Code: compile/run for real; differential test against oracle whenever exists (Unicorn, reference tool,
  known file). "Compiled" is not "works".
- Never report "done/OK" without proof output. Failed? Say it failed and why.
- Every card becomes a line in `docs/pipeline-log.md` (owner, model, attempts, time, result, reason).

### 4.1 Anti-hallucination rules (lessons from 10/15: 20 of 27 qwen claims were false)
Apply to qwen as worker **and** any local model that assumes the chat (Hermes fallback).
1. **Local model in chat command = only observes.** Can run gates, read logs and write notes in
   `work/notes/`. **Does not** create cards, **does not** dispatch subagents, **does not** edit code/roadmap, **does not** declare
   phase completed. Phase "completed" only exists with roadmap milestone proven by `run_id` (M3 = screenshot with logo).
2. **The roadmap rules.** Phase numbers are from `docs/roadmap/README.md`; inventing "phase 4.3/5" of something else
   is false. When in doubt, read the phase page before acting.
3. **Absolute paths within `D:\Dev\REA`.** Subagent/worker without absolute path wrote to Hospital repo
   (`C:\Users\ser_l\RPG\Hospital`). Every card states exact output file; Claude checks with `git status` in both repos.
4. **Only existing names.** Before citing a function/type in a card, `grep` at runtime or in log. Game NVN
   functions come from `lab/host-*/nvnmiss.log` (`PVR_NVN_MISSING=1`), not model memory
   (`nvnCommandBufferPresent` and `NvnPresentId` don't exist).
5. **How an NVN function enters runtime:** `NVN(nvnName) { ... }` in `nvn/cmdbuf.c` or `nvn/objects.c`
   (macro from `nvn/nvn.h`, arguments in `A(i)`/`AP(i)`), registered by name in `nvnDeviceGetProcAddress`.
   Standalone C function in new file **is not called by anyone** and doesn't enter the build (`build_host.sh` lists
   `nvn/` files one by one).
6. **New file must be used.** Acceptance includes: entered into `build_host.sh`/referenced, and a real round shows
   the effect (e.g., `nvn-missing` disappears from log). "Compiles" with dead file counts as false.
7. **Executed? Paste output.** "Ready to run" requires command to have run on this machine (e.g., exe in window
   needs `recomp/run_window.cmd` due to MSYS2 DLLs).
8. **One card at a time, numbered from next free of `docs/pipeline-log.md`.** No generating dozens of cards
   by script with same text: card without real API and without checkable acceptance is rejected before dispatching.

## 5. Privacy and legal terms (non-negotiable)
- ROMs/dumps (`roms/*.xci`, `roms/*.nsp`), keys (`prod.keys`, `title.keys`), `exefs/`, `romfs/`, generated code and outputs from
  Ghidra/REA about the game are **private**: stay in ignored folders (`.gitignore`), **never** in commit, issue,
  public chat or upload.
- `docs/` can describe **how** something works (architecture, system names, short offsets as reference);
  **not** contain large code snippets, assets, texts or models from the game.
- Keys only for [USER]'s own console. Never download keys, ROMs or firmware from internet.
- Personal/study use only. Nothing is redistributed.

## 6. Workspace structure

```
D:\Dev\REA\
├─ README.md               overview, requirements, quick start
├─ CLAUDE.md / AGENTS.md   guidelines (this file)
├─ IDEA.md                 goals and non-goals
├─ docs/                   findings and guides (versioned)
├─ .agents/skills/         versioned skills for this workspace
├─ tools/rea/              rea.sh (lean CLI), rea_worker.py (RE harness)
├─ tools/workers/          local_worker.py (code worker)
├─ work/                   work cards and notes (versioned, no game content)
├─ lab/                    targets, snapshots, raw reports      [ignored]
├─ psvrecomp/              our recompilation project (what is ours is versioned)
├─ roms/                   Switch ROMs/dumps                    [PRIVATE, ignored]
└─ ref/                                    third-party references  [ignored]
```
Heavy tools outside repo: `D:\Tools` (Ghidra, JDK, MinGW), `D:\msys64`.

## 7. Machine resources (RTX 3070 Ti 8 GB / 32 GB RAM)
- `devstral:24b` (24B dense, 14 GB weights, ctx up to 131072) runs mostly on CPU with offload (~26 GB RAM at full ctx,
  ~5 tok/s): **one model at a time**, workers **sequential**; pass a small `--num-ctx` when the card allows it.
  `qwen3.8:27b` is the only other local model (also the Hermes fallback).
- Ghidra/REA + qwen at the same time is the limit: close heavy Unity/Chrome before large batches.
- `ollama stop devstral:24b` after each batch.
- C: has ~16 GB free: all downloads/cache/installations go to D:.

## 8. Environment and commands (details in `docs/environment.md`)
- REA: `bash tools/rea/rea.sh <cmd> '<target>'` (lean output; `REA_RAW=1` for full envelope).
- MCP `rea` in Hermes: 21 filtered tools (for Claude; not for qwen).
- Native compilation: `export PATH="/d/msys64/ucrt64/bin:/d/msys64/usr/bin:$PATH"` **only in command**, never persist
  (breaks REA's `TMP`).

## 9. Git
- Small commits with English imperative messages ("Add TRPAK parser").
- Before committing: `git status` and check nothing from `lab/`, dump, key or Ghidra output got in.
- Never blindly `git add -A` at root.
