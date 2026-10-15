# Fase 1: Recompilador ARM64 → C

**Objetivo:** transformar `main` + `sdk` (+ `subsdk*`) em C que compila numa DLL, com semântica provada por
testes diferenciais.

**No Zelda:** `nso.py` → `gen.py` (descoberta de funções em ponto fixo, jump tables via Unicorn, emissão com `goto`
/ `musttail` / `rt_dispatch`) → `lifter.py` (inteiros/memória/controle) + `simd_c.py` (FP/SIMD em C portátil) →
chunks de ~1.500 funções → `clang -O1`. Testes: `test_lift.py`, `test_simd.py`.

## Tarefas
- [x] 1.1 🧠 (14/10, commit local; test_simd 74.950 casos 0 falhas) Criar `Pokemon Decompile/` como **fork local** de `LASRecomp-main/tools` + `runtime/cpu.h`, `simd*.h`
  (cabeçalho MIT preservado). Renomear `LARECOMP_*` → `PVR_*`, `lasgame` → `pvgame`.
- [x] 1.2 🧠 (14/10: `layout.py` + `pvgame.h`/`pvgame_entry.c`; o gen.py já gerava por módulo) Generalizar `gen.py` para **N módulos** (main, sdk, subsdk0..n) com bases de carga do npdm/rtld,
  tabelas de função por módulo e `dispatch` com N tabelas.
- [x] 1.3 🤖 (14/10: única família faltante era LDXP/LDAXP/STXP/STLXP de 64 bits, 15.832 ocorrências → W01/W02, 0 restantes) Cartões: cobrir as instruções que o censo da fase 0 apontou como não suportadas. Cada cartão =
  1 grupo de encodings + teste diferencial no Unicorn como critério de aceite.
- [ ] 1.4 🤖 Rodar `test_lift.py` sobre o `main` do Pokémon (amostras aleatórias de instruções reais) → 0 divergências.
- [ ] 1.5 🤖 `test_simd.py` completo (todos os encodings) → 0 divergências (já passou no LAS aqui: 12.000 casos).
- [x] 1.6 🧠 (14/10, ver medição abaixo) Escala: gerar 100% do `main`; medir tempo, tamanho do C e tempo de compilação. Se não couber:
  paralelizar o `gen.py` (multiprocessing por faixa de funções) e `make -j` com limite de RAM.
- [ ] 1.7 🤖 Relatório de jump tables: resolvidas / fallback "all labels" / `br` de dispatch. Meta: fallback < 1%.
- [x] 1.8 🧠 `patches.py` vazio, com o mecanismo pronto (patch que confere a palavra original).

## Estado em 15/10 (revisão com o [USER])
- 🔴 **1.7 virou prioridade 1:** a 1ª batalha fecha o jogo com `FATAL: no function at 7000cedb00 (lr=7000cedadc)`
  (`lab/host-vk/crash_batalha_20261015.log`): salto indireto para um endereço que o gerador não emitiu como função.
  Caminho: achar a origem do salto (tabela, ponteiro de função, vtable) e incluir o alvo na descoberta de funções.

## Critério de saída (M1)
`make gen && make` produz `pvgame.dll` sem erros; `test_lift.py` e `test_simd.py` verdes; relatório com
nº de funções, % fallback, nº de `rt_udf` (cada um justificado).

## Riscos
- Compilação: milhões de linhas C. Mitigação: `-O1`, chunks equilibrados (o LAS já faz), ccache, compilar em lotes.
- Código gerado por compilador diferente (Game Freak usa o mesmo clang do SDK, então padrões parecidos com o LAS).

## Medição 1.6 (14/10, `main` v1.0.0, `--simd c`) ✅

| Etapa | Resultado |
|---|---|
| Descoberta de funções | 172.175 inícios → **207.297 funções** em 16 rodadas de ponto fixo, **33 s** |
| Geração de C | **980 arquivos, 800 MB**, 41 s no total, **4,4 GB** de RAM de pico |
| Compilação (`clang -O1 -march=x86-64-v3`, 10 jobs) | **981 objetos, 0 erros, 152 s**, 269 MB de `.o` (RAM não medida) |
| Instruções não suportadas | 15.832 → **0** (W01/W02) |
| `rt_udf` no C | 51.247 palavras zero de alinhamento + 493 trap/dados no `.text`: esperado, só dispara se executado |
| Saltos indiretos | 107 jump tables resolvidas; **5.801 com fallback "todas as instruções"**; 19.660 `br` via dispatch |

Conclusão: escala **não é problema** na máquina (32 GB). Próximo foco da fase 1:
- **1.7**: 5.801 fallbacks é muito mais que o Zelda (correto, mas incha o código e é lento). Investigar o padrão das tabelas
  que o emulador de jump table não reconhece.
- `sdk` + `subsdk0` (N módulos, 1.2) e linkar uma `pvgame.dll` (M1).

## M1 "Compila" ✅ (14/10)
- Layout próprio (`recomp/layout.py`): `main` 0x7000000000 (68 MiB, não cabe nos 64 MiB do layout do Zelda), `subsdk0`
  0x7004400000, `sdk` 0x7004c00000; 90 MiB no total.
- `subsdk0`: 17.807 funções / 96 arquivos; `sdk`: 45.923 / 107; ambos compilam com 0 erros.
- **Interface jogo ↔ runtime**: os 271 mil símbolos gerados dependem só de `rt_dispatch`, `rt_svc`, `rt_brk`, `rt_udf`,
  `rt_ticks`, `fnprof_hit`, `g_fnprof` (+ `fegetround`/`fesetround`/`___chkstk_ms` da libc). Nenhuma referência pendente entre módulos.
- `recomp/link_m1.sh`: linka `pvgame.dll` (271 MB, lld < 1 s) contra um host de verificação (`m1_host.c`, runtime
  como armadilhas) e valida as tabelas: **271.027 funções nos 3 módulos, OK**.
- Pipeline completo do zero: gerar ~50 s + compilar ~3 min + linkar < 1 s.
