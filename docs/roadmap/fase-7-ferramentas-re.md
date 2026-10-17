# Fase 7: Ferramentas de RE e debug (contínua, desde a fase 1)

**Objetivo:** enxergar dentro do jogo. O LAS fez RE **instrumentando o jogo recompilado**; nós somamos o REA/Ghidra.

## Do LAS (portar)
- [ ] 7.1 🤖 `FN_ENTER` + `PVR_FNPROF=<de>:<até>`: contagem de entradas de função entre frames; **diff entre duas
  execuções** mostra que código uma ação ativa.
- [ ] 7.2 🤖 `sym.py`: endereço → módulo+offset → símbolo (se houver) + disassembly (Capstone).
- [ ] 7.3 🤖 Busca/"cutucada" de valores na memória (`ADDF_MATCH` do LAS) para achar estruturas (posição do
  jogador, câmera, HP).
- [ ] 7.4 🤖 `shot.sh`/`frames.sh`/`montage.sh` + métricas de imagem (`transients.py`, `bandmetric.py`).
- [ ] 7.5 🤖 Ganchos `PVR_*` documentados onde são definidos (input roteirizado, save temporário, screenshot no frame N...).

## Estado em 15/10
- 🟢 Kit de diagnóstico por variáveis `PVR_*` (lista em `psvrecomp/README.md`), `tools/rea/glsl_slice.py`,
  `tools/verify/run_auto.sh`, gates.
- 🔴 **Falta log/aviso de crash:** o jogo fecha sem mensagem. Item: caixa de erro com a causa (`FATAL`) e o log
  copiado com data, mais um resumo do último estado (cena, frame, último `[draw]`/`[svc]`).

## Nosso (REA)
- [ ] 7.6 🧠 Converter cada NSO para ELF analisável (ou loader NSO do Ghidra) e criar **snapshots REA** por build id
  (`lab/snapshots`, ignorado).
- [ ] 7.7 🤖 `rea_worker` com perguntas sobre o Pokémon: "quem chama X", "o que faz a função Y", com contrato e revisão.
  Achados vão para `docs/re/` (descrição, não código).
- [ ] 7.8 🧠 Nomes: base de nomes para funções/structs descobertas (`work/names.tsv`: endereço, nome, evidência),
  consumida pelo `sym.py` e pelo Ghidra.
- [ ] 7.9 🧠 Ponte "Ghidra ↔ recompilado": abrir no Ghidra a função que o `fnprof` apontou; no código gerado,
  comentário com o nome descoberto.
