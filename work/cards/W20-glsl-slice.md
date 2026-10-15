# W20 — glsl_slice.py: backward def chain in a translated Maxwell shader

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
1. Find the line index of `// pc <hex>:` for the given pc. Start searching for definitions of the register in the
   lines BEFORE that comment.
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
