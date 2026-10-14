# Pipeline log

Uma linha por cartão de trabalho. Quem lê isto quer saber **quanto trabalho os modelos locais realmente fizeram**.

| Data | Cartão | Dono | Modelo | Tentativas | Tempo | Resultado | Motivo / o que o Claude corrigiu |
|---|---|---|---|---|---|---|---|
| 2026-10-14 | RE whoami.exe → LookupAccountSidW (run 1) | subagente Hermes | qwen3-coder-64k | 1 | 2m10 | ❌ rejeitado | 0 chamadas de ferramenta; relatório inventado |
| 2026-10-14 | idem (run 2) | rea_worker v1 | qwen3-coder-64k | 1 | 5m30 | ❌ rejeitado | seguiu a string em .rdata, não o import |
| 2026-10-14 | idem (run 3) | rea_worker v2 | qwen3-coder-64k | 1 | 5m28 | ⚠️ aceito c/ correção | inventou o chamador `FUN_14000377c` |
| 2026-10-14 | idem (run 4) | rea_worker v3 | qwen3-coder-64k | 1 | 7m58 | ✅ aceito c/ ressalvas | ids citados do decompile, não do xrefs |
| 2026-10-14 | F1.1 fork do recompilador do LAS em `Pokemon Decompile/` | Claude (exceção 3: infraestrutura) | — | 1 | ~5 min | ✅ | cópia + 3 ajustes; test_simd 1500 encodings / 74.950 casos, 0 falhas |
| 2026-10-14 | F1.3 W01 helpers C LDXP/STXP 128 bits (`runtime/excl_pair.h`) | qwen (local_worker) | qwen3-coder-64k | 2 | 42 s + 16 s | ✅ aceito | t1: ordem de memória inválida no `stlxp64` (falha SEQ_CST > sucesso RELEASE); t2 corrigiu. 500/500 casos = Unicorn |
| 2026-10-14 | F1.3 W02 lifter LDXP/LDAXP/STXP/STLXP (`recomp/excl_pair.py`) | qwen (local_worker) | qwen3-coder-64k | 2 | 12 s + 37 s | ⚠️ aceito com revisão | t1: `bits()` com bit alto em vez do baixo (todos os registradores errados). t2 corrigiu, mas trocou `Insn('op')` por `Insn('ldxp')` (o gen.py **descartaria a instrução em silêncio**) e deixou `;;`. Claude corrigiu 4 linhas; teste de aceite agora checa o tipo. 15.832 instruções do `main` antes não suportadas → 0 |
| 2026-10-14 | F1.2 layout N módulos + pvgame.h/entry + host M1 + scripts de compilação/link | Claude (exceção 3: interface/infra de verificação) | — | 1 | ~15 min | ✅ M1 | 271.027 funções validadas na DLL |
