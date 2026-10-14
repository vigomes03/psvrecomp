# Achados: fase 0 (aquisição)

> Só metadados (nomes, tamanhos, IDs). Nenhum conteúdo do jogo.

## Arquivos do dump (`Pokémon Violet/`, privado, ignorado)

| Arquivo | Tamanho | O quê |
|---|---:|---|
| `Pokémon Violet.xci` | 7.985.954.816 | cartucho 8 GB, jogo base (v1.0.0 presumido ❓) |
| `Pokémon Violet v4.0.0.nsp` | 5.235.895.884 | update **v4.0.0** |
| `The Legend of Zelda Links Awakening [01006BB00C6F0000][v0].nsp` | 6.274.802.512 | Zelda LA v1.0.0: serve para testar o pipeline do LAS Recomp ponta a ponta |

## XCI (lido sem chaves) ✅
Partições HFS0: `update` (225 arquivos, firmware do cartucho), `logo`, `normal` (vazia), `secure` (o jogo, NCAs criptografados).

## NSP do update (lido sem chaves) ✅
- Title ID **`01008F6008C5E800`** (update do Violet; base = `01008F6008C5E000`)
- Conteúdo: `.cert`, `.tik` (ticket com title key), 4 NCAs + `cnmt.nca`/`cnmt.xml`
- NCA maior `d24a763a…` ≈ 5,2 GB: patch do programa (exefs novo + romfs em BKTR sobre o base)

## Pendências
- [ ] `keys/prod.keys` (Lockpick_RCM no console do [USER]): **bloqueia o resto da fase 0**
- [ ] Decisão de versão: recompilar a **v4.0.0** (última, exefs do update) ← proposta
- [ ] Teste de pipeline: rodar o LAS Recomp com o Zelda NSP (`make gen` → jogo rodando) antes de adaptar ao Pokémon
