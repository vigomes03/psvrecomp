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

## Critério de saída (M3 → M4)
M3: screenshot automático no frame N mostra o logo. M4: tela de título correta comparada com o Eden (diferença
visual pequena medida por script).

## Riscos
- Volume de shaders e variações: compilação na hora = travadas. Mitigar com cache e pré-compilação.
- Diferenças de precisão/ordem de blend entre Maxwell e o Vulkan no PC: artefatos (o LAS ainda tem bugs de luz).
