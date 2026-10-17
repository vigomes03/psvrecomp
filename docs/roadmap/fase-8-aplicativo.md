# Fase 8: O aplicativo

**Objetivo:** transformar o "jogo rodando" num aplicativo nosso, como o LAS Recomp é para o Zelda.

**No Zelda:** start screen (ImGui) com setup dos arquivos e build do código **na máquina do jogador**; menu
overlay F1; aspecto desbloqueado (patches de FOV/aspecto/culling); resolução interna, SMAA, FSR1; controles
remapeáveis; editor de save; tracker; randomizer.

## Tarefas
- [ ] 8.1 🤖 Launcher: escolher a pasta do dump (base + update), validar build ids, gerar/compilar o código (com
  barra de progresso, como o `gamebuild.c` do LAS), configurações.
- [x] 8.2 🤖 Menu overlay (F1 / Esc; controle: Home ou Back+Start), em inglês como o LAS: abas Controls (layout),
  Video (tela cheia, monitor, VSync, FPS, resolução interna, upscaler, SMAA), Audio (volume), Quit. `runtime/ui/menu.cpp`
  (de `menu.mm`), `option_rows.cpp`/`osk.cpp` do LAS, Dear ImGui em `third_party/imgui`. Teste: `PVR_MENU_KEYS=<frame>:<tecla>,...`
  + `LARECOMP_WINDOW_SHOT`. FPS-alvo fica em 30 (decisão do [USER] 16/10). **Safe start:** se o processo morrer na
  abertura ou até 300 frames depois de mudar as opções, a abertura seguinte arquiva `psvrecomp.ini` como `.crashed` e usa defaults.
- [ ] 8.3 🧠 **Desbloqueio de FPS** (30 → 60+): experimento `PVR_GAME60=1` existe, mas está suspenso por decisão do [USER];
  não colocar no menu antes de ele pedir e de testar física/animação/cutscenes.
- [ ] 8.4 🧠 **Widescreen/ultrawide**: aspecto da câmera + culling + UI ancorada (técnica de `patches.py` do LAS).
- [ ] 8.5 🧠 Resolução interna, upscaler FSR1 e anti-aliasing SMAA do LAS: já expostos na aba Video; falta uma matriz
  de teste visual/performance por combinação para validar o recurso.
- [ ] 8.6 🤖 Distância de desenho / LOD (o Switch corta muito no mundo aberto).
- [ ] 8.7 🤖 Ferramentas de estudo dentro do app: câmera livre, visualizador de stats de Pokémon na tela, warp.
- [ ] 8.8 💡 Ideias futuras (depois de M7): editor de save, randomizer próprio, mods de dados lidos do `trpfs`.

## Regra
Tudo **local**. Nada de empacotar para distribuição (`make dist` não é objetivo).
