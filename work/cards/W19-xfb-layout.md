# W19 — Ler o layout de transform feedback da seção de controle do shader NVN (função pura + teste)

## Contexto
Cada vertex shader NVN vem com uma "seção de controle" (bytes gerados pelo compilador glslc). Quando o shader usa
transform feedback (a GPU grava as saídas do vertex shader em buffers), o layout está nesta seção. O Claude descobriu
os campos comparando os 1009 vertex shaders do jogo (28 usam transform feedback). Todos os inteiros são little-endian.

| offset | tipo | significado |
|---|---|---|
| `0x6ED` | u8 | 1 = transform feedback ligado; 0 = desligado (aí nada mais vale) |
| `0x6EC` | u8 | número de buffers usados (1 a 4) |
| `0x6E8 + b` | u8 | 1 = buffer `b` ativo (b = 0..3) |
| `0x6DC + 2*b` | u16 | stride do buffer `b` em bytes |
| `0xDC + 0x80*b` | u8 | saída capturada pelo buffer `b`: `0x20` = saída 0 (v0), `0x21` = saída 1 (v1), ... |
| `0x4DC + 0x80*b` | u8 | quantos componentes (1 a 4, a partir de .x) da saída o buffer `b` captura |

## Entregue: dois arquivos
1. `xfb_layout.c` (só `<stdint.h>` e `<string.h>`), com:
```c
typedef struct {
    uint8_t enabled;       // 0 ou 1
    uint8_t nbuf;          // valor de 0x6EC
    struct {
        uint8_t active;    // 0x6E8 + b
        uint16_t stride;   // 0x6DC + 2*b
        uint8_t output;    // (byte em 0xDC + 0x80*b) - 0x20; 0xFF se o byte for < 0x20
        uint8_t ncomp;     // 0x4DC + 0x80*b
    } buf[4];
} XfbLayout;
// control: ponteiro para a seção de controle (pelo menos 0x700 bytes).
// Desligado: zera *out inteiro e retorna 0. Ligado: preenche os 4 buffers (inativos ficam todos 0) e retorna nbuf.
// Retorna -1 (e zera *out) se ligado mas algo for inválido: nbuf fora de 1..4, buffer ativo com stride 0,
// ncomp fora de 1..4, output 0xFF, ou stride < 4*ncomp.
int xfb_layout_parse(const uint8_t *control, XfbLayout *out);
```
Leia u16 com `memcpy` (não faça cast de ponteiro desalinhado).

2. `test_xfb.c` com `main(int argc, char **argv)`: `argv[1]` é a pasta com os .bin de exemplo. Para cada caso abaixo,
lê o arquivo inteiro (`fopen`/`fread`, modo `"rb"`), chama `xfb_layout_parse` e confere. Imprime `PASS n` ou
`FAIL <arquivo> <campo>` e retorna 0 só se tudo passar. Mais um caso sem arquivo: um buffer de 0x700 bytes zerado,
com `[0x6ED]=1`, `[0x6EC]=1`, `[0x6E8]=1`, stride 0 → deve retornar -1.

| arquivo | retorno | buffers ativos: (stride, output, ncomp) |
|---|---|---|
| `76e62e9c00.bin` | 0 | nenhum (enabled 0) |
| `7442108000.bin` | 1 | b0 (12, 0, 3) |
| `74420fe000.bin` | 1 | b0 (12, 0, 3) |
| `74420fe600.bin` | 2 | b0 (12, 0, 3), b1 (4, 1, 1) |
| `74420fee00.bin` | 3 | b0 (12, 0, 3), b1 (4, 1, 1), b2 (4, 2, 1) |
| `7442120000.bin` | 3 | b0 (12, 0, 3), b1 (12, 1, 3), b2 (12, 2, 3) |

Os buffers não listados devem ter active 0, stride 0, output 0, ncomp 0.

## Aceite (o Claude roda)
`clang -O2 -Wall -Wextra xfb_layout.c test_xfb.c -o test_xfb.exe && ./test_xfb.exe D:/Dev/REA/work/out/W19/ctrl`
imprime `PASS 7` e retorna 0, sem warnings. Não invente offsets nem casos fora destas tabelas.
