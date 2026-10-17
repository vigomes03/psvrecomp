# Achados: fase 0 (aquisição)

> Só metadados (nomes, tamanhos, IDs). Nenhum conteúdo do jogo.

## Arquivos das ROMs (`roms/`, privado, ignorado)

| Arquivo | Tamanho | O quê |
|---|---:|---|
| `roms/Pokémon Violet.xci` | 7.985.954.816 | cartucho 8 GB, jogo base (v1.0.0 presumido ❓) |
| `roms/Pokémon Violet v4.0.0.nsp` | 5.235.895.884 | update **v4.0.0** (liberado pelo [USER] em 16/10: base do recomp e do Eden de referência) |
| `roms/The Legend of Zelda Links Awakening [01006BB00C6F0000][v0].nsp` | 6.274.802.512 | Zelda LA v1.0.0. ⛔ **NÃO USAR** até confirmar que veio do console/compra do [USER] |

**Decisão (14/10, revista em 16/10):** base = **cartucho v1.0.0** do console do [USER]; o update **v4.0.0** foi liberado
pelo [USER] e é a versão de trabalho. Zelda continua só depois de confirmada a origem.

## XCI (lido sem chaves) ✅
Partições HFS0: `update` (225 arquivos, firmware do cartucho), `logo`, `normal` (vazia), `secure` (o jogo, NCAs criptografados).

## NSP do update (lido sem chaves) ✅
- Title ID **`01008F6008C5E800`** (update do Violet; base = `01008F6008C5E000`)
- Conteúdo: `.cert`, `.tik` (ticket com title key), 4 NCAs + `cnmt.nca`/`cnmt.xml`
- NCA maior `d24a763a…` ≈ 5,2 GB: patch do programa (exefs novo + romfs em BKTR sobre o base)

## Extração da v1.0.0 (cartucho) ✅ 14/10
- Chaves: `keys/prod.keys` do console do [USER]. O hactool (2023) aborta com o arquivo inteiro (`master_kek_source_*` com
  34 caracteres), então usamos `keys/game.keys`, gerado com só 111 chaves de conteúdo (`header_key`, `master_key_*`,
  `key_area_key_*`, `titlekek_*`), **nenhuma por-console**. Ambos ignorados pelo git.
- ⚠️ Lição: o hactool imprime **valores** de chaves nos avisos `Failed to match key`. Sempre filtrar a saída
  (`sed -E 's/[0-9A-Fa-f]{32,}/<oculto>/g'` + `grep -v 'Failed to match key'`).
- `secure`: NCAs Program (6,7 GB), Control, Meta, 2× Manual; Title ID `01008F6008C5E000`.
- Saída em `dumps/base/` (ignorado): `exefs/` e `romfs/` (6,3 GB, só **24 arquivos**).

## Inventário do executável ✅ (`recomp/nso.py` + `analyze.py`)

| Módulo | build id (16) | .text | .rodata | .data | .bss | funções (`.eh_frame`) | com nome | imports |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `main` | `959ed651bf1ae0cc` | **48,1 MB** | 15,6 MB | 3,4 MB | 0,8 MB | **172.011** | **33** | 956 |
| `sdk` | `3644a6760469451c` | 5,8 MB | 6,7 MB | 0,4 MB | 0,7 MB | 30.320 | 23.656 | 14 |
| `subsdk0` | `d0f13015e5badf22` | 3,2 MB | 2,1 MB | 0,2 MB | 1,1 MB | 9.831 | 8.781 | 660 |

- SDK: `NintendoSdk_nnSdk-13_3_5-Release`.
- **`main` é praticamente sem símbolos** (33 nomes em 172 mil funções). O SDK e o `subsdk0` têm nomes (bom para HLE).
  Os limites de função vêm do `.eh_frame`, então a recompilação funciona igual. A dificuldade está em **entender**
  o jogo (fase 7/9): todo nome será descoberto por RE.
- `subsdk0` = biblioteca multimídia da Nintendo (`nn::movie`, codecs de origem Android, mkvparser, Opus/SILK).
- 📖 Middleware no `main` (contagem de strings; ❓ confirmar): **Wwise** (áudio; `romfs/audio/wwise/.../Stream.pck` 930 MB,
  `PM.bnk`), **Havok** (prefixo `hk*`), **Pia** (rede da Nintendo), **Bink 2** (vídeos `.bk2` em `demo/movie`).
- romfs: `arc/data.trpfs` **5,15 GB** (pacote único de assets) + `arc/data.trpfd` 11 MB (índice), áudio Wwise, vídeos Bink.

### Comparação de escala com o Zelda (❓ falta medir o Zelda com dump próprio)
172k funções em 48 MB de `.text`. Estimativa: C gerado na ordem de **vários GB**. A fase 1.6 (medir 1% e extrapolar)
passa a ser prioridade.

## Pendências
- [x] `keys/prod.keys` (Lockpick_RCM no console do [USER])
- [x] Decisão de versão: **v1.0.0 do cartucho** (trocar para o update depois = refazer a geração, não o projeto)
- [x] Update v4.0.0 liberado pelo [USER] (16/10)
- [ ] Teste de pipeline com o Zelda **se** o [USER] tiver o jogo (dump próprio)
