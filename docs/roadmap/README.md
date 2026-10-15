# Roadmap: Pokémon Violet Recomp (PVRecomp)

> **Meta:** fazer com o Pokémon Violet o que o LAS Recomp fez com o Zelda: **recompilação estática** do código
> ARM64 do jogo para C, com um runtime nativo (Horizon OS falso + NVN→Vulkan), virando um **aplicativo Windows
> que roda o jogo** a partir do nosso dump. Depois disso, entender o jogo por dentro e adicionar recursos.
>
> **Escopo:** estudo pessoal, **100% local**. Nada sai desta máquina: sem remote, sem upload, sem release.

Base técnica: [estudo-lasrecomp.md](../estudo-lasrecomp.md) (como o Zelda foi feito). Regras de trabalho: [CLAUDE.md](../../CLAUDE.md)
(Claude orquestra, qwen executa, tudo verificado).

## Fases

| # | Fase | Saída (marco verificável) | Equivalente no LAS Recomp | Status |
|---|---|---|---|---|
| 0 | [Aquisição e reconhecimento](fase-0-aquisicao.md) | dump extraído (base + update), inventário do executável, decisão de "vale/não vale" | dump do usuário + `nso.py`/`analyze.py` | ✅ base + v4.0.0 extraídos e verificados (gate dumps run_id=131ff828b2) |
| 1 | [Recompilador](fase-1-recompilador.md) | todo o `main` vira C que **compila**; testes diferenciais verdes | `tools/gen.py`, `lifter.py`, `simd_c.py` | ✅ **M1** (pvgame.dll com 271k funções, linkada no boot run_id=990a33212b); **1.7 reaberto com prioridade**: função ausente em `7000cedb00` derruba a 1ª batalha |
| 2 | [Runtime mínimo / boot headless](fase-2-runtime-boot.md) | o jogo roda `nn::init::Start` → `nnMain` e chega ao loop principal **sem gráficos** | `loader.c`, `kernel.c`, `dispatch.c`, `ipc.c`, `services/` | ✅ **M2** nas duas versões (v400 run_id=7adc0390c2, base run_id=db35401e31) |
| 3 | [Sistema de arquivos e dados](fase-3-arquivos.md) | o jogo lê o romfs (base + patch) e os arquivos `trpfs` sozinho | `services/fs.c`, `romfs_build.c` | 🟢 na prática: o jogo carrega tudo do romfs; **save persistente** (fecha, reabre e carrega) — teste manual do [USER], 15/10 |
| 4 | [Gráficos: NVN → Vulkan](fase-4-graficos.md) | **primeiro frame**: logo / tela de título renderizada | `runtime/nvn/*`, `maxwell/translate.c`, `vulkan/` | 🟢 **M3/M4** atingidos no teste manual (nota 95/100); faltam artefatos de iluminação, skybox com linhas, objetos não renderizados, gate `window` |
| 5 | [Áudio, input, save, tempo](fase-5-sistemas.md) | controle funciona, som toca, save grava/carrega | `services/audio.c`, `hle/input.c`, `fs.c` (save) | 🟡 input e save ok; **áudio: silêncio total**; **teclado do nome (swkbd) ausente** |
| 6 | [Jogável](fase-6-jogavel.md) | começar um jogo novo e andar pelo mapa aberto | ciclo shot.sh + correções | 🟡 **M5** e **M6 parcial** no teste manual (intro e começo da história, >10 min sem crash); bloqueios: **crash na 1ª batalha**, **5-10 fps (≈3 fps em área aberta)** |
| 7 | [Ferramentas de RE e debug](fase-7-ferramentas-re.md) | (contínua) fnprof, ganchos `PVR_*`, screenshot automático, REA/Ghidra | `fnprof.c`, `LARECOMP_*`, `sym.py`, `shot.sh` | 🟢 contínua: kit `PVR_*`, `glsl_slice.py`, `run_auto.sh`, gates; **falta log/aviso de crash** |
| 8 | [O aplicativo](fase-8-aplicativo.md) | launcher, menu overlay, resolução/FPS desbloqueados, recursos nossos | `ui/launcher.mm`, `menu.mm`, `hle/widescreen.c` | 🟡 nome **PSV Recomp**, `psvrecomp.ini`, `run_window.cmd` |
| 9 | [Entender o jogo (estudo AAA)](fase-9-estudo-aaa.md) | documentação de motor, formatos, sistemas de jogo | (não existe no LAS: é o nosso objetivo de estudo) | ⬜ contínua |

Ordem real: **0 → 1 → 2 → 3 → 4 → 5 → 6 → 8**, com **7 e 9 correndo em paralelo** desde a fase 1.

## Estado e próximos passos (revisão com o [USER], 15/10/2026)

**Alvo principal: v4.0.0** (com o update). A v1.0.0 segue só como build de comparação.

Marcos: M0-M2 provados por gate. **M3, M4, M5** atingidos e **M6 parcial** pelo teste manual do [USER] (15/10): do
logo até o começo da história, mais de 10 min sem crash, save persistente; o gate automático `window` fica como item
próprio para formalizá-los.

Ordem de trabalho:
1. 🧠 **Crash da 1ª batalha** (1.7): `FATAL: no function at 7000cedb00 (lr=7000cedadc)` — salto indireto para um
   endereço que o recompilador não reconheceu como função. Repro: carregar o save do [USER] → A na batalha.
   Log: `lab/host-vk/crash_batalha_20261015.log`.
2. 🧠 **Desempenho (6.6), com urgência logo depois:** 5-10 fps em interior, ≈3 fps em área aberta, CPU ~9 % e GPU
   ociosa = gargalo de sincronização (~60 mil flushes CPU↔GPU por rodada). Meta: 30 fps em interior.
3. 🧠 **Log e aviso de crash (7.x):** caixa de erro com a mensagem e o log salvo sozinho; hoje o jogo só fecha.
4. **Visual:** skybox com linhas, artefatos de iluminação, objetos sem render. O [USER] indica o lugar e cria saves.
5. **Áudio (5.1):** hoje silêncio total.
6. **Teclado do nome (5.6, swkbd):** hoje o jogo usa um nome padrão (`?瑱?` na ficha).
7. **Gate `window`:** screenshot automático no frame N para formalizar M3-M5.

## Marcos

| Marco | Critério objetivo |
|---|---|
| M0 Dump pronto | `dumps/base/exefs/main` e `dumps/update/exefs/main` existem; build ids anotados; romfs listado |
| M1 "Compila" | `generated/main/*.c` + `sdk` compilam e linkam numa DLL; 0 `rt_udf` por instrução não suportada (ou lista justificada) |
| M2 "Respira" | log mostra o jogo criando threads, abrindo serviços e entrando no loop de frames (headless) |
| M3 "Primeiro pixel" | screenshot automático mostra o logo da Game Freak / The Pokémon Company |
| M4 "Título" | tela de título com música, e o controle navega no menu |
| M5 "Jogo novo" | cria personagem, cutscene inicial, controla o personagem |
| M6 "Mundo aberto" | anda por Paldea 10 min sem crash; FPS medido |
| M7 "App" | launcher próprio, configurações, recursos extras |

## Diferenças em relação ao Zelda (riscos principais)

| Tema | Zelda LA (2019) | Pokémon Violet (2022) | Impacto |
|---|---|---|---|
| Tamanho do código | médio | ❓ provavelmente **várias vezes maior** (mundo aberto, motor maior) | tempo de geração e compilação; 32 GB de RAM pode apertar ao compilar |
| Símbolos | SDK com símbolos `nn::` | ❓ verificar na fase 0 (`.dynsym`, `.eh_frame`) | sem símbolos = mais RE manual |
| Módulos | `main` + `sdk` | ❓ pode ter `subsdk*` (middleware) | o gerador precisa de N módulos |
| Gráficos | NVN, cenas pequenas | NVN, mundo aberto, muitos shaders, ❓ compute/tessellation | mais trabalho no tradutor de shaders e no backend |
| Formatos de dados | BFRES/BNTX/SARC (Nintendo) | ❓ formatos próprios da Game Freak (`trpfs`, FlatBuffers `tr*`) | o **jogo** lê os dados; só precisamos de parser para estudo/mods |
| Threads | poucas | ❓ muitas (streaming de mundo) | sincronização (SVCs de arbitragem) precisa ser sólida |
| Online | nenhum | Union Circle, Tera Raid, Poké Portal | **stub**: serviços de rede respondem "offline" |
| Desempenho no Switch | bom | ruim (quedas de FPS) | nativo no PC deve ir melhor, mas depende do backend Vulkan |

## Estratégia (decisões tomadas)
1. **Partir de um fork local do LAS Recomp (MIT)** para o gerador e o runtime: lifter, SIMD em C, jump tables
   via Unicorn, kernel, IPC, NVN→Vulkan. Reescrever só o que for específico do Zelda (`hle/` de jogo, `patches.py`,
   randomizer, UI). Manter o aviso de copyright do MIT.
2. **Eden (GPL-3) é referência de leitura**: semântica de SVCs, serviços e o recompilador de shaders Maxwell.
   Entender e reimplementar; não colar código.
3. **REA/Ghidra** para entender o código do jogo (fase 7/9). O LAS fez RE instrumentando o jogo recompilado; nós
   temos as duas coisas.
4. **Oráculo sempre**: Unicorn para instruções; Eden rodando o mesmo dump como **referência de comportamento**
   (o que o jogo deveria ver/fazer) quando o recompilado divergir.
5. **Divisão de trabalho**: Claude projeta e verifica; qwen executa cartões. Cada fase lista o que é cartão de worker.

## Como acompanhar
- Cada fase tem a sua página com tarefas `[ ]` → `[x]`, quem executa (🤖 qwen / 🧠 Claude) e o critério de saída.
- Todo cartão vai para `docs/pipeline-log.md`. Achados vão para `docs/`, e nada do jogo é copiado para lá.
