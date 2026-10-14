# Fase 9: Entender o jogo (o estudo AAA) (contínua)

**Objetivo do IDEA.md:** entender como é feito um jogo AAA. Recompilar é o meio; esta fase é o fim.
Tudo documentado em `docs/re/` como **descrição** (arquitetura, fluxos, nomes, offsets curtos), sem copiar
código decompilado ou assets.

## Trilhas de estudo
- [ ] 9.1 **Arquitetura do motor**: loop principal, threads (quem faz o quê), scheduler de tarefas, alocadores de
  memória (heaps), sistema de entidades/componentes.
- [ ] 9.2 **Streaming do mundo aberto**: como Paldea é dividido, carregado e descarregado; LOD; o que causa as
  quedas de FPS no Switch.
- [ ] 9.3 **Formatos de dados**: `trpfs`/`trpfd` (pacotes), modelos/materiais/esqueletos/animações (FlatBuffers
  `tr*`), texturas, scripts/eventos, tabelas de dados (Pokémon, golpes, itens, encontros).
- [ ] 9.4 **Renderização**: passes por frame (via `PVR_DEBUG_FRAME`), shaders principais, sombras, céu/tempo.
- [ ] 9.5 **Sistemas de jogo**: batalha (cálculo de dano, IA), Terastal, spawn/encontros no overworld, Pokémon
  seguidores, ciclo dia/noite e clima.
- [ ] 9.6 **Middleware**: o que é da Game Freak e o que é de terceiros (física, áudio, rede, UI).
- [ ] 9.7 **Comparação** com o Zelda LA: o que é igual (SDK, NVN) e o que muda num motor AAA de mundo aberto.

## Como trabalhamos aqui
- Pergunta → cartão `rea_worker` (🤖) → revisão (🧠) → nota em `docs/re/<tema>.md` com marcação
  ✅ verificado / 📖 lido / ❓ hipótese e evidência (evidence_id, endereço+build id).
- Parsers de formato em `Pokemon Decompile/tools/formats/` (🤖 cartões, critério: lê 100% dos arquivos daquele tipo
  sem erro + teste com arquivo do `lab/`).
