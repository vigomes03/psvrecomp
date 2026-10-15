# Fase 4: Gráficos (NVN → Vulkan)

**Objetivo:** primeiro frame correto e depois o jogo inteiro renderizando em Vulkan na RTX 3070 Ti.
É a maior fase: no LAS são ~14.500 linhas (`runtime/nvn/`).

**No Zelda:** todas as funções NVN (495) interceptadas por nome via `nvnBootstrapLoader`/`nvnDeviceGetProcAddress`;
command buffers gravados na memória do jogo (`cmdbuf.c`); objetos (`objects.c`); texturas e formatos (`formats.c`,
`astc.c`, `texpatch.c`); **tradutor de shaders Maxwell SASS → MSL/GLSL** (`maxwell/translate.c`, ~2.100 linhas) +
shaderc; backend Vulkan (`vulkan/exec.c`, `device.c`, `textures.c`, `shaders.c`); escala de saída/SMAA/FSR1.

## Tarefas
- [ ] 4.1 🧠 Comparar a lista de funções NVN do Pokémon (fase 0) com as 495 do LAS → lista do que falta.
- [ ] 4.2 🤖 Um cartão por função NVN faltante simples (getters/setters/estado), com teste de gravação de comando.
- [ ] 4.3 🧠 Recursos que o Zelda não usa e o Pokémon talvez use: compute shaders, tessellation/geometry,
  queries, indirect draw, mais formatos de textura (BC1-7, ASTC variados), MSAA. Cada um vira subfase.
- [ ] 4.4 🧠 Tradutor de shaders: rodar **todos** os shaders do jogo pelo tradutor offline (dump dos shaders na
  primeira passada) → lista de instruções SASS não suportadas → cartões 🤖 por instrução, aceite = fuzz
  (`test_translate`) + validação SPIR-V (shaderc + SPIRV-Tools). Referência: `eden/src/shader_recompiler`.
- [ ] 4.5 🧠 **Cache de pipelines** em disco (um mundo aberto tem milhares de combinações).
- [ ] 4.6 🤖 Ferramentas de diagnóstico: `PVR_DEBUG_FRAME` (lista de draws por frame), `passes.py`, captura RenderDoc.
- [ ] 4.7 🧠 VRAM: 8 GB. Medir uso; streaming de texturas; liberar recursos órfãos.

## Estado em 15/10 (auditado pelo Claude)
- 🟡 Backend Vulkan do LAS portado (`nvn/vulkan`, `nvn/maxwell`, `astc`, `texpatch`, `output_scale`, SMAA, SDL3) e
  ligado em `build_host.sh <dir> vulkan`; o build headless (null) continua passando (gate host v400 run_id=d4b249f9a9).
- 🟡 Execução em janela: `recomp/run_window.cmd` (põe `D:\msys64\ucrt64\bin` no PATH: SDL3, shaderc, libstdc++).
  Rodada de 20 s em `lab/host-vk/window.log`: sem FATAL, 18 a 27 fps, ~10-13 mil draws por 2 s e **quase metade
  descartada** (`skipped`), o jogo chega a pedir o nome do jogador (swkbd headless). **Tela ainda preta.** Ainda não há
  gate para o modo janela: isto é observação de log, não marco.
- 🟡 4.1 feito na prática: com `PVR_NVN_MISSING=1`, o jogo pede **18** funções NVN que não temos
  (`lab/host-v400/nvnmiss.log`): 6 `Bind*Deferred`, `OverrideSubtileSize`, `ProgramGetSubtileSize`,
  `TextureBuilderGetViewOffset`, `SetZCullZF32CompressionEnable` e 8 de checkpoints/depuração.
- ❌ Descartado (FALSE): tudo o que os turnos do qwen produziram depois disso (stubs fora do build com tipos
  inventados, "nvnCommandBufferPresent", 33 cartões gerados em lote com numeração repetida, anúncio falso de fim das
  fases 4 e 5, arquivos C# e C escritos no repositório do Hospital). Arquivado em `lab/arquivo/fallback-qwen-20261015/`,
  afirmações registradas como falsas no placar (`gates.py score`).

- 🟡 **Primeiros pixels (15/10, 02:00):** a tela preta era o stub `widescreen_present_crop` do W11 (viewport de 1x1 px).
  Corrigido em `pv_zelda_stubs.c`; com `LARECOMP_SCREENSHOT_EVERY=150 LARECOMP_SCREENSHOT_FROM=150` saem frames reais em
  `lab/host-vk/build/frames/`: seleção de idioma (frame 150), escolha de avatar (450), brasão da Academia Uva (900).
  Faltam textos em algumas caixas (draws descartados). Ainda sem gate `window`: não é o M3 formal.

- 🟡 **Descartes −98% (15/10):** contador por motivo em `exec.c` (`skip why:` na linha `[vk]`) mostrou 98% `no_program`:
  o jogo faz `BindProgram(NULL, FRAGMENT)` para passes só de profundidade e o LAS guardava um único ponteiro de programa.
  Agora o bind é por estágio (`bind_program_stages`) e programa sem FS vira draw só de profundidade (FS vazio, sem
  escrita de cor). De ~13.200 para ~220 descartes por 2 s, draws executados 13 mil → 26 mil; host v400 run_id=87b55bc362.
  Restam ~165 por shader com instrução Maxwell desconhecida (4.4) e ~55 de compute.

- 🟡 **Tradutor (15/10):** TLD4S (W13), VMNMX (W14), VOTE (W15), ATOM global (W16) pelo qwen, revisados; LEA.LO e o
  cabeçalho dos blobs de compute (`0x12345679`, código em +0x100) pelo Claude. Compute 100% traduzido (dispatches 0 → todo
  frame). `PVR_DIAG_UNKNOWN=1` lista todas as instruções desconhecidas; `tools/verify/frame_stats.py` mede frames sem abrir.
- 🔴 **Causa provável da cena 3D preta:** os únicos draws que falham são 2 passes de tela cheia em 480x270 (¼ de 1080p) com
  `SUST`/`SURED` = histograma da exposição automática. Sem histograma, exposição 0: 3D preto, UI 2D ok. Desligar o teste
  de profundidade não muda nada (cutscene média 1,7 nas duas rodadas). Falta suporte a **storage images** inteiro:
  tradutor (`imageStore`/`imageAtomic*`) e backend (descritores `STORAGE_IMAGE`, `st.img` → textura pelo pool).

- 🟢 **Storage images (15/10):** infra do Claude + W17 SUST/SURED (qwen). 0 instruções desconhecidas, 0 draws descartados.
  O 3D passou a aparecer (geometria do personagem num quadro opaco e ampliado, conferido pelo [USER]).
- 🔴 **Causa do texto ausente (e suspeita para o 3D):** o VS de texto lê os glifos por `LDG` de `cb0[17]` + 64*instância,
  mas a janela de memória global dos shaders (`gmem`, import do heap) só cobre `HEAP_BASE..+0xd0000000`. O Pokémon põe
  **todos** os 1004 memory pools da GPU na região alias (VAMM do SDK 13): `0x7441c8f000..0x771116d000`, 828 MB em 2 grupos
  (~130 MB em 0x7441c-0x7449x, ~800 MB em 0x76c9c-0x76fb3). Leituras fora da janela devolvem 0: glifos de tamanho 0.
  Correção: várias janelas de memória (uma por grupo de pools, import host por janela, tabela base/tamanho num uniform)
  e o tradutor escolhendo a janela por endereço em LDG/STG/ATOM.

- 🟢 **Revisão com o [USER] (15/10):** M3/M4 atingidos no teste manual (do logo ao começo da história, nota 95/100).
  Corrigidos e registrados em `docs/pipeline-log.md`: listras diagonais (stencil), cabelo neon (BRA com flow test /
  `.CC`), foto do jogador na ficha (write-back de cópia). Restam: skybox com linhas, artefatos de iluminação, objetos sem
  render, gate `window`. Os "Próximos passos" antigos desta página (tela preta, 18 NVN faltantes) foram superados;
  a ordem atual está no [README](README.md#estado-e-próximos-passos-revisão-com-o-user-15102026).

## Critério de saída (M3 → M4)
M3: screenshot automático no frame N mostra o logo. M4: tela de título correta comparada com o Eden (diferença
visual pequena medida por script).

## Riscos
- Volume de shaders e variações: compilação na hora = travadas. Mitigar com cache e pré-compilação.
- Diferenças de precisão/ordem de blend entre Maxwell e o Vulkan no PC: artefatos (o LAS ainda tem bugs de luz).
