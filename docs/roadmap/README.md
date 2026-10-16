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
| 6 | [Jogável](fase-6-jogavel.md) | começar um jogo novo e andar pelo mapa aberto | ciclo shot.sh + correções | 🟡 **M5** e **M6 parcial** no teste manual (intro, começo da história, 1ª batalha); 30 fps com clock fixo; 60 fps experimental; falta fluidez (engasgos) e o crash raro conhecido |
| 7 | [Ferramentas de RE e debug](fase-7-ferramentas-re.md) | (contínua) fnprof, ganchos `PVR_*`, screenshot automático, REA/Ghidra | `fnprof.c`, `LARECOMP_*`, `sym.py`, `shot.sh` | 🟢 contínua: kit `PVR_*`, `glsl_slice.py`, `run_auto.sh`, gates; **falta log/aviso de crash** |
| 8 | [O aplicativo](fase-8-aplicativo.md) | launcher, menu overlay, resolução/FPS desbloqueados, recursos nossos | `ui/launcher.mm`, `menu.mm`, `hle/widescreen.c` | 🟡 nome **PSV Recomp**, `psvrecomp.ini`, `run_window.cmd` |
| 9 | [Entender o jogo (estudo AAA)](fase-9-estudo-aaa.md) | documentação de motor, formatos, sistemas de jogo | (não existe no LAS: é o nosso objetivo de estudo) | ⬜ contínua |

Ordem real: **0 → 1 → 2 → 3 → 4 → 5 → 6 → 8**, com **7 e 9 correndo em paralelo** desde a fase 1.

## Estado e próximos passos (revisão com o [USER], 15/10/2026)

**Alvo principal: v4.0.0** (com o update). A v1.0.0 segue só como build de comparação.

Marcos: M0-M2 provados por gate. **M3, M4, M5** atingidos e **M6 parcial** pelo teste manual do [USER] (15/10): do
logo até o começo da história, mais de 10 min sem crash, save persistente; o gate automático `window` fica como item
próprio para formalizá-los.

Ordem de trabalho (atualizada no fim de 15/10; 🟢 = provado por run_auto/teste do [USER], sem gate):
1. 🟢 **Crash da 1ª batalha** (1.7): jump table mal resolvida no gen.py — corrigido (commit 28c44eb); a batalha roda.
2. 🟢 **Desempenho (6.6)** — os 3 objetivos do [USER]:
   - 🟢 **Clock fixo:** o jogo pede intervalo 2 (30 fps) e o limitador `runtime/framepace.c` respeita; menu/loading
     não aceleram mais (commit 0ad8fe3).
   - 🟢 **30 fps:** batalha 9 → 28 fps (FP do mingw), depois 46-48 fps sem limitador (transform feedback em VRAM);
     mundo aberto parado 54-63 sem limitador. Personagem invisível no mundo aberto corrigido (occlusion query).
   - 🧪 **60 fps:** `PVR_GAME60=1` liga o modo 60 do próprio jogo com a velocidade certa (só v4.0.0, experimental).
     Falta: opção no menu/`psvrecomp.ini`, teste longo de sincronia (animações, cutscenes).
   - **Regra de teste ([USER], 15/10): daqui em diante tudo é testado a 30 fps** (limitador ligado, sem
     `PVR_FRAMEPACE=0` / `PVR_GAME60`), salvo medição de folga pedida explicitamente.
3. 🟢 **Fluidez / consistência (6.8)** — medição feita (commit 912c97b): a 30 fps os picos só aparecem no carregamento
   e na compilação de shaders ao entrar em cenas novas; o [USER] considera os 30 fps ok (15/10). Os itens abaixo ficam
   em espera, retomados se os engasgos voltarem a incomodar ou para preparar 60 fps / fidelidade:
   1. **Medição** por frame: tempo de cada frame, 1% low, quantos picos e a causa de cada um (compilação de shader,
      upload de textura, espera de GPU, jogo). Sem isso qualquer correção é chute.
   2. **Compilação de shader durante o jogo:** `compiles N pending` e draws pulados em áreas novas → pré-compilar
      (no carregamento / offline) ou pipeline libraries.
   3. **Upload de texturas:** ~200 MB a cada 2 s re-checados/re-enviados → rastrear páginas escritas (proteção de
      memória) em vez de comparar tudo.
   4. **Pontos de sincronia CPU↔GPU:** cópia buffer→buffer e leituras de imagem pela CPU forçam flush + espera.
   5. **Ritmo de apresentação vs monitor:** o limitador usa timer, não o refresh do monitor → alternância de 2/3
     refreshes por frame em 60/144 Hz. Apresentar sincronizado ou VRR.
   6. **Código recompilado:** ~7 % ainda no caminho lento de FP; FN_ENTER em toda função; dispatch indireto.
   7. **Memória:** dados que a GPU lê (vértices, constantes) moram na RAM e são lidos via PCIe; cópias em VRAM
      dos mais usados.
4. 🟢 **Log e aviso de crash (7.x):** caixa de erro com a causa + cópia do log em `crashes/` + `tools/rea/crash_report.py` (16/10; falta o [USER] ver a caixa na janela).
5. **Visual:** skybox com linhas, artefatos de iluminação, objetos sem render. O [USER] indica o lugar e cria saves.
6. 🟢 **Áudio (5.1):** corrigido 16/10 (o build de janela usava o dispositivo de áudio falso do headless); o jogo toca pelo audout. Falta o [USER] ouvir na janela.
7. 🟢 **Teclado do nome (5.6, swkbd):** caixa de texto na frente do jogo + resposta em UTF-16 (o Violet não usa UTF-8) (16/10; falta o [USER] ver o nome na ficha).
8. ✅ **Gate `window`:** `gates.py run window` (jogo novo, 30 fps, sem crash, telas renderizadas, cena avança) — run_id=312d34de1a.
9. **Fidelidade (futuro, depois da fluidez):** resolução 1440p/4K (a base do LAS já tem escala de render; faltam
   cópias para a CPU de imagens escaladas e efeitos com pixel fixo; medir VRAM), anti-aliasing (há SMAA no código
   herdado — conferir se está ligado e qual AA o jogo usa), filtro anisotrópico.

## Problemas conhecidos (para caçar depois)

- **Crash raro no carregamento da 1ª batalha** (~1 em 9 execuções do save `user_antes_batalha_20261015`, sem
  limitador): `exception c0000005` em funções do jogo, p.ex. `f_7000c1e658 <- f_7000c1e5f8 <- f_7000e02cac` (busca
  de componente com hash `0x3d3f8b275e8b9993` que volta nulo e o chamador não checa) e outro acessando `0x1e8`; uma
  vez precedido de `OODLE ERROR: LZ corruption`. Hipótese: race de carregamento que o nosso timing expõe (no Switch
  o objeto já estaria pronto). Logs: `lab/host-vk/stb3_3.run1.log`, `xs3.run1.log`, `stab_7.run1.log`,
  `stab_8.run1.log`. Adiado por decisão do [USER] (15/10).

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
| M6 "Mundo aberto" | anda por Paldea 10 min sem crash; FPS medido | 🟢 teste do [USER] (>10 min) + frametime a 30 fps no mundo aberto; falta um gate longo |
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
