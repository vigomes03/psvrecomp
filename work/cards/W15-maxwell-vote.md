# W15 — Maxwell Translator: VOTE Instruction (Warp Voting), GLSL Output

## Context
A compute shader from the game fails with `unknown instruction 50d8e38000070010` (VOTE). API in `work/ctx/W15-translate-api.c`:
`bits`, `reg`, `RZ`, `PT` (=7, always true predicate), `pred(c, p, neg, buf)` (reads predicate: returns "p3", "!p3",
"true" or "false"), `set_reg`, `sp(&c->body, ...)`, `c->pred_used[]`, `fail`, `c->glsl`. Registers are `uint`,
predicates are `bool p0..p6`. The GL_KHR_shader_subgroup_vote/ballot extensions are already in the header.

## Deliverable
Only ONE C function: `static void emit_vote(Ctx *c, uint64_t w);` (if `!c->glsl`: `fail(c, "vote msl"); return;`).

## Encoding
| field | bits |
|---|---|
| d (destination register) | 0..7 |
| pa (input predicate) | 39..41 |
| neg_pa | 42 |
| pb (output predicate) | 45..47 |
| op | 48..49: 0 ALL, 1 ANY, 2 EQ, 3 invalid → `fail(c, "vote op 3")` |

## Semantics (in this order, in its own block to avoid reading the result before time)
1. `v` = `pred(c, pa, neg_pa, buf)`.
2. Emit: `sp(&c->body, "    { bool vv = %s;\n", v);`
3. If pb != PT: `c->pred_used[pb] = 1;` and emit `      p<pb> = subgroupAll(vv);` (ALL) / `subgroupAny(vv)` (ANY) /
   `subgroupAllEqual(vv)` (EQ).
4. If d != RZ: emit `      r<d> = subgroupBallot(vv).x;` and mark `c->reg_used[d] = 1;` (DO NOT use set_reg here).
5. Close: `sp(&c->body, "    }\n");`.

## Acceptance (Claude runs)
1. Compile. 2. Real run: `unknown instruction 50d8...` some and no shaderc error appears. 3. Only the requested function.
