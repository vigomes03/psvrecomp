# Achados: fase 0 (aquisição)

> Só metadados (nomes, tamanhos, IDs). Nenhum conteúdo do jogo.

## Arquivos do dump (`Pokémon Violet/`, privado, ignorado)

| Arquivo | Tamanho | O quê |
|---|---:|---|
| `Pokémon Violet.xci` | 7.985.954.816 | cartucho 8 GB, jogo base (v1.0.0 presumido ❓) |
| `Pokémon Violet v4.0.0.nsp` | 5.235.895.884 | update **v4.0.0**. ⛔ **NÃO USAR**: baixado da internet, não dumpado do console |
| `The Legend of Zelda Links Awakening [01006BB00C6F0000][v0].nsp` | 6.274.802.512 | Zelda LA v1.0.0. ⛔ **NÃO USAR** até confirmar que veio do console/compra do [USER] |

**Decisão (14/10):** trabalhamos só com o que veio do console do [USER]. Base = **cartucho v1.0.0**. Update e Zelda
só depois de dumpados com nxdumptool/DBI do próprio Switch (atualizar o jogo pelo console → dumpar o update instalado).

## XCI (lido sem chaves) ✅
Partições HFS0: `update` (225 arquivos, firmware do cartucho), `logo`, `normal` (vazia), `secure` (o jogo, NCAs criptografados).

## NSP do update (lido sem chaves) ✅
- Title ID **`01008F6008C5E800`** (update do Violet; base = `01008F6008C5E000`)
- Conteúdo: `.cert`, `.tik` (ticket com title key), 4 NCAs + `cnmt.nca`/`cnmt.xml`
- NCA maior `d24a763a…` ≈ 5,2 GB: patch do programa (exefs novo + romfs em BKTR sobre o base)

## Pendências
- [ ] `keys/prod.keys` (Lockpick_RCM no console do [USER]): **bloqueia o resto da fase 0**
- [x] Decisão de versão: **v1.0.0 do cartucho** (trocar para o update depois = refazer a geração, não o projeto)
- [ ] Update v4.0.0 dumpado do console (nxdumptool/DBI), opcional
- [ ] Teste de pipeline com o Zelda **se** o [USER] tiver o jogo (dump próprio)
