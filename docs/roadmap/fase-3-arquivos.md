# Fase 3: Sistema de arquivos e dados do jogo

**Objetivo:** o jogo lê os próprios arquivos (romfs base + update) pelo serviço `fsp-srv`, exatamente como no console.
**O jogo** interpreta os formatos; nós só servimos bytes. Parsers próprios são para estudo/mods (fase 9).

**No Zelda:** `services/fs.c` serve o romfs extraído; `romfs_build.c` monta um romfs com os arquivos trocados pela
seed (layering). Saves em pasta própria.

## Tarefas
- [ ] 3.1 🧠 Decidir: servir o **romfs extraído** (pasta, simples, como o LAS) ou ler o **NCA direto** (sem
  extrair 7+ GB). Começar com a pasta.
- [ ] 3.2 🤖 Layering base + update: arquivo do update sobrepõe o da base (`dumps/update/romfs` por cima de `base`).
- [ ] 3.3 🤖 `fsp-srv`: `OpenFileSystemWithPatch`/`OpenDataStorageByCurrentProcess`, `IStorage::Read` grande,
  leituras **assíncronas/paralelas** (streaming do mundo aberto): medir latência.
- [ ] 3.4 🤖 Save data: `OpenSaveDataFileSystem` → `save/` local, com commit atômico.
- [ ] 3.5 🤖 (Estudo, paralelo) Parser de `trpfd`/`trpfs` em Python para **listar** o conteúdo (nomes/hashes),
  com o critério "lista bate com o que o jogo pede no log do `fsp-srv`".

## Critério de saída
Log de `fsp-srv`: todo arquivo pedido no boot é achado; nenhum `PathNotFound` inesperado; save cria e lê.

## Riscos
- Hash de nome em vez de caminho dentro do `trpfs`: irrelevante para rodar (o jogo resolve), relevante para estudar.
