# Fase 6: Jogável

**Objetivo:** do jogo novo até explorar Paldea com estabilidade e desempenho medidos.

**No Zelda:** ciclo `shot.sh <frame>` com input roteirizado (`LARECOMP_INPUT`), warp direto para fases, save em pasta
temporária, screenshots comparados; correção bug a bug, com comentário explicando o porquê.

## Tarefas
- [ ] 6.1 🧠 Roteiros de teste (`PVR_INPUT`): título → jogo novo → primeira cutscene → controle do personagem.
- [ ] 6.2 🤖 Rodar roteiros em lote, coletar screenshots/logs, **triagem** automática (crash? tela preta? FPS?).
  Saída: `work/notes/triagem-<data>.md` para o Claude priorizar.
- [ ] 6.3 🧠 Cada bug: causa raiz (skill `systematic-debugging`) → cartão de correção 🤖 ou correção 🧠 se for no núcleo.
- [ ] 6.4 🤖 Desempenho: `fnprof` (funções quentes), FPS por área, uso de CPU por thread. O jogo original roda a
  ~30 FPS com quedas; meta inicial: 30 FPS estáveis, depois desbloquear (fase 8).
- [ ] 6.5 🧠 Estabilidade: 10 min de exploração sem crash (roteiro + aleatório).

- [ ] 6.6 🟢 **Desempenho (urgente) — 30 fps atingido 15/10 (run_auto, sem gate):** 5-10 fps em interior, ≈3 fps em área aberta, CPU ~9 %, GPU ociosa. O log mostra
  ~60 mil flushes CPU↔GPU por rodada (cada lista de comandos enviada e esperada uma a uma). Meta: 30 fps em interior.
- [ ] 6.7 🟢 Crash da 1ª batalha (ver fase 1, item 1.7): corrigido, provado por run_auto (4365 frames) e pelo [USER]; sem gate.
- [ ] 6.8 🧠 **Fluidez:** medição por frame (1% low, causa dos picos) → shaders pré-compilados → rastreio de escrita de
  texturas → menos sincronia CPU↔GPU → ritmo de apresentação pelo monitor. Testes sempre a 30 fps.
- [ ] 6.9 60 fps (`PVR_GAME60`): opção no menu/ini, endereço por versão, teste longo de sincronia.

## Estado em 15/10 (revisão com o [USER])
- 🟢 **M5 atingido e M6 parcial** no teste manual: intro e começo da história, mais de 10 min sem crash, save ok.
  Bugs visuais pequenos (nota 95/100): skybox com linhas, iluminação, objetos sem render. O [USER] indica os lugares e
  cria saves para a busca.

## Critério de saída (M5 → M6)
M5: jogo novo até controlar o personagem. M6: 10 min no mundo aberto sem crash, FPS registrado em `docs/`.
