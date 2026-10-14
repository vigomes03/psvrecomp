# Fase 1: Recompilador ARM64 → C

**Objetivo:** transformar `main` + `sdk` (+ `subsdk*`) em C que compila numa DLL, com semântica provada por
testes diferenciais.

**No Zelda:** `nso.py` → `gen.py` (descoberta de funções em ponto fixo, jump tables via Unicorn, emissão com `goto`
/ `musttail` / `rt_dispatch`) → `lifter.py` (inteiros/memória/controle) + `simd_c.py` (FP/SIMD em C portátil) →
chunks de ~1.500 funções → `clang -O1`. Testes: `test_lift.py`, `test_simd.py`.

## Tarefas
- [x] 1.1 🧠 (14/10, commit local; test_simd 74.950 casos 0 falhas) Criar `Pokemon Decompile/` como **fork local** de `LASRecomp-main/tools` + `runtime/cpu.h`, `simd*.h`
  (cabeçalho MIT preservado). Renomear `LARECOMP_*` → `PVR_*`, `lasgame` → `pvgame`.
- [ ] 1.2 🧠 Generalizar `gen.py` para **N módulos** (main, sdk, subsdk0..n) com bases de carga do npdm/rtld,
  tabelas de função por módulo e `dispatch` com N tabelas.
- [ ] 1.3 🤖 Cartões: cobrir as instruções que o censo da fase 0 apontou como não suportadas. Cada cartão =
  1 grupo de encodings + teste diferencial no Unicorn como critério de aceite.
- [ ] 1.4 🤖 Rodar `test_lift.py` sobre o `main` do Pokémon (amostras aleatórias de instruções reais) → 0 divergências.
- [ ] 1.5 🤖 `test_simd.py` completo (todos os encodings) → 0 divergências (já passou no LAS aqui: 12.000 casos).
- [ ] 1.6 🧠 Escala: gerar 100% do `main`; medir tempo, tamanho do C e tempo de compilação. Se não couber:
  paralelizar o `gen.py` (multiprocessing por faixa de funções) e `make -j` com limite de RAM.
- [ ] 1.7 🤖 Relatório de jump tables: resolvidas / fallback "all labels" / `br` de dispatch. Meta: fallback < 1%.
- [x] 1.8 🧠 `patches.py` vazio, com o mecanismo pronto (patch que confere a palavra original).

## Critério de saída (M1)
`make gen && make` produz `pvgame.dll` sem erros; `test_lift.py` e `test_simd.py` verdes; relatório com
nº de funções, % fallback, nº de `rt_udf` (cada um justificado).

## Riscos
- Compilação: milhões de linhas C. Mitigação: `-O1`, chunks equilibrados (o LAS já faz), ccache, compilar em lotes.
- Código gerado por compilador diferente (Game Freak usa o mesmo clang do SDK, então padrões parecidos com o LAS).
