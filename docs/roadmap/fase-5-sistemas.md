# Fase 5: Áudio, input, save e tempo

**No Zelda:** `services/audio.c` (audren/audout → SDL3), `hle/input.c` (`nn::hid::GetNpadState*` por HLE: teclado e
controle via SDL3, remapeáveis), `services/time.c`, `hid_set.c`, `acc.c`, `am.c`, `movie.c` (vídeos com FFmpeg).

## Tarefas
- [ ] 5.1 🤖 Áudio: `audren:u` (renderer de áudio do Switch) → mixer próprio → SDL3. Se o jogo usar middleware de
  áudio (fase 0), ele roda **dentro** do código recompilado; só o renderer é nosso.
- [ ] 5.2 🤖 Input: HLE de `nn::hid` (Npad Pro Controller/Handheld), teclado + controle Xbox/PS via SDL3; mapeamento
  configurável. Giroscópio/vibração: stub.
- [ ] 5.3 🤖 Vídeos (se houver `.mp4`/`.usm` no romfs): FFmpeg como no LAS.
- [ ] 5.4 🤖 Tempo/relógio (`time:u/a/s`): o relógio do jogo (dia/noite) segue o relógio do PC.
- [ ] 5.5 🤖 Conta/usuário (`acc:u0`): um usuário local fixo; `am`/applet: foco, modo portátil/dock (resolução).
- [ ] 5.6 🧠 Teclado de software (`swkbd`) para nomear personagem/Pokémon: HLE com caixa de texto própria (o LAS tem `hle/swkbd.c`).

## Estado em 15/10 (revisão com o [USER])
- 🟢 5.2 input: teclado e controle (Npad HLE em `hle/input.c`), confirmado pelo [USER].
- 🔴 5.1 áudio: **silêncio total** na janela. Vem depois do desempenho.
- 🔴 5.6 swkbd: sem teclado o jogo segue com um nome padrão (`?瑱?` na ficha de matrícula).

## Critério de saída
Música e efeitos na tela de título; menu navegável com controle; nomear personagem funciona; save persiste entre execuções.
