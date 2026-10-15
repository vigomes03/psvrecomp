# Pokemon Decompile — PSV Recomp (PVRecomp)

Recompilação estática do Pokémon Violet (v1.0.0 e update v4.0.0, cartucho e console do [USER]), seguindo o processo do
LAS Recomp (Link's Awakening Switch). O aplicativo se chama **PSV Recomp** (título da janela, `psvrecomp.log`,
`psvrecomp.ini`); o binário de desenvolvimento é `pvhost.exe` + `pvgame.dll`.
Roadmap: [../docs/roadmap/README.md](../docs/roadmap/README.md). Regras: [../CLAUDE.md](../CLAUDE.md).
**Uso local, nada sai desta máquina.**

## O que é (recomp, não emulador de CPU)
- **CPU:** todo o código ARM64 do jogo (`main`, `subsdk*`, `sdk`) foi traduzido **uma vez, antes de rodar**, para C e
  compilado para x86-64 (`pvgame.dll`, ~271 mil funções). Não há interpretador nem JIT de ARM em tempo de execução.
- **Sistema (Horizon OS):** reimplementado em C (HLE): kernel/SVCs, IPC, serviços (`fs`, `hid`, `audren`...).
- **GPU:** as chamadas NVN do jogo são reimplementadas sobre Vulkan; os shaders Maxwell do jogo são traduzidos para
  GLSL/SPIR-V **em tempo de execução** (`runtime/nvn/maxwell/translate.c`), como um emulador faz com a GPU.

## Pastas
| Pasta | Conteúdo |
|---|---|
| `recomp/` | recompilador ARM64 → C (fork do LAS `tools/`: nso, analyze, lifter, simd_c, gen, layout, sym), testes diferenciais, `build_host.sh` (runtime), lançador `run_window.cmd` |
| `runtime/` | runtime nativo: loader, kernel, IPC, serviços, `hle/` (input, nvn_boot...), `nvn/` (camada NVN), `nvn/vulkan/` (backend), `nvn/maxwell/` (tradutor de shaders), `platform/`, `ui/` |
| `third_party/` | `LICENSE-LASRecomp.txt` (MIT, Copyright (c) 2026 Peiikai), `smaa/` (SMAA, MIT, Jorge Jimenez et al.) |

Origem: `LASRecomp-main` (github.com/peiikai/LASRecomp, 14/10/2026). O que era do Zelda foi removido ou virou stub
neutro (`runtime/pv_zelda_stubs.c`). Mudanças do recompilador em relação ao original: `patches.py` vazio, caminho do
harness em `test_simd.py`, assinatura de `fnprof_hit` em `test_simd_harness.c`. O histórico de cada mudança do runtime
está em `../docs/pipeline-log.md`.

## Rodar
```bash
# build do runtime (Vulkan) -> D:/Dev/REA/lab/host-vk/pvhost.exe
cd "Pokemon Decompile/recomp" && bash build_host.sh /d/Dev/REA/lab/host-vk vulkan
# prova de build/boot (única prova aceita, ver CLAUDE.md)
python tools/verify/gates.py run host --version v400
```
- **Jogar à mão:** dois cliques em `recomp/run_window.cmd` (sem limite de tempo, abre no monitor 2; teclado WASD/setas,
  K ou Espaço = A, J = B, I = X, L = Y, ou controle Xbox/PS/Switch Pro). Log em `lab/host-vk/window.log`.
- **Pipeline (Claude):** `bash tools/verify/run_auto.sh <segundos> <nome> [VAR=valor ...]` — entrada automática,
  log `lab/host-vk/<nome>.log`, frames com `LARECOMP_SCREENSHOT_EVERY/FROM`.

## Ferramentas de diagnóstico (variáveis de ambiente, todas desligadas por padrão)
| Variável | O que faz |
|---|---|
| `LARECOMP_DEBUG_FRAME=<n>` / `PVR_DEBUG_ON=<w>x<h>/<fmt>` / `PVR_DEBUG_ON_COPY=<w>x<h>` | lista todos os draws de um frame (por número, ou disparado quando a cena usa tal textura/cópia) e salva cada passe |
| `PVR_DIAG_SAVETEX=<w>` + `PVR_DIAG_SAVETEX_FS=<fs>` | salva as texturas lidas pelos draws de um shader |
| `PVR_DBG_FS=<fs,...>` `PVR_DBG_PC` `PVR_DBG_REG` `PVR_DBG_RT` (+`SIGNED/FRACT/UINT`) | pinta a saída de shaders de branco ou mostra um registrador |
| `PVR_DBG_SREF=<de>:<para>` `PVR_DBG_CBFILL=<k>:<word>` `PVR_WATCH=<addr>` | troca referência de stencil / preenche um cbuf / vigia quem escreve num endereço |
| `PVR_LOG_COPIES` `PVR_SAVE_COPY=<w>x<h>` `PVR_LOG_TEXADDR=<addr>` | cópias de textura/buffer, origem salva, texturas num endereço |
| `PVR_NO_BRA_CC` `PVR_NO_COPY_WRITEBACK` `PVR_NO_QUADSWAP` `PVR_NO_STENCIL_VIEW` | A/B: desliga uma correção para comparar |
| `PVR_NVN_MISSING` `PVR_DIAG_UNKNOWN` `PVR_DUMP_THREADS` `PVR_SYM_AT` | funções NVN faltantes, instruções Maxwell desconhecidas, threads, símbolos |

Detalhe de uso e armadilhas: skill `switch-static-recompilation` (referência `vulkan-backend.md`).

## Testes (sem precisar do jogo)
```bash
cd "Pokemon Decompile/recomp"
export PATH="/d/msys64/ucrt64/bin:$PATH"   # clang (só neste comando)
venv/Scripts/python.exe test_simd.py --encodings 400 --cases 30 --seed 1 --jobs 8
python ../../tools/verify/test_glsl_slice.py
```
