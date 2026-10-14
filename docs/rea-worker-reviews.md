# Revisões do Claude: worker REA local

Gabarito do Claude (`whoami.exe`): `LookupAccountSidW` é chamada em 0x140003d24, dentro de `FUN_140003bc0`
(ev_8e65ba5e…). Essa função habilita `SeDebugPrivilege` e resolve o SID `*param_1` em `DOMÍNIO\nome`.
Chamadores: `FUN_140003498` (call em 0x14000377c) e `FUN_140003b3c` (call em 0x140003b64), ev_3cb3d430….

| run | executor | REA calls | tempo | veredito | motivo |
|---|---|---|---|---|---|
| 1 | delegate_task (subagente Hermes, qwen3-coder-64k) | 0 | 2m10 | REJEITADO | relatório 100% inventado (main/TokenGroups/malloc, "10 call sites") |
| 2 | rea_worker v1 | 13 | 5m30 | REJEITADO | honesto, mas seguiu a string em .rdata; "sem referências" citando o xrefs errado |
| 3 | rea_worker v2 (+callers) | 7 | 5m28 | ACEITO c/ correção | função certa e código verbatim; inventou o chamador `FUN_14000377c` (era endereço de chamada) |
| 4 | rea_worker v3 (+checagem de símbolos) | 7 | 7m58 | ACEITO c/ ressalvas | função + 2 chamadores certos; ids citados = decompile (não xrefs); seção de código vazia |

## Lições dos cartões de código (W01/W02)
- O qwen confunde `bits(w, lo, n)` com "bit alto": na tabela de campos do cartão, escreva a **chamada pronta** (`bits(w, 16, 5)`), não "bits 20:16".
- Numa retry ele "melhora" partes que já estavam certas (mudou o tipo `Insn('op')`). No cartão de retry, liste o que **não** pode mudar,
  e o teste de aceite deve checar a interface (tipo/assinatura), não só o texto ou o resultado.
- Teste diferencial contra oráculo (Unicorn) pegou o erro que a leitura rápida não pegaria.
