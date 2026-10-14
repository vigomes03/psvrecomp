# Fase 0: Aquisição e reconhecimento

**Objetivo:** ter o código e os dados do jogo extraídos (base + update) e saber **com o que estamos lidando**
antes de escrever uma linha do recompilador. Essa fase decide a escala de todo o resto.

**No Zelda:** o usuário fornece `extracted/exefs` e `romfs`; `tools/nso.py` lê o NSO e `tools/analyze.py`
faz o censo de funções e instruções.

## Tarefas

### 0.1 Chaves e extração 🧠 (com o [USER])
- [ ] `prod.keys`/`title.keys` do console do [USER] (Lockpick_RCM) em `keys/` (ignorado)
- [ ] `hactool` no XCI → partição `secure` → identificar o NCA de Program (base 1.0.0)
- [ ] Extrair `exefs` (main, sdk, subsdk*, rtld, main.npdm) → `dumps/base/exefs/`
- [ ] Extrair `romfs` → `dumps/base/romfs/`
- [ ] Dump do **update** (NSP do [USER]): aplicar o patch (BKTR) com hactool `--basenca` → `dumps/update/`
- [ ] Anotar: versão do jogo, Title ID, **build id** de cada NSO, versão do SDK (string `NintendoSdk_*` no rodapé do NSO)

**Decisão:** recompilar **uma versão só** (provavelmente a última do update), porque endereços, patches e hooks são por build id.

### 0.2 Inventário do executável 🤖 (cartões de script) + 🧠 revisão
- [ ] Rodar o `nso.py` do LAS sobre cada NSO: tamanho de `.text/.rodata/.data/.bss`, `MOD0`, imports/exports
- [ ] Contar funções: `.eh_frame_hdr` × símbolos × alvos de BL (`analyze.py`)
- [ ] **Símbolos:** quantos `STT_FUNC` com nome? (o `main` tem nomes ou só o SDK?)
- [ ] Censo de instruções: % FP/SIMD, instruções raras (LSE atomics? ARMv8.1+? o lifter do LAS cobre ARMv8.0 + crypto + CRC32)
- [ ] Lista de **middleware** por strings (Havok? Wwise/CRI? Pia (rede)? FlatBuffers?) e por `subsdk*`
- [ ] Lista de **serviços IPC** usados (strings `"fsp-srv"`, `"nifm:u"`...), a lista de trabalho da fase 2
- [ ] Lista de funções **NVN** importadas (`nvn*` via `nvnBootstrapLoader`), a lista de trabalho da fase 4
- [ ] Inventário do romfs: extensões, tamanhos, `*.trpfs`/`*.trpfd` (arquivos-pacote da Game Freak)

### 0.3 Primeira visão no Ghidra/REA 🤖 (rea_worker) + 🧠
- [ ] Carregar `main` (ELF convertido do NSO, ou loader de NSO do Ghidra) e conferir que o REA consegue analisar
  um binário desse tamanho (tempo, RAM). Se não der na CLI (20 s por chamada × reimport), usar sessão MCP.
- [ ] Achar `nnMain`, o loop principal e as threads criadas na inicialização

### 0.4 Referência de comportamento 🧠
- [ ] Compilar/rodar o **Eden** com o mesmo dump (precisa das chaves): confirma que o dump está íntegro e dá um
  oráculo de "como deveria ser" (logs de SVC/IPC do Eden vs os nossos)

## Saída / critério (M0)
`docs/roadmap/achados-fase-0.md` com: versões, build ids, tamanhos, nº de funções, cobertura de símbolos, % SIMD,
middleware, serviços, funções NVN, formatos do romfs. Com isso a gente revisa as fases 1 a 4 (tempo e ordem).

## Riscos
- `.text` gigante → tempo de geração (Python) e compilação: medir já aqui (gerar só 1% e cronometrar).
- Instruções fora do ARMv8.0 → o lifter precisa crescer.
