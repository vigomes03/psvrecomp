# W20 (TENTATIVA 2) — glsl_slice.py: backward def chain in a translated Maxwell shader

Write ONE file: `D:\Dev\REA\tools\rea\glsl_slice.py` (Python 3, stdlib only).

## Input format (GLSL produced by our translator)
- Each guest instruction starts with a comment line `    // pc <HEX>: <16 hex digits>`. The pc is hex, no `0x` (e.g. `// pc 25f0: ...`).
- Instruction bodies follow, until the next `// pc` line. They may be:
  - plain assignment: `    rN = <expr>;`
  - predicated: a line `  if (pK) {` or `  if (!pK) {`, then assignments, then `  }`. The predicate string is `pK` or `!pK`.
  - texture block: a line starting with `{ vec4 t = ...` or `{uvec4 t = ...` or `{ uint lv = ...` whose expression
    uses registers, then lines `rN = as_u(t[i]);` / `rN = q[i];`, then `}`. Every `rN` assigned in the block uses the
    registers of the block's first line.
- Lines like `case 123u:`, `pc = ...; continue;`, `exit_now = true; break;`, `uint rN = 0u;` declarations before
  `switch` are NOT definitions (ignore declarations: lines matching `^\s*uint r\d+ = 0u;`).
- Registers are `r` + digits. Use regex `\br(\d+)\b` to find them. `cb3[1][0]`, `t[0]`, `p0` are not registers.

## CLI
`python glsl_slice.py <file> --pc <hex> --reg rN [--depth D]` (depth default 8 = max recursion levels).

## Algorithm (ignore control flow; walk the file text backwards)
1. Parse the file FORWARD first into a list of instructions: for each `// pc` comment, record its pc and the lines of
   its body (up to the next `// pc` comment). Then the target instruction is the one with the given pc. The walk for
   the target register starts at the LAST line of the target instruction's body (the target's own assignment counts:
   with `--pc 28 --reg r6` the row `r6 @ 28` must be emitted).
2. For a wanted register R at a start line: walk backwards. At each assignment to R (left side exactly `rN =`, not `==`):
   - emit a row; if the assignment is inside a predicated block, set `pred` to that predicate and KEEP walking
     backwards for an earlier definition of R; otherwise stop for R.
   - If the start of the file (the `switch` line) is reached with no unpredicated definition, emit a row with
     `pc: null` (meaning: initial value / undefined).
3. `uses` = all registers on the right-hand side (for texture blocks: registers of the block's first line), R itself
   included when it appears (e.g. `r10 = r10 * r11` uses r10 and r11); no duplicates, sorted by number. Recurse on each used register starting
   at the line of that definition, depth+1, until `--depth`.
4. Each (reg, pc) pair is emitted once (dedupe). `pc` of a row = the pc of the `// pc` comment the assignment belongs to.

## Output: one JSON object per line on stdout
`{"reg": "r3", "pc": "18", "line": 17, "pred": null, "stmt": "r3 = as_u(t[0]);", "uses": ["r2", "r5"], "depth": 1}`
- `line` = 1-based line number of the assignment (int); for `pc: null` rows, `line: null`, `stmt: null`, `uses: []`.

## Acceptance (script-checked)
`python D:\Dev\REA\tools\verify\test_glsl_slice.py` prints `PASS` (it contains the fixture and the expected set).
Do not edit the test.

## TENTATIVA 1 — REJEITADA (test printed nothing: `FAIL set: missing` everything)
Errors in attempt 1, each with the correct behaviour:
1. Walking backwards, it read the pc from a `// pc` comment ABOVE the assignment only after passing it, so the pc was
   wrong/unset. Correct: build the instruction list forward (step 1); each body line knows its pc.
2. It started the search before the target's comment, so the target's own definition was missed. Correct: step 1.
3. After an UNPREDICATED definition it kept walking. Correct: stop for that register; continue only past predicated ones.
4. It never emitted the `pc: null` row when no unpredicated definition exists. Correct: step 2, emit
   `{"reg": R, "pc": null, "line": null, "pred": null, "stmt": null, "uses": [], "depth": d}`.
5. `uses` held digit strings ("3"). Correct: "r3".
6. For texture blocks the uses came from the `rN = as_u(t[0])` line (no registers). Correct: registers of the block's
   first line (`{ vec4 t = texture(t0, vec2(as_f(r2), as_f(r5)));` -> ["r2", "r5"]).
7. The predicate was guessed by looking 20 lines up for any `if (`. Correct: while parsing forward, track whether the
   line is between `  if (pK) {` / `  if (!pK) {` and its closing `  }`.
8. Dedupe was per call. Correct: one global set of (reg, pc) for the whole run, including the null rows.
9. pc strings: keep them exactly as in the comment (lowercase hex, no 0x): "28", "18", "8", "0".
