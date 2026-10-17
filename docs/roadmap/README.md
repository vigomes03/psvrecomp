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
| 4 | [Gráficos: NVN → Vulkan](fase-4-graficos.md) | **primeiro frame**: logo / tela de título renderizada | `runtime/nvn/*`, `maxwell/translate.c`, `vulkan/` | 🟢 **M3/M4**: árvores, névoa do vale, céu, terreno e iluminação alinhados ao Eden; sobra comparar/refinar o desfoque de distância |
| 5 | [Áudio, input, save, tempo](fase-5-sistemas.md) | controle funciona, som toca, save grava/carrega | `services/audio.c`, `hle/input.c`, `fs.c` (save) | 🟢 teclado, áudio, save e relógio do jogo funcionam; áudio e nome confirmados pelo [USER] em 16/10 |
| 6 | [Jogável](fase-6-jogavel.md) | começar um jogo novo e andar pelo mapa aberto | ciclo shot.sh + correções | 🟢 **M5/M6**: mundo aberto a 30 fps com velocidade correta; espelhos de VRAM reduzem o trabalho da GPU. Crashes raros seguem registrados e adiados |
| 7 | [Ferramentas de RE e debug](fase-7-ferramentas-re.md) | (contínua) fnprof, ganchos `PVR_*`, screenshot automático, REA/Ghidra | `fnprof.c`, `LARECOMP_*`, `sym.py`, `shot.sh` | 🟢 contínua: kit `PVR_*`, `glsl_slice.py`, `run_auto.sh`, gates, relatório de crash e safe start do ini |
| 8 | [O aplicativo](fase-8-aplicativo.md) | launcher, menu overlay, resolução/FPS desbloqueados, recursos nossos | `ui/launcher.mm`, `menu.mm`, `hle/widescreen.c` | 🟡 nome **PSV Recomp**, `psvrecomp.ini`, safe start, `run_window.cmd` e menu F1; falta a tela inicial/launcher |
| 9 | [Entender o jogo (estudo AAA)](fase-9-estudo-aaa.md) | documentação de motor, formatos, sistemas de jogo | (não existe no LAS: é o nosso objetivo de estudo) | ⬜ contínua |

Ordem real: **0 → 1 → 2 → 3 → 4 → 5 → 6 → 8**, com **7 e 9 correndo em paralelo** desde a fase 1.

## Estado e próximos passos (revisão com o [USER], 16/10/2026)

**Alvo principal: v4.0.0** (com o update). A v1.0.0 segue só como build de comparação.

Marcos: M0-M2 provados por gate. **M3-M6** têm gate `window`/teste manual do [USER]; M6 inclui 10 min no mundo aberto
(run_id=c6a80b10d8). O alvo de jogo é **30 fps estáveis, com velocidade correta**. Explorar 60 fps está suspenso até o
[USER] pedir explicitamente.

Ordem de trabalho atual (16/10; 🟢 = execução/teste real; os crashes raros são baixa prioridade, depois do app):
1. 🟢 **Desempenho / 30 fps (6.6):** o intervalo 2 do jogo mantém 30 fps e a velocidade correta. O gargalo que entrou
   com árvores e detalhes era a GPU buscar vértices/índices dos pools importados da RAM via PCIe: espelhos de 16 MB na
   VRAM, invalidados por `MEM_WRITE_WATCH`, baixaram o trabalho da GPU de ~1300 para ~700 ms a cada 2 s. Quatro runs
   (incluindo Poco Path) sem crash e 30 fps cravados; o jogo tinha ~45 fps sem limitador, mas fica limitado a 30 por decisão
   do [USER]. `PVR_VRAM_MIRROR=0`/`PVR_NO_WRITE_WATCH=1` voltam ao caminho antigo.
2. 🟢 **Fluidez / consistência (6.8):** a 30 fps, o trabalho por quadro ficou em ~17–19 ms; picos observados nos testes
   são compilação/carregamento e capturas do pipeline. Só retomar esta investigação se os engasgos voltarem a incomodar.
3. 🟢 **Visual:** céu, terreno, árvores/moitas, iluminação e névoa sobre o vale foram comparados com o Eden no mesmo save
   e horário (`PVR_CLOCK_START`). A imagem principal bate; sobra apenas comparar/refinar o desfoque de distância, se o
   [USER] apontar uma cena onde incomode.
4. 🟢 **Sistemas (fase 5):** áudio e teclado do nome funcionam e foram confirmados pelo [USER]; save e relógio persistem.
5. 🟡 **APP / M7:** menu overlay estilo LAS pronto (F1/Esc; controle: Home ou Back+Start): Controls, Video (monitor,
   fullscreen, VSync, FPS, escala, FSR1, SMAA), Audio e Quit. Configurações em `psvrecomp.ini`; se morrer durante a
   abertura ou até 300 frames depois de uma mudança, a próxima abertura arquiva o ini em `.crashed` e usa defaults.
   **Próximo cartão:** tela inicial/launcher com Play, Settings e Quit; ela deve segurar a inicialização do jogo até Play.
6. ⏸️ **60 fps:** `PVR_GAME60=1` existe como experimento, mas não entra no menu nem é alvo agora.
7. ⏸️ **Crashes raros:** vestiário e primeira batalha permanecem registrados abaixo; só retomar depois do APP ou se
   ficarem determinísticos.

## Problemas conhecidos (para caçar depois)

- **Crash no vestiário (escola, antes de "Head to the lighthouse")**, jogo manual do [USER] em 16/10, 1 ocorrência,
  sem passo a passo para repetir: `exception c0000005 accessing 0xffffffffffffffff` em `f_7000bf3dcc <- f_7000bf399c
  <- f_70027beaec <- f_7002b79458`. `f_7000bf3dcc` é a remoção de um nó de `unordered_map` (libc++ `__hash_table`):
  o nó lido do bucket (x19 = `32d102231b656757`) é lixo, ou seja, a tabela já estava corrompida (uso depois de
  liberar / corrida entre threads), não um erro de tradução nesse ponto. Log: `lab/host-vk/crash_vestiario_20261016.log`
  (tem o `[input]` da sessão); save logo depois: `lab/saves/user_apos_vestiario_20261016`. Se repetir no mesmo
  lugar, vira bug determinístico e se caça pelo chamador.
- **Crash raro no carregamento da 1ª batalha** (~1 em 9 execuções do save `user_antes_batalha_20261015`, sem
  limitador): `exception c0000005` em funções do jogo, p.ex. `f_7000c1e658 <- f_7000c1e5f8 <- f_7000e02cac` (busca
  de componente com hash `0x3d3f8b275e8b9993` que volta nulo e o chamador não checa) e outro acessando `0x1e8`; uma
  vez precedido de `OODLE ERROR: LZ corruption`. Hipótese: race de carregamento que o nosso timing expõe (no Switch
  o objeto já estaria pronto). Logs: `lab/host-vk/stb3_3.run1.log`, `xs3.run1.log`, `stab_7.run1.log`,
  `stab_8.run1.log`. Adiado por decisão do [USER] (15/10).

- ~~Crash antes do Poco Path (`no function at 7002a1fc24`)~~ — corrigido em 16/10. Primeiro registrado como
  "vtable corrompida" (ERRADO: era determinístico, sempre no mesmo endereço). Causa real no gen.py: um switch de 11
  casos em `f_7002a1f54c` teve a função partida onde uma função vizinha pula para o meio dela (cauda compartilhada);
  os casos depois do corte eram rejeitados e caíam no dispatch global. Ver pipeline-log 16/10.

- ~~Personagem invisível no mundo aberto~~ — corrigido em 15/10 (occlusion query reportava 0 pixels; ver pipeline-log).

## Marcos

| Marco | Critério objetivo | Estado (16/10) |
|---|---|---|
| M0 Dump pronto | `dumps/base/exefs/main` e `dumps/update/exefs/main` existem; build ids anotados; romfs listado | ✅ gate dumps (run_id=131ff828b2) |
| M1 "Compila" | `generated/main/*.c` + `sdk` compilam e linkam numa DLL; 0 `rt_udf` por instrução não suportada (ou lista justificada) | ✅ gate boot com pvgame.dll (run_id=990a33212b) |
| M2 "Respira" | log mostra o jogo criando threads, abrindo serviços e entrando no loop de frames (headless) | ✅ v400 run_id=7adc0390c2, base run_id=db35401e31 |
| M3 "Primeiro pixel" | screenshot automático mostra o logo da Game Freak / The Pokémon Company | ✅ gate window (run_id=312d34de1a): telas renderizadas no jogo novo |
| M4 "Título" | tela de título com música, e o controle navega no menu | ✅ gate window (run_id=312d34de1a) + áudio corrigido 16/10 (o [USER] confirma o som) |
| M5 "Jogo novo" | cria personagem, cutscene inicial, controla o personagem | ✅ gate window (run_id=312d34de1a): a cena avança com a entrada; nome pela caixa de texto (16/10) |
| M6 "Mundo aberto" | anda por Paldea 10 min sem crash; FPS medido | ✅ gate window --save (run_id=c6a80b10d8): 10 min no mundo aberto sem crash a ~29 fps, entrada automática simples (não é exploração livre) + teste do [USER] (>10 min) |
| M7 "App" | launcher próprio, configurações, recursos extras | 🟡 nome PSV Recomp, psvrecomp.ini, crash report |

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
