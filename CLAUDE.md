# CLAUDE.md: diretrizes do workspace REA

> Lido por Claude (Hermes desktop / Claude Code) e por qualquer agente que trabalhe aqui.
> Objetivo (IDEA.md): **decompilar Pokémon Scarlet/Violet para uso pessoal e entender como é feito um jogo AAA.**

## 1. Papéis: Claude orquestra, os modelos locais executam

**Claude é o orquestrador, não o executor.** Todo trabalho de execução vai para os modelos locais
(Ollama, `qwen3-coder-64k` por padrão). Claude:
- entende o pedido, quebra em **cartões** pequenos e verificáveis, escolhe ferramenta e modelo;
- despacha os cartões e **verifica** cada entrega contra a evidência real;
- aceita, devolve com os erros exatos (no máximo 3 tentativas) ou escala;
- decide arquitetura, registra os achados em `docs/` e reporta ao [USER].

Claude **não** escreve o código do produto nem faz a investigação de RE "na mão" quando um worker pode fazer.
Exceções (sempre registradas em `docs/pipeline-log.md` com o motivo):
1. o worker falhou 3 vezes no mesmo cartão: Claude termina, marcando o que aproveitou;
2. edição trivial (1 a 3 linhas) em que escrever o cartão custa mais que a edição;
3. a própria infraestrutura de verificação (harness, checkers, scripts de teste do pipeline).

### Qual worker usar

| Tarefa | Ferramenta | Comando |
|---|---|---|
| Investigação de RE em binário (quem chama X, o que faz a função Y, strings, xrefs) | `tools/rea/rea_worker.py` (qwen + REA/Ghidra, contrato verificado em código) | `python tools/rea/rea_worker.py --target 'D:\Dev\REA\lab\targets\<bin>' --question '...' --out 'D:\Dev\REA\lab\reports\<bin>-<tema>.md'` |
| Gerar um arquivo (script Python, parser de formato, teste, tabela, C/C++) | `tools/workers/local_worker.py` | `python tools/workers/local_worker.py --task work/cards/Wnn-x.md --out <arquivo> --ctx <api.h> --lang python` |
| Triagem de log / resumo de saída grande | `local_worker.py` com cartão de resumo | idem, `--out work/notes/<x>.md` |

Rodar sempre pelo `terminal` com `background=true, notify=true`; enquanto isso Claude prepara o próximo cartão.

**Não usar `delegate_task` (subagente Hermes) como worker.** Testado em 14/10: o qwen com o prompt grande do
Hermes fez **0 chamadas de ferramenta** e entregou um relatório **inteiramente inventado**. Os harnesses acima
falam direto com o Ollama, com prompt curto, e recusam saída que não bate com a evidência.

## 2. Skills que o Claude deve carregar

| Skill | Quando |
|---|---|
| `rea-local-lab` | qualquer tarefa com REA/Ghidra ou com o `rea_worker.py` |
| `local-worker-orchestration` | ao escrever/despachar/verificar cartões; ler `references/worker-cards.md` (como escrever cartões que o qwen acerta) |
| `local-ai-resource-manager` | antes de subir modelo: cabe na RAM/VRAM? |
| `systematic-debugging` | bug ou resultado estranho: causa raiz antes de corrigir |
| `test-driven-development` | código novo de ferramenta: teste/oráculo primeiro |
| `grounded-citations` | ao escrever achados em `docs/`: toda afirmação com fonte |
| `blocked-page-recovery` | download/documentação bloqueada |

Se uma skill estiver errada ou faltar uma armadilha descoberta, **corrigir a skill** (`skill_manage patch`) antes de encerrar.
As skills específicas e versionadas deste workspace ficam em [`.agents/skills/`](.agents/skills/); carregar a
`SKILL.md` correspondente antes de trabalho de RE ou de recompilação estática.

## 3. Como escrever um cartão (resumo; o detalhe está em `worker-cards.md`)
- Arquivo em `work/cards/Wnn-<tema>.md`: objetivo, **API existente** que pode usar (curta), entradas/saídas,
  **critério de aceite checável por script** (compila, teste passa, contagem, hash, comparação com oráculo).
- Teste: inclua a **tabela de valores esperados** já calculada. Formato binário: inclua offsets/tamanhos conhecidos e
  um arquivo de exemplo **do lab** (nunca cole bytes do jogo no cartão versionado).
- Nada de exemplos literais em cartão criativo (o qwen copia).
- Retry: `<cartão>-t2.md` com seção "TENTATIVA 2 — REJEITADA" listando cada erro e a resposta correta.

## 4. Verificação (o worker se auto-reporta; Claude nunca confia sem checar)
- **Gates (`tools/verify/gates.py`) são a única prova aceita.** "Compila", "linka", "boot OK", "fase N concluída"
  só valem citando um `run_id` de `python tools/verify/gates.py run <dumps|host|link|boot|simd|excl_pair>`, que roda o
  comando de verdade e grava a evidência em `work/evidence/gates.jsonl` (hashes, exit code, estágio do boot).
  Ninguém escreve nesse arquivo à mão. Doc que diz ✅/[x]/concluído sem `run_id=...` é barrada no pre-commit.
- **Proibido (contado como falso):** script que só faz `echo "✅ PASSOU"`; `|| true` em build/run; trocar código real
  por stub "para compilar"; `rm -rf` em `dumps/`; replace cego em docs; dizer que uma ferramenta "não existe" sem
  procurar em `D:\Tools`. Falhou? Dizer que falhou, com a saída.
- **Placar do qwen:** toda afirmação de um agente vira uma linha em `work/evidence/claims.jsonl`:
  `gates.py claim <gate> --agent qwen --text "<o que ele disse>"` (roda o gate e julga) ou, para turnos de chat
  já passados, `gates.py note --agent qwen --verdict FALSE --evidence "<prova>"`. `gates.py score -v` = taxa de falsas.
- Pre-commit: `cp tools/verify/pre-commit .git/hooks/pre-commit` (roda `test_gates.py` + `gates.py lint --staged`).
- RE: conferir 2 ou 3 afirmações contra `<relatório>.log.jsonl` (saídas reais). Um id real numa afirmação errada passa
  pelo harness: só a revisão pega. Registrar o veredito em `docs/rea-worker-reviews.md`.
- Código: compilar/rodar de verdade; teste diferencial contra oráculo sempre que existir (Unicorn, ferramenta de
  referência, arquivo conhecido). "Compilou" não é "funciona".
- Nunca reportar "feito/OK" sem a saída que prova. Falhou? Dizer que falhou e por quê.
- Todo cartão vira uma linha em `docs/pipeline-log.md` (dono, modelo, tentativas, tempo, resultado, motivo).

### 4.1 Regras anti-alucinação (lições de 15/10: 20 de 27 afirmações do qwen eram falsas)
Valem para o qwen como worker **e** para qualquer modelo local que assuma o chat (fallback do Hermes).
1. **Modelo local no comando do chat = só observa.** Pode rodar gates, ler logs e escrever notas em
   `work/notes/`. **Não** cria cartões, **não** despacha subagentes, **não** edita código/roadmap, **não** declara
   fase concluída. Fase "concluída" só existe com o marco do roadmap provado por `run_id` (M3 = screenshot com o logo).
2. **O roadmap manda.** Os números de fase são os de `docs/roadmap/README.md`; inventar "fase 4.3/5" de outra coisa
   é falso. Na dúvida, ler a página da fase antes de agir.
3. **Caminhos absolutos dentro de `D:\Dev\REA`.** Subagente/worker sem caminho absoluto escreveu no repo do Hospital
   (`C:\Users\ser_l\RPG\Hospital`). Todo cartão diz o arquivo exato de saída; Claude confere com `git status` nos
   dois repos.
4. **Só nomes que existem.** Antes de citar uma função/tipo num cartão, `grep` no runtime ou no log. Funções NVN
   do jogo vêm de `lab/host-*/nvnmiss.log` (`PVR_NVN_MISSING=1`), não da memória do modelo
   (`nvnCommandBufferPresent` e `NvnPresentId` não existem).
5. **Como uma função NVN entra no runtime:** `NVN(nvnNome) { ... }` em `nvn/cmdbuf.c` ou `nvn/objects.c`
   (macro de `nvn/nvn.h`, argumentos em `A(i)`/`AP(i)`), registrada por nome no `nvnDeviceGetProcAddress`.
   Função C solta em arquivo novo **não é chamada por ninguém** e nem entra no build (`build_host.sh` lista os
   arquivos de `nvn/` um a um).
6. **Arquivo novo tem que ser usado.** Aceite inclui: entrou no `build_host.sh`/foi referenciado, e uma rodada real
   mostra o efeito (ex.: `nvn-missing` some do log). "Compila" com arquivo morto conta como falso.
7. **Executou? Cole a saída.** "Pronto para rodar" exige que o comando tenha rodado nesta máquina (ex.: o exe em janela
   precisa de `recomp/run_window.cmd` por causa das DLLs do MSYS2).
8. **Um cartão por vez, numerado do próximo livre de `docs/pipeline-log.md`.** Nada de gerar dezenas de cartões
   por script com o mesmo texto: cartão sem a API real e sem aceite checável é rejeitado antes de despachar.

## 5. Privacidade e parte legal (inegociável)
- As ROMs/dumps (`roms/*.xci`, `roms/*.nsp`), chaves (`prod.keys`, `title.keys`), `exefs/`, `romfs/`, código gerado e saídas de
  Ghidra/REA sobre o jogo são **privados**: ficam em pastas ignoradas (`.gitignore`), **nunca** em commit, issue,
  chat público ou upload.
- `docs/` pode descrever **como** algo funciona (arquitetura, nomes de sistemas, offsets curtos como referência);
  **não** pode conter trechos grandes de código decompilado, assets, textos ou modelos do jogo.
- Chaves só do console do próprio [USER]. Nunca baixar chaves, ROMs ou firmware da internet.
- Uso pessoal/estudo. Nada é redistribuído.

## 6. Estrutura do workspace

```
D:\Dev\REA\
├─ CLAUDE.md / AGENTS.md   diretrizes (este arquivo)
├─ IDEA.md                 objetivo
├─ docs/                   achados e guias (versionado)
├─ .agents/skills/         skills versionadas deste workspace
├─ tools/rea/              rea.sh (CLI enxuta), rea_worker.py (harness de RE)
├─ tools/workers/          local_worker.py (worker de código)
├─ work/                   cartões e notas de trabalho (versionado, sem conteúdo do jogo)
├─ lab/                    alvos, snapshots, relatórios brutos      [ignorado]
├─ psvrecomp/              nosso projeto de recompilação (o que for nosso é versionado)
├─ roms/                   ROMs/dumps do Switch                    [PRIVADO, ignorado]
└─ ref/                                    referências de terceiros  [ignorado]
```
Ferramentas pesadas fora do repo: `D:\Tools` (Ghidra, JDK, MinGW), `D:\msys64`.

## 7. Recursos da máquina (RTX 3070 Ti 8 GB / 32 GB RAM)
- `qwen3-coder-64k` usa ~25 GB de RAM com offload: **um modelo por vez**, workers **sequenciais**.
- Ghidra/REA + qwen ao mesmo tempo é o limite: feche Unity/Chrome pesado antes de lotes grandes.
- `ollama stop qwen3-coder-64k` ao fim de cada lote.
- C: tem ~16 GB livres: todo download/cache/instalação vai para o D:.

## 8. Ambiente e comandos (detalhes em `docs/ambiente.md`)
- REA: `bash tools/rea/rea.sh <cmd> '<alvo>'` (saída enxuta; `REA_RAW=1` para envelope completo).
- MCP `rea` no Hermes: 21 ferramentas filtradas (para o Claude; não para o qwen).
- Compilação nativa: `export PATH="/d/msys64/ucrt64/bin:/d/msys64/usr/bin:$PATH"` **só no comando**, nunca deixar persistente
  (quebra o `TMP` do REA).

## 9. Git
- Commits pequenos, mensagem em português no imperativo ("Adiciona parser de TRPAK").
- Antes de commitar: `git status` e conferir que nada de `lab/`, dump, chave ou saída de Ghidra entrou.
- Nunca `git add -A` às cegas na raiz.
