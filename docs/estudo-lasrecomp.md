# Estudo do LAS Recomp: como foi feito

> Análise feita **lendo o código** (sem o REA), em 14/10/2026, sobre o zip `LASRecomp-main`
> (= `github.com/peiikai/LASRecomp`, 2 commits antes do HEAD). Tudo o que está marcado como ✅ foi
> executado nesta máquina; o resto vem da leitura do código e dos comentários.

---

## 1. O que é, em uma frase

Uma **recompilação estática** do *Zelda: Link's Awakening* (Switch, 2019): o código de máquina **ARM64**
do jogo é traduzido **uma vez, offline**, para **C**, e esse C é compilado para x86-64 (ou ARM64) e linkado
com um **runtime** que imita o sistema operacional do Switch (Horizon) e a API gráfica (NVN → Vulkan/Metal).
**Não é emulador:** não há interpretador nem JIT. As funções do jogo viram funções C nativas.

Tamanho: cerca de **51 mil linhas próprias** (runtime em C/ObjC/C++ e ferramentas em Python), mais o randomizador
de terceiros (LAS-Randomizer) com cerca de 8 mil linhas de adaptação.

| Área | Linhas | O quê |
|---|---:|---|
| `tools/` recompilador (`nso`, `analyze`, `lifter`, `simd_c`, `gen`, `patches`) | ~3.250 | ARM64 → C |
| `runtime/nvn/` | ~14.500 | API gráfica NVN + tradutor de shaders Maxwell + Vulkan/Metal |
| `runtime/ui/` | ~6.400 | tela inicial, menu overlay (ImGui), tracker, editor de save |
| `runtime/hle/` | ~6.000 | substituições de funções do jogo/SDK e features novas |
| `runtime/services/` + `kernel.c` + `ipc.c` + `loader.c` | ~3.800 | "Horizon OS" falso |
| `tools/rando/` | ~8.000 | randomizador (entradas, salas, pots/bushes/digs, lojas...) |

---

## 2. Arquitetura

```
 OFFLINE (no PC de quem joga, na primeira execução)               EM TEMPO DE EXECUÇÃO
 ────────────────────────────────────────────────                ─────────────────────────────────────────
 extracted/exefs/main, sdk (NSO, ARM64)                           lasrecomp.exe  (runtime, sem código do jogo)
        │ tools/nso.py   (LZ4, segmentos, MOD0, dynsym, relocs)        │ carrega lasgame.dll (código do jogo)
        ▼                                                              ▼
 tools/gen.py  ──►  descobre funções  ──►  tools/lifter.py       loader.c  → mapeia NSO em 0x70_0000_0000,
   (eh_frame, símbolos, relocs, alvos de BL, ADR/ADRP+ADD,        aplica relocs, liga imports a stubs HLE
    ponto fixo dividindo funções)            │ 1 instrução → C    kernel.c  → SVCs (threads, mutex, eventos, memória)
   jump tables resolvidas EMULANDO           │ FP/SIMD: asm (ARM)  ipc.c + services/ → sm:, fsp-srv, hid, audren, time...
   o trecho com Unicorn                      │   ou C portátil     hle/      → funções do SDK/jogo trocadas por C
        ▼                                     (simd_c.py)          nvn/      → NVN → Vulkan (Win/Linux) | Metal (mac)
 generated/main/*.c, sdk/*.c  (~1.500 funções/arquivo)                         shaders Maxwell → GLSL/MSL → SPIR-V
        │ clang -O1 (dev)  |  zig cc (jogador)                     ui/       → ImGui: start screen, menu F1, tracker
        ▼                                                         rando     → seed escolhe instruções/arquivos
 lasgame.dll  (+ lasgame.dll.id = hash do gerador+flags)
```

### Fluxo de boot (`runtime/main.c`)
`plat_init` → tela inicial (`launcher_run`) → `boot()`: `gamelib_load` (DLL do jogo) → `loader_load(exefs)`
→ `rando_boot` (patches da seed) → `kernel_init` → `dispatch_init` → lê `main.npdm` (prioridade/stack) →
chama o `nn::init::Start` do jogo numa thread "guest". `ui_run()` fica com a janela e o input na thread
principal; trocar de seed ou voltar ao título faz **reboot in-place** (`RT_ON_RESET` limpa o estado).

---

## 3. O recompilador (`tools/`) passo a passo

1. **`nso.py`**: lê o NSO (formato executável do Switch): descompacta LZ4, monta a imagem
   (`.text/.rodata/.data/.bss`), lê `MOD0`, a tabela dinâmica, os símbolos (`dynsym`) e as relocações.
2. **Descoberta de funções** (`gen.py: boundaries` + `main`):
   - `.eh_frame_hdr` (tabela de unwind do C++ = início de quase toda função);
   - símbolos `STT_FUNC`, alvos de `R_AARCH64_RELATIVE` (vtables e ponteiros);
   - todo alvo de `BL`, endereços materializados com `ADR` / `ADRP+ADD` (callbacks);
   - **ponto fixo**: qualquer branch para fora da própria função vira novo início e divide a função,
     até não aparecer mais nada.
3. **Lifter** (`lifter.py`): decodifica **cada palavra de 32 bits à mão** (sem Capstone no caminho
   crítico), instrução por instrução, e gera C sobre `struct Cpu` (`x[31]`, `sp`, `nzcv`, `v[32]`...).
   Flags são calculadas só nas instruções que as setam (`adds64`, `subs64`...). LDXR/STXR viram
   compare-and-swap. Instrução não suportada vira `rt_udf()` (falha alta, não silenciosa).
4. **FP/SIMD**: duas estratégias.
   - Em host ARM64 (Mac M1+), as instruções são **re-emitidas como asm inline**, em lotes de até 24,
     carregando/salvando os registradores V do `Cpu`. Fica bit-exato por construção.
   - Em x86 (Windows/Linux), `simd_c.py` + `runtime/simd.h`: cada encoding vira chamada de helper
     `static inline` com constantes, e o clang dobra os `switch`. Exige AVX2/FMA (`-march=x86-64-v3`).
5. **Jump tables** (`br xN`): em vez de heurística, **emulam com Unicorn** o trecho entre o `cmp` e o `br`
   para cada índice possível e coletam os destinos. O que não resolvem vira o fallback "todas as
   instruções da função são labels" + `switch(pc)`. Assim um caso esquecido ainda acerta.
6. **Emissão** (`emit_function`): cada função vira `void f_<addr>(Cpu *c)`. Branch interno = `goto L_x`;
   chamada direta = chamada C; tail-call/indireto = `__attribute__((musttail)) return rt_dispatch(c)`.
   O `musttail` impede o stack do host de crescer em cadeias de saltos.
7. **Saída**: chunks de cerca de 1.500 funções ou 1,5 MB de C (função gigante ganha arquivo próprio, para
   compilar em paralelo) + `main_table.c` (endereço → ponteiro). `write_if_changed` faz o `make` só
   recompilar o que mudou.

### Despacho em runtime (`dispatch.c`)
Cache direto-mapeado de 4096 entradas por thread na frente de uma busca binária nas tabelas.
Endereços falsos `HLE_BASE + 16*i` apontam para funções em C do host. `hle_override` troca qualquer
função do jogo por endereço.

---

## 4. Decisões de projeto (e por quê)

| Decisão | Por quê / efeito |
|---|---|
| **Endereço do guest = endereço do host** (janela fixa `0x70_0000_0000..0x73_2000_0000`) | Load/store vira `*(uint32_t*)addr`, sem tradução. No Windows, `VirtualAlloc` reserva e um *vectored exception handler* faz commit sob demanda. |
| **Recompilar no PC do jogador** (gerador Python empacotado com PyInstaller + `zig cc`) | O release **não contém código da Nintendo**; cada um gera o próprio a partir do próprio dump. Questão legal resolvida por arquitetura. |
| `GAMELIB_ID` = hash do gerador + headers + flags | DLL antiga nunca é carregada com runtime novo: é recompilada. |
| **HLE por nome de símbolo** (`HLE_FUNC("_ZN2nn3hid12GetNpad...", fn)`) registrado via **seções do linker** | O SDK (`nn::`) vem com símbolos. Basta escrever a função C e ela "aparece" sozinha, sem tabela central, nos 3 SOs (Mach-O/ELF/PE com `.hle$a/m/z`). |
| Toda a API **NVN** (495 funções) interceptada por nome via `nvnBootstrapLoader` | Não emulam a GPU Maxwell em nível de registrador; reimplementam a API em cima de Vulkan/Metal. |
| Command buffers gravados **na memória do próprio jogo** | O gerenciamento de memória e os callbacks de "sem memória" do jogo continuam funcionando como foram projetados. |
| Shaders: **binário Maxwell (SASS) → MSL**, e GLSL por reescrita de tokens do MSL | Um tradutor só; GLSL compilado com shaderc. Branches viram máquina de estados `switch(pc)` com pilhas SSY/PBK. |
| **`patches.py`**: patch por instrução que **confere a palavra original** (`assert w == 0xbd457369`) | Endereço errado ou versão errada do jogo falha na geração, não vira bug silencioso. Usado em widescreen, FOV, culling, warp. |
| **Randomizer no código**: `patch_variants.json`, onde a seed escolhe a instrução em runtime (`rando_word`) | Uma DLL serve para todas as seeds; troca de seed sem recompilar nem reiniciar. |
| `RT_ON_RESET` (também por seção do linker) | Reboot in-place: cada módulo declara o que zerar. |
| `-O1` no código gerado | Milhões de linhas C; `-O2` custaria muito tempo de compilação para pouco ganho. |
| Comentários dizem **por quê** (endereço, o que o jogo faz, qual seed/bug mostrou o problema) | O código é a documentação da engenharia reversa. Ex.: `doorjump.c` explica a struct `PlayerCollision`, a vtable e o offset. |

---

## 5. Como fizeram a engenharia reversa (sem Ghidra no repositório)

Não há projeto de Ghidra/IDA no repo. A RE foi feita **instrumentando o próprio jogo recompilado**:

- **Símbolos do SDK** (`nn::...` mangled) + `tools/sym.py` (endereço → símbolo + disassembly com Capstone + `c++filt`).
- **`LARECOMP_FNPROF=<de>:<até>`**: cada função gerada chama `FN_ENTER`. Contam as entradas entre dois
  frames e **comparam duas execuções** para ver quais funções do jogo uma ação ativa.
- **`LARECOMP_ADDF_MATCH`**: "cutuca" todo float/double da memória do jogo perto de um valor e vê o que
  move o Link, para achar a posição real numa **bisseção de memória** (é assim que achou o `PlayerCollision+0x80`).
- **248 variáveis `LARECOMP_*`** como ganchos de debug: input roteirizado, warp para fase X, seed, save em pasta
  temporária, screenshot no frame N, trace de device-lost do Vulkan, log de draws por frame...
- Hooks de `str` via `patches.py` para **descobrir onde um objeto vive** (ex.: o objeto de "level jump request").

## 6. Fluxo de trabalho (como desenvolveram)

- **Feito quase todo por IA**: o README diz que o código, as ferramentas, a RE e a documentação foram escritos pelo
  **Claude (Claude Code)**, "dirigido, testado e revisado por um humano".
- O histórico público é **achatado**: 12 commits, o primeiro sendo "LARecomp Beta 3". O planejamento ficava em
  `notes/PLAN.md` (citado num comentário, **não publicado**).
- **Testes diferenciais contra um oráculo** (o ponto mais forte do projeto):
  - `test_lift.py`: instrução por instrução, C gerado vs Unicorn, com valores-limite;
  - `test_simd.py`: enumera **todo** o espaço de encodings FP/SIMD, compara validade e resultados com Unicorn
    (NaN, ±0, denormais, modos de arredondamento);
  - `test_translate.sh`: fuzz do tradutor de shaders: MSL byte-idêntico a um tradutor de referência, GLSL compila
    (shaderc) e valida (SPIRV-Tools);
  - `test_vk_pipelines.sh`, `test_astc.sh`: pipelines Vulkan reais, decodificador ASTC vs referência.
- **Validação visual automatizada**: `shot.sh <frame>` roda o jogo com input roteirizado e salva PNG;
  `montage.sh`, `frames.sh`, `transients.py` (pisca-pisca entre frames), `bandmetric.py` (banding),
  `passes.py` (agrupa draws por shader/render target).
- **Testes de jogo**: `doorjump_test.sh <seed>` percorre toda porta incompatível do dungeon shuffle;
  geram várias seeds e conferem que todos os locais são alcançáveis.
- **Performance**: `perf_sweep.py`, `fnprof`, `sampletree.py` (árvore do `sample` do macOS).
- Regras (`CONTRIBUTING.md`): **nenhum arquivo da Nintendo** no repo; "um fix só está verificado quando você viu
  funcionar"; mudar Metal exige o par no Vulkan; seed IDs antigos precisam continuar carregando.

---

## 7. Ferramentas usadas (e o que eu instalei aqui)

| Ferramenta | Papel | Aqui |
|---|---|---|
| **Python 3.12** + `capstone` 5.0.9, `unicorn` 2.1.4, `lz4` 4.4.5 | recompilador / testes diferenciais | ✅ `tools/venv` (uv, CPython 3.12.13) |
| LAS-Randomizer: `oead`, `evfl`, `keystone-engine`, `quicktex`, Pillow, PyYAML | gerar seeds | ✅ `third_party/LAS-Randomizer/venv` |
| **MSYS2 UCRT64**: clang 23, lld, make, SDL3, FFmpeg, Vulkan headers/loader/validation, shaderc, SPIRV-Tools, VMA, gdb, nasm | compilar o runtime | ✅ **`D:\msys64`** (o script oficial usa `C:\msys64`) |
| **Zig 0.17.0** (`zig cc`) | compilar o código do jogo no PC do jogador | ✅ `build/zig` (hash conferido) |
| Dear ImGui, VMA, SMAA, FSR1 | UI e pós-processamento | já vêm em `third_party/` |
| PyInstaller | empacotar gerador e randomizador | não instalado (só para release) |

### O que verifiquei ✅
- `make build/lasrecomp.exe` → **compila** (12 MB) com clang 23.
- O app **abre** com Vulkan na RTX 3070 Ti e mostra a tela "Game Files" (pede o dump v1.0.0).
- `test_simd.py`: **1.048.640 encodings** com validade idêntica à do Unicorn; **12.000 casos** executados, **0 falhas**.

### Problemas encontrados no projeto (não são do ambiente)
1. **Makefile**: `all: $(EXE) $(if $(GEN_SRC),$(GAMELIB))`. Sem `generated/`, `GEN_SRC` vale `" "`
   (dois `wildcard` vazios + espaço), e o GNU make considera isso verdadeiro. Ele tenta linkar uma `lasgame.dll`
   vazia e falha. **Contorno:** `make build/lasrecomp.exe` (ou `$(strip $(GEN_SRC))` no Makefile).
2. **`tools/test_simd_harness.c`** está desatualizado: declara `fnprof_hit(uint64_t)`, mas o `cpu.h` mudou para
   3 argumentos. Rodei numa cópia corrigida, fora do repositório.
3. **`test_translate.sh`** depende do commit `652e234`, que **não existe no histórico público** (achatado).
4. A doc avisa: **não rode a janela sob `timeout` do MSYS**, porque trava. Use Python/PowerShell para testes de janela.

### Como compilar aqui
```bash
export PATH="/d/msys64/ucrt64/bin:/d/msys64/usr/bin:$PATH"
cd /d/Dev/REA/ref/LASRecomp-main/LASRecomp-main
make -j12 build/lasrecomp.exe          # runtime/app (sem jogo)
# com o seu dump em extracted/:  make gen && make -j12   → generated/ + build/lasgame.dll
# rodar: PATH com D:\msys64\ucrt64\bin (DLLs)  →  build\lasrecomp.exe
```
Cópia com histórico git: `D:\Dev\REA\ref\LASRecomp-git` (LF, `autocrlf=false`).

---

## 8. Se fôssemos fazer algo parecido: lições

1. **Escolha um alvo com metadados**: `.eh_frame` + símbolos do SDK foram o que tornou a descoberta de funções e
   o HLE viáveis. Binário sem símbolos multiplica o trabalho.
2. **Recompilação estática é viável quando o código é fixo** (sem JIT, sem código automodificável). A
   dificuldade real fica em: jump tables (resolvidas emulando), chamadas indiretas (dispatch com cache) e FP/SIMD.
3. **Oráculo primeiro**: antes de escrever o lifter, ter Unicorn como referência e testes diferenciais.
   Eles garantem que a IA não "acha" que acertou.
4. **Reimplementar a API, não o hardware**: HLE da NVN e dos serviços em vez de emular a GPU/kernel.
5. **Patches que se auto-verificam** (conferir a palavra original) e **ganchos de debug por variável de
   ambiente** desde o dia 1; screenshot automático para validar visualmente.
6. **Legal por arquitetura**: distribuir só o gerador; o código do jogo nasce na máquina de quem tem o jogo.
7. **Com o nosso setup** (Claude orquestrando + qwen local + REA): o REA/Ghidra entra na fase de **entender o
   binário** (achar funções, structs, quem chama o quê), que aqui foi feita com `fnprof`/`ADDF_MATCH`/`sym.py`.
   O qwen local serve para cartões fechados e verificáveis (testes, tabelas, triagem de logs de draws). Lifter,
   tradutor de shaders e decisões de arquitetura ficam com o Claude, sempre com testes diferenciais como contrato.
