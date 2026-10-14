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

## Critério de saída (M5 → M6)
M5: jogo novo até controlar o personagem. M6: 10 min no mundo aberto sem crash, FPS registrado em `docs/`.
