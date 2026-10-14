# Fase 8: O aplicativo

**Objetivo:** transformar o "jogo rodando" num aplicativo nosso, como o LAS Recomp é para o Zelda.

**No Zelda:** start screen (ImGui) com setup dos arquivos e build do código **na máquina do jogador**; menu
overlay F1; aspecto desbloqueado (patches de FOV/aspecto/culling); resolução interna, SMAA, FSR1; controles
remapeáveis; editor de save; tracker; randomizer.

## Tarefas
- [ ] 8.1 🤖 Launcher: escolher a pasta do dump (base + update), validar build ids, gerar/compilar o código (com
  barra de progresso, como o `gamebuild.c` do LAS), configurações.
- [ ] 8.2 🤖 Menu overlay (F1): resolução, FPS-alvo, vsync, escala, controles, áudio.
- [ ] 8.3 🧠 **Desbloqueio de FPS** (30 → 60+): achar o limitador de frame e o passo de tempo da simulação
  (fase 7) e corrigir a física/animação dependente de frame.
- [ ] 8.4 🧠 **Widescreen/ultrawide**: aspecto da câmera + culling + UI ancorada (técnica de `patches.py` do LAS).
- [ ] 8.5 🧠 Resolução interna e upscaler (FSR1 do LAS) + anti-aliasing.
- [ ] 8.6 🤖 Distância de desenho / LOD (o Switch corta muito no mundo aberto).
- [ ] 8.7 🤖 Ferramentas de estudo dentro do app: câmera livre, visualizador de stats de Pokémon na tela, warp.
- [ ] 8.8 💡 Ideias futuras (depois de M7): editor de save, randomizer próprio, mods de dados lidos do `trpfs`.

## Regra
Tudo **local**. Nada de empacotar para distribuição (`make dist` não é objetivo).
