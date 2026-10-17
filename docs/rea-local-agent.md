# REA Lab: guide for the local agent

> Reader: the local agent (a local model via Ollama, driven by the harnesses in `tools/`).
> Orchestrator: Claude, in the Hermes desktop session. It plans, hands out
> tasks, and checks the reports. You do the heavy investigation work.
> Everything here was tested on this machine (10/14/2026).

---

## 1. Machine and environment (verified facts)

| Item | Value |
|---|---|
| OS | Windows 11, shell = git-bash (POSIX syntax; `/d/...` works in bash) |
| GPU / RAM | RTX 3070 Ti 8 GB VRAM / 32 GB RAM |
| REA | `D:\Dev\REA\ref\rea-main\rea-main` (6.4.0, snapshot of `main`, local build) |
| Windows native addon | built with MinGW in `native\windows\build` (`verify:windows-native:artifact` OK) |
| Ghidra | `D:\Tools\ghidra_12.1.4_PUBLIC` (`GHIDRA_INSTALL_DIR`) |
| JDK | `D:\Tools\jdk-21.0.12.1+1` (`JAVA_HOME`) |
| Node | `C:\Program Files\nodejs\node.exe` v24.18 (= `.nvmrc`) |
| Lab | `D:\Dev\REA\lab\` → `targets\`, `reports\`, `snapshots\` · scripts in `D:\Dev\REA\tools\rea\` |
| Worker model | `devstral:24b` (24B dense, ctx up to 131072) via `http://127.0.0.1:11434/v1` (until 10/17: `qwen3-coder-64k`, now removed) |

`rea doctor --provider ghidra` = all OK. Hopper does not exist on Windows.
IDA and JADX (Android) **are not configured**: do not try to use them.

### What works on Windows (Ghidra P0, experimental)
- Native x86/x86-64 PE (EXE and DLL) on a local NTFS disk. **Read-only.**
- Static analysis of JavaScript/Electron (`analyze-javascript-application`): does not need Ghidra.
- **Does not work here:** .NET/managed via Ghidra, targets outside NTFS, debugging (gdb/rizin), Android without JADX.

---

## 2. Architecture

```
Claude (Hermes desktop): orchestrator
  ├─ defines the question, splits it into cards, reviews and accepts/rejects
  └─ terminal (background) ──► python D:\Dev\REA\tools\rea\rea_worker.py   ← HARNESS
                                  ├─ Ollama /api/chat  →  devstral:24b (worker)
                                  ├─ tools: rea(callers|search|xrefs|function|decompile|analyze), finish
                                  ├─ contract verified in code (section 3)
                                  └─ reports\<target>-<topic>.md  +  .log.jsonl (every call and output)
```

**Do not use `delegate_task` (Hermes subagent) as an RE worker.** Tested on
10/14: qwen received Hermes's large prompt, spent 2 min processing it, and
wrote a **100% invented** report (zero tool calls, "MSDN-style" code,
a `main` function that does not exist). The `rea_worker.py` harness fixes this:
short prompt, only 2 tools, and the report is refused if it does not match the real outputs.

**Why CLI and not MCP for the worker:** REA's full MCP catalog has
**207 tools, about 220k tokens of schemas alone**. It does not fit in the
local model's context. The `rea.sh` wrapper returns only `evidence_id`, `confidence`, and
`normalized_result`, capped at 2000 tokens per call.

MCP is for Claude, filtered to 21 tools (about 8k tokens).
See section 7.

---

## 3. Worker contract (mandatory)

Enforced **in code** by `rea_worker.py` (the report is refused up to 3 times, then `FAILED_CONTRACT`):
- `finish` only after at least 3 successful REA calls;
- every cited `ev_...` must come from a call in this run;
- every cited `FUN_…`/`LAB_…`/`DAT_…`/`0x…` (6+ digits) must appear in some REA output;
- mandatory sections: Observed, Inferred, Failures.

What the code does **not** catch (Claude reviews it): a real id cited for a
wrong claim. Example from the test: "no references", citing the xrefs of the *string*
`LookupAccountSidW` in `.rdata` instead of the `EXTERNAL:0x4` import.

Rules for the model:

1. **Every claim cites the `evidence_id`** of the REA output that supports it.
2. Separate **Observed** (literally in the output) from **Inferred** (your interpretation).
3. **Never invent** an address, function name, string, or code. If a command
   failed, copy the exact error into "Failures" and continue with what you have.
4. One target, one question. Default budget: at most 12 REA calls per card.
5. Do not modify the target, do not run the target, do not download binaries.
6. **Always** finish with the report in the section 6 format, even if incomplete.
   An honest report with "not found" is worth more than a pretty, false one.
7. If you get stuck (3 identical errors, or the question needs an unavailable tool),
   stop and write what was missing under "Escalate to Claude".

---

## 4a. Run the worker (harness)

```bash
cd /d/Dev/REA
python tools/rea/rea_worker.py --target 'D:\Dev\REA\lab\targets\whoami.exe' \
  --question 'Which internal function calls LookupAccountSidW and what does it do?' \
  --out 'D:\Dev\REA\lab\reports\whoami-lookupaccountsid.md'
# options: --model devstral:24b  --max-steps 14
# output: .md report (with a <!-- harness: stats --> footer), .log.jsonl, or .FAILED.txt
```

Measured cost (whoami.exe, 3070 Ti, with the old qwen3-coder-64k): about 5.5 min, 7 to 13 REA calls, about 37k
local prompt tokens and **0 API tokens**. Claude only reads the final report and checks 2 or 3 ids in the `.log.jsonl`.

## 4b. Verified commands (via the wrapper, for manual/Claude use)

Each call takes about 20 s, because Ghidra re-analyzes the file. This is normal; do not cancel.
Always pass the target path in single quotes, with Windows backslashes.

```bash
R=/d/Dev/REA/tools/rea/rea.sh
T='D:\Dev\REA\lab\targets\whoami.exe'

$R analyze  "$T" --provider ghidra          # overview: segments, number of functions/strings
$R search   "$T" LookupAccountSid --kind procedures   # functions/imports by name
$R search   "$T" "text"                     # strings (default) ; --mode regex for regex
$R xrefs    "$T" 'EXTERNAL:0x4'             # who references an address/symbol
$R function "$T" 0x140003d24                # full dossier of the function containing the address
$R decompile "$T" FUN_140003c90             # pseudocode (name or address)
$R <command> --help                         # help for any command

REA_OFFSET=2000 $R decompile "$T" FUN_...   # next window of a long output
REA_TOKENS=4000 $R function "$T" 0x...      # larger window (use sparingly)
REA_RAW=1 $R ...                            # full envelope (large; avoid)
```

Reading tips (typical x64 PE, `image_base 0x140000000`):
- `EXTERNAL:0xN` = function imported from a DLL.
- Address in `.rdata` = import/data table, **not** code. Code lives in `.text`.
- `FUN_<address>` = name generated by Ghidra (the PDB is not applied).
- `confidence: observed` = fact from Ghidra; `derived` = composed by REA.

Typical flow: **search** (finds import/string) → **xrefs** (finds where it is used)
→ **function** (which function contains it) → **decompile** → repeat with callers/callees.

---

## 5. Model choice (3070 Ti 8 GB + 32 GB)

Models installed in Ollama (since 10/17):

| Model | Use in the lab | Note |
|---|---|---|
| `devstral:24b` | **default worker** | 24B dense, ctx up to 131072, good with tool calls; ~60% on CPU with offload → ~5 tok/s |
| `qwen3.8:27b` | alternative / Hermes fallback | dense, 17 GB → also slow with 8 GB VRAM |

Removed on 10/17 (kept here because the measurements above used it): `qwen3-coder-64k` (30B MoE with about 3B active →
fast even with RAM offload, ~37 tok/s), `qwen3-64k`, `qwen2.5-coder:14b-instruct-q4_K_M`. On this hardware a MoE model
is the fastest option, because only the active experts are read per token.

Memory rules:
- Minimum context for the Hermes agent: **64k**. With Ollama's 4k default,
  the prompt is silently truncated and the model never sees the tools.
- The worker uses about 16 GB at ctx 16k (~26 GB at full ctx). Close heavy Unity and Chrome first.
  One model at a time, **sequential** agents.
- `ollama stop devstral:24b` when the batch is done.

---

## 6. Report format (`D:\Dev\REA\lab\reports\<target>-<topic>.md`)

```markdown
# <target>: <short question>
## Question
## Observed
- <fact> (ev_xxxxxxxx)
## Relevant code (decompiled excerpt)
## Inferred
- <hypothesis> (based on: ev_..., ev_...)
## Failures / open questions
## Escalate to Claude (if applicable)
## Commands executed
```

---

## 7. Claude/MCP setup (the human applies it: Hermes blocks the agent from editing the config)

`rea setup` already registered the `rea` server in `%LOCALAPPDATA%\hermes\config.yaml`
and in Claude Code. To avoid loading 220k tokens of schemas, replace the
`rea:` block in `mcp_servers` with this one and run `/reload-mcp` (or restart Hermes):

```yaml
  rea:
    command: C:\Program Files\nodejs\node.exe
    args:
      - D:\Dev\REA\ref\rea-main\rea-main\scripts\rea.mjs
      - mcp
    env:
      GHIDRA_INSTALL_DIR: D:\Tools\ghidra_12.1.4_PUBLIC
      JAVA_HOME: D:\Tools\jdk-21.0.12.1+1
      REA_MCP_INPUT_SCHEMA_PROFILE: compact
      REA_MCP_OUTPUT_SCHEMA_PROFILE: 'off'
    enabled: true
    timeout: 600
    tools:
      include: [binary_session, open_binary, binary_overview, list_procedures,
        search_procedures, procedure_info, procedure_pseudo_code, procedure_callers,
        procedure_callees, procedure_references, xrefs, find_xrefs_to_name,
        list_strings, search_strings, list_segments, list_names, analyze_function,
        batch_decompile, get_call_graph, list_unknowns, analyze_javascript_application]
      resources: false
      prompts: false
```

Advantage of MCP over the CLI: the MCP session keeps Ghidra open, so only the
first query pays the roughly 20 s. If the worker proves it can handle MCP,
it can be migrated later.

---

## 8. Lab roadmap (in order)

1. ✅ REA + Ghidra + JDK + addon installed, `doctor` green.
2. ✅ `rea.sh` wrapper with lean output.
3. Done (manual review by Claude; no gate applies to RE answers): reference test `whoami.exe` → `LookupAccountSidW` (correct answer: `FUN_140003bc0`,
   which enables `SeDebugPrivilege` and resolves the SID of `param_1` into `DOMAIN\name`).
   - run 1 (Hermes subagent): invented report → **rejected**
   - run 2 (harness v1): honest but did not find it (followed the string instead of the import)
   - run 3 (harness v2 + `callers`): **got it right**; 1 error (called the call-site address `0x14000377c` a function)
   - run 4 (harness v3 + ghost-symbol check): **accepted with review**. Also found the 2 callers
     (`FUN_140003498`, `FUN_140003b3c`), no invented symbols, 8 min, 0 API tokens.
     Caveats: cited ids from the decompile instead of the xrefs; left the code section empty.
   - Reviews in `reports/REVIEW.md`
4. Measure per card: REA calls, time, worker hits/misses, tokens spent by Claude.
5. Own targets (a program you compiled) → then real apps (always x64 PE, NTFS).
6. If process capture / Frida / gdb is needed → move the lab to Linux
   (the other drive). Ollama and the models are the same.

## 9. Do and don't

- ✅ Copy the target to `D:\Dev\REA\lab\targets\` before analyzing it (REA refuses mutable/sensitive paths).
- ✅ One question per card; Claude chains the cards.
- ❌ Do not analyze software you do not have the right to analyze (license/EULA). Use your own or system binaries for study.
- ❌ Do not paste huge raw output into the report: only the relevant excerpt + `evidence_id`.
- ❌ Do not say "build OK"/"found it" without the output that proves it.
