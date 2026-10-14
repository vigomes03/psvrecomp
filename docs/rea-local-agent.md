# REA Lab: guia para o agente local

> Leitor: o agente local (qwen via Ollama, rodando como subagente do Hermes).
> Orquestrador: Claude, na sessão desktop do Hermes. Ele planeja, distribui
> tarefas e confere os relatórios. Você faz o trabalho pesado de investigação.
> Tudo o que está aqui foi testado nesta máquina (14/10/2026).

---

## 1. Máquina e ambiente (fatos verificados)

| Item | Valor |
|---|---|
| SO | Windows 11, shell = git-bash (sintaxe POSIX; `/d/...` funciona no bash) |
| GPU / RAM | RTX 3070 Ti 8 GB VRAM / 32 GB RAM |
| REA | `D:\Dev\REA\rea-main\rea-main` (6.4.0, snapshot do `main`, build local) |
| Addon nativo Windows | compilado com MinGW em `native\windows\build` (`verify:windows-native:artifact` OK) |
| Ghidra | `D:\Tools\ghidra_12.1.4_PUBLIC` (`GHIDRA_INSTALL_DIR`) |
| JDK | `D:\Tools\jdk-21.0.12.1+1` (`JAVA_HOME`) |
| Node | `C:\Program Files\nodejs\node.exe` v24.18 (= `.nvmrc`) |
| Laboratório | `D:\Dev\REA\lab\` → `targets\`, `reports\`, `snapshots\` · scripts em `D:\Dev\REA\tools\rea\` |
| Modelo worker | `qwen3-coder-64k` (qwen3-coder:30b MoE, ctx 65536) via `http://127.0.0.1:11434/v1` |

`rea doctor --provider ghidra` = tudo OK. Hopper não existe no Windows.
IDA e JADX (Android) **não estão configurados**: não tente usar.

### O que funciona no Windows (Ghidra P0, experimental)
- PE nativo x86/x86-64 (EXE e DLL) em disco NTFS local. **Só leitura.**
- Análise estática de JavaScript/Electron (`analyze-javascript-application`): não precisa de Ghidra.
- **Não funciona aqui:** .NET/managed via Ghidra, alvos fora de NTFS, depuração (gdb/rizin), Android sem JADX.

---

## 2. Arquitetura

```
Claude (Hermes desktop): orquestrador
  ├─ define a pergunta, divide em cartões, revisa e aceita/rejeita
  └─ terminal (background) ──► python D:\Dev\REA\tools\rea\rea_worker.py   ← HARNESS
                                  ├─ Ollama /api/chat  →  qwen3-coder-64k (worker)
                                  ├─ ferramentas: rea(callers|search|xrefs|function|decompile|analyze), finish
                                  ├─ contrato verificado em código (seção 3)
                                  └─ reports\<alvo>-<tema>.md  +  .log.jsonl (toda chamada e saída)
```

**Não use `delegate_task` (subagente Hermes) como worker de RE.** Testado em
14/10: o qwen recebeu o prompt grande do Hermes, passou 2 min processando e
escreveu um relatório **100% inventado** (zero chamadas de ferramenta, código
"estilo MSDN", função `main` que não existe). O harness `rea_worker.py` resolve:
prompt curto, só 2 ferramentas, e o relatório é recusado se não bater com as saídas reais.

**Por que CLI e não MCP para o worker:** o catálogo MCP completo do REA tem
**207 ferramentas, cerca de 220 mil tokens só de schemas**. Não cabe nos 64k do
qwen. O wrapper `rea.sh` entrega só `evidence_id`, `confidence` e
`normalized_result`, com teto de 2000 tokens por chamada.

O MCP fica para o Claude, com filtro de 21 ferramentas (cerca de 8k tokens).
Veja a seção 7.

---

## 3. Contrato do worker (obrigatório)

Aplicado **em código** pelo `rea_worker.py` (o relatório é recusado até 3x, depois `FAILED_CONTRACT`):
- `finish` só depois de pelo menos 3 chamadas REA bem-sucedidas;
- todo `ev_...` citado precisa ter saído de uma chamada desta execução;
- todo `FUN_…`/`LAB_…`/`DAT_…`/`0x…` (6+ dígitos) citado precisa aparecer em alguma saída do REA;
- seções obrigatórias: Observado, Inferido, Falhas.

O que o código **não** pega (o Claude revisa): um id real citado numa
afirmação errada. Exemplo do teste: "sem referências", citando o xrefs da *string*
`LookupAccountSidW` em `.rdata` em vez do import `EXTERNAL:0x4`.

Regras para o modelo:

1. **Cada afirmação cita o `evidence_id`** da saída REA que a sustenta.
2. Separe **Observado** (está literalmente na saída) de **Inferido** (sua interpretação).
3. **Nunca invente** endereço, nome de função, string ou código. Se um comando
   falhou, copie o erro exato em "Falhas" e siga com o que tem.
4. Um alvo, uma pergunta. Orçamento padrão: no máximo 12 chamadas REA por cartão.
5. Não modifique o alvo, não rode o alvo, não baixe binários.
6. Termine **sempre** com o relatório no formato da seção 6, mesmo que incompleto.
   Um relatório honesto com "não encontrei" vale mais que um bonito e falso.
7. Se travar (3 erros iguais, ou a pergunta exige ferramenta indisponível),
   pare e escreva em "Escalar para Claude" o que faltou.

---

## 4a. Rodar o worker (harness)

```bash
cd /d/Dev/REA
python tools/rea/rea_worker.py --target 'D:\Dev\REA\lab\targets\whoami.exe' \
  --question 'Qual função interna chama LookupAccountSidW e o que ela faz?' \
  --out 'D:\Dev\REA\lab\reports\whoami-lookupaccountsid.md'
# opções: --model qwen3-64k  --max-steps 14
# saída: relatório .md (com rodapé <!-- harness: stats -->), .log.jsonl, ou .FAILED.txt
```

Custo medido (whoami.exe, 3070 Ti): cerca de 5,5 min, 7 a 13 chamadas REA, cerca de 37k tokens de prompt
locais e **0 tokens de API**. O Claude só lê o relatório final e confere 2 ou 3 ids no `.log.jsonl`.

## 4b. Comandos verificados (via wrapper, para uso manual/Claude)

Cada chamada leva cerca de 20 s, porque o Ghidra reanalisa o arquivo. É normal, não cancele.
Sempre passe o caminho do alvo entre aspas simples, com barra invertida do Windows.

```bash
R=/d/Dev/REA/tools/rea/rea.sh
T='D:\Dev\REA\lab\targets\whoami.exe'

$R analyze  "$T" --provider ghidra          # visão geral: segmentos, nº de funções/strings
$R search   "$T" LookupAccountSid --kind procedures   # funções/imports por nome
$R search   "$T" "texto"                    # strings (padrão) ; --mode regex p/ regex
$R xrefs    "$T" 'EXTERNAL:0x4'             # quem referencia um endereço/símbolo
$R function "$T" 0x140003d24                # dossiê completo da função que contém o endereço
$R decompile "$T" FUN_140003c90             # pseudocódigo (nome ou endereço)
$R <comando> --help                         # ajuda de qualquer comando

REA_OFFSET=2000 $R decompile "$T" FUN_...   # próxima janela de uma saída longa
REA_TOKENS=4000 $R function "$T" 0x...      # janela maior (use com moderação)
REA_RAW=1 $R ...                            # envelope completo (grande; evite)
```

Dicas de leitura (PE x64 típico, `image_base 0x140000000`):
- `EXTERNAL:0xN` = função importada de DLL.
- Endereço em `.rdata` = tabela de import/dados, **não** é código. Código fica em `.text`.
- `FUN_<endereço>` = nome gerado pelo Ghidra (o PDB não é aplicado).
- `confidence: observed` = fato do Ghidra; `derived` = composto pelo REA.

Fluxo típico: **search** (acha import/string) → **xrefs** (acha onde é usado)
→ **function** (qual função contém) → **decompile** → repetir com callers/callees.

---

## 5. Escolha de modelos (3070 Ti 8 GB + 32 GB)

Modelos já instalados no Ollama:

| Modelo | Uso no lab | Observação |
|---|---|---|
| `qwen3-coder-64k` | **worker padrão** | 30B MoE (cerca de 3B ativos) → rápido mesmo com offload para RAM; ctx 64k; bom com tool-calls |
| `qwen3-64k` | alternativa para raciocínio/síntese | mesma base MoE, ctx 64k |
| `qwen2.5-coder:14b-instruct-q4_K_M` | cartões pequenos (resumir pseudocódigo) | ctx padrão do Ollama = 4k → **cria uma variante 32k antes de usar como agente** |
| `qwen3.8:27b` | não recomendado como agente | denso, 17 GB → lento com 8 GB VRAM |
| `qwen3:8b` / 7B | não recomendado | perde o fio em investigação multi-etapa |

Regras de memória:
- Contexto mínimo para o agente do Hermes: **64k**. Com o padrão de 4k do Ollama,
  o prompt é truncado em silêncio e o modelo nunca vê as ferramentas.
- O worker ocupa cerca de 25 GB de RAM. Feche Unity e Chrome pesados antes.
  Um modelo por vez, agentes **sequenciais**.
- `ollama stop qwen3-coder-64k` ao terminar o lote.

---

## 6. Formato do relatório (`D:\Dev\REA\lab\reports\<alvo>-<tema>.md`)

```markdown
# <alvo>: <pergunta curta>
## Pergunta
## Observado
- <fato> (ev_xxxxxxxx)
## Código decompilado (trecho relevante)
## Inferido
- <hipótese> (baseada em: ev_..., ev_...)
## Falhas / perguntas em aberto
## Escalar para Claude (se aplicável)
## Comandos executados
```

---

## 7. Setup do Claude/MCP (o humano aplica: o Hermes bloqueia edição do config pelo agente)

O `rea setup` já registrou o servidor `rea` em `%LOCALAPPDATA%\hermes\config.yaml`
e no Claude Code. Para não carregar 220k tokens de schemas, troque o bloco
`rea:` em `mcp_servers` por este e rode `/reload-mcp` (ou reinicie o Hermes):

```yaml
  rea:
    command: C:\Program Files\nodejs\node.exe
    args:
      - D:\Dev\REA\rea-main\rea-main\scripts\rea.mjs
      - mcp
    env:
      GHIDRA_INSTALL_DIR: D:\Tools\ghidra_12.1.4_PUBLIC
      JAVA_HOME: D:\Tools\jdk-21.0.12.1+1
      REA_MCP_INPUT_SCHEMA_PROFILE: compact
      REA_MCP_OUTPUT_SCHEMA_PROFILE: 'off'
    enabled: true
    timeout: 600
    tools:
      include: [binary_session, open_binary, binary_overview, list_procedures,
        search_procedures, procedure_info, procedure_pseudo_code, procedure_callers,
        procedure_callees, procedure_references, xrefs, find_xrefs_to_name,
        list_strings, search_strings, list_segments, list_names, analyze_function,
        batch_decompile, get_call_graph, list_unknowns, analyze_javascript_application]
      resources: false
      prompts: false
```

Vantagem do MCP sobre a CLI: a sessão MCP mantém o Ghidra aberto, então só a
primeira consulta paga os cerca de 20 s. Se o worker mostrar que dá conta de MCP,
dá para migrá-lo depois.

---

## 8. Roteiro do laboratório (ordem)

1. ✅ REA + Ghidra + JDK + addon instalados, `doctor` verde.
2. ✅ Wrapper `rea.sh` com saída enxuta.
3. ✅ Teste de referência `whoami.exe` → `LookupAccountSidW` (resposta certa: `FUN_140003bc0`,
   que habilita `SeDebugPrivilege` e resolve o SID de `param_1` em `DOMÍNIO\nome`).
   - run 1 (subagente Hermes): relatório inventado → **rejeitado**
   - run 2 (harness v1): honesto mas não achou (seguiu a string em vez do import)
   - run 3 (harness v2 + `callers`): **acertou**; 1 erro (chamou de função o endereço de chamada `0x14000377c`)
   - run 4 (harness v3 + checagem de símbolos fantasmas): **aceito com revisão**. Achou também os 2 chamadores
     (`FUN_140003498`, `FUN_140003b3c`), nenhum símbolo inventado, 8 min, 0 tokens de API.
     Ressalvas: citou ids do decompile em vez do xrefs; deixou a seção de código vazia.
   - Revisões em `reports/REVIEW.md`
4. Medir por cartão: chamadas REA, tempo, acertos/erros do worker, tokens gastos pelo Claude.
5. Alvos próprios (programa seu compilado) → depois apps reais (sempre PE x64, NTFS).
6. Se precisar de captura de processo / Frida / gdb → migrar o lab para Linux
   (o outro HD). Ollama e os modelos são os mesmos.

## 9. Fazer e não fazer

- ✅ Copie o alvo para `D:\Dev\REA\lab\targets\` antes de analisar (o REA recusa caminhos mutáveis/sensíveis).
- ✅ Uma pergunta por cartão; o Claude encadeia os cartões.
- ❌ Não analise software sem ter direito de fazê-lo (licença/EULA). Use binários próprios ou do sistema para estudo.
- ❌ Não cole saída bruta enorme no relatório: só o trecho relevante + `evidence_id`.
- ❌ Não diga "build OK"/"encontrei" sem a saída que prove.
