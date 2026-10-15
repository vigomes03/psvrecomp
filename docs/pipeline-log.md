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
| 2026-10-14 | Fallback (Claude sem limite): "fase 3/4 concluídas", HLEs, boot, base v4.0.0 | qwen (chat Hermes) | qwen3-coder-64k | — | ~1 h | ❌ 7 afirmações falsas | scripts só com `echo PASSOU`, main.c trocado por printf, `rm -rf dumps/base`, docs falsificados. Ver `gates.py score -v` |
| 2026-10-14 | Reparo: main.c do host refeito do original, stubs falsos removidos, build_host volta a gerar `pvhost.dll.a`, dump re-extraído | Claude (exceção 3) | — | 1 | ~30 min | host run_id=1a08d1116c, dumps run_id=920a8818e9 | boot real para em init_sdk (exceção em 0x20) run_id=990a33212b |
| 2026-10-14 | Harness anti-fake `tools/verify/gates.py` + `test_gates.py` + pre-commit | Claude (exceção 3) | — | 1 | ~25 min | test_gates 13/13 | fixtures = os fakes reais do fallback |
| 2026-10-14 | Update v4.0.0: hactool upstream (1d64a83 = HEAD do SciresM) recusa o BKTR (subsection termina 0x4200 antes do fim da seção). Patch `tools/hactool/bktr-tail.patch` relaxa o teste | Claude (exceção 3) | — | 1 | ~15 min | exefs v4.0.0 extraído, hashes SHA-256 dos 3 NSOs batem (`nso_verify.py`); romfs NÃO: `-y` diz "section 1 is corrupted" | os 0x4200 extras devem ser a tabela de compressão (NCA comprimido, SDK 13.3.13), que o hactool não implementa |
| 2026-10-14 | Romfs v4.0.0 com o hactoolnet do [USER] (precisa do .NET 8 x86, portátil em `D:\Tools\dotnet8-x86`, `DOTNET_ROOT_X86`) | Claude (exceção 3) | — | 1 | ~10 min | 30 arquivos, 9,3 GB; `romfs_verify.py`: 6 iguais à base, 16 .bnk com estrutura íntegra, trpfs com índice válido; gate dumps v400 (ver gates.jsonl) | hactoolnet `-y` marca "Master Hash (FAIL)" na seção patch mas "Section Validity: Valid": em aberto |
