# W15 — Tradutor Maxwell: instrução VOTE (votação do warp), saída GLSL

## Contexto
Um compute shader do jogo falha com `unknown instruction 50d8e38000070010` (VOTE). API em `work/ctx/W15-translate-api.c`:
`bits`, `reg`, `RZ`, `PT` (=7, predicado sempre verdadeiro), `pred(c, p, neg, buf)` (lê predicado: devolve "p3", "!p3",
"true" ou "false"), `set_reg`, `sp(&c->body, ...)`, `c->pred_used[]`, `fail`, `c->glsl`. Registradores são `uint`,
predicados são `bool p0..p6`. As extensões GL_KHR_shader_subgroup_vote/ballot já estão no cabeçalho.

## Entregue
Só UMA função C: `static void emit_vote(Ctx *c, uint64_t w);` (se `!c->glsl`: `fail(c, "vote msl"); return;`).

## Codificação
| campo | bits |
|---|---|
| d (registrador destino) | 0..7 |
| pa (predicado de entrada) | 39..41 |
| neg_pa | 42 |
| pb (predicado de saída) | 45..47 |
| op | 48..49: 0 ALL, 1 ANY, 2 EQ, 3 inválido → `fail(c, "vote op 3")` |

## Semântica (nesta ordem, num bloco próprio para não ler o resultado antes da hora)
1. `v` = `pred(c, pa, neg_pa, buf)`.
2. Emita: `sp(&c->body, "    { bool vv = %s;\n", v);`
3. Se pb != PT: `c->pred_used[pb] = 1;` e emita `      p<pb> = subgroupAll(vv);` (ALL) / `subgroupAny(vv)` (ANY) /
   `subgroupAllEqual(vv)` (EQ).
4. Se d != RZ: emita `      r<d> = subgroupBallot(vv).x;` e marque `c->reg_used[d] = 1;` (NÃO use set_reg aqui).
5. Feche: `sp(&c->body, "    }\n");`.

## Aceite (o Claude roda)
1. Compila. 2. Rodada real: `unknown instruction 50d8...` some e não aparece erro de shaderc. 3. Só a função pedida.
