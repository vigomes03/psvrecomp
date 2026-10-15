# W18 — Agrupar memory pools da GPU em janelas de memória (função pura + teste)

## Contexto
O jogo cria centenas de memory pools NVN espalhados por ~11 GB de endereços (dois grupos grandes). O backend
Vulkan importa a memória do convidado em "janelas" contíguas (no máximo 8, cada uma < 4 GB). Precisamos de uma função
pura que, dada a lista de pools, devolva as janelas.

## Entregue: dois arquivos
1. `gwin.c` com a função (sem dependências além de `<stdint.h>`, `<stdlib.h>`, `<string.h>`):
```c
typedef struct { uint64_t base, size; } GwinRange;
// pools: n faixas [base, base+size) quaisquer (desordenadas, podem se sobrepor, size > 0).
// Saída: janelas ordenadas por base, sem sobreposição, cada uma:
//   base alinhada para BAIXO a `align`, fim alinhado para CIMA a `align` (align é potência de 2);
//   cobre todos os pools que caem nela;
// Duas faixas alinhadas se juntam numa janela só se a distância entre elas (início da 2ª - fim da 1ª) for <= gap
// E a janela resultante tiver tamanho <= maxspan. Faixas que se tocam ou se sobrepõem sempre se juntam se couber.
// Um pool que sozinho (alinhado) passe de maxspan vira uma janela própria mesmo assim.
// Retorna o número de janelas escritas em out; se precisaria de mais que maxout, retorna -1.
int gwin_cluster(const GwinRange *pools, int n, uint64_t align, uint64_t gap, uint64_t maxspan,
                 GwinRange *out, int maxout);
```
Algoritmo sugerido: copiar, alinhar cada faixa, ordenar por base (qsort), varrer juntando enquanto as regras deixarem.

2. `test_gwin.c` com `main()` que testa e imprime `PASS n` ou `FAIL <caso>` (retorno 0 só se todos passarem):
| caso | pools (base, size) | align, gap, maxspan, maxout | janelas esperadas (base, size) |
|---|---|---|---|
| vazio | — | 0x4000000, 0x20000000, 0xF0000000, 8 | 0 janelas |
| um | (0x7441c8f000, 0x10000) | 0x4000000, 0x20000000, 0xF0000000, 8 | (0x7440000000, 0x4000000) |
| dois perto | (0x7441c8f000, 0x10000), (0x7449900000, 0x100000) | idem | (0x7440000000, 0xC000000) |
| dois longe | (0x7441c8f000, 0x10000), (0x76c9c00000, 0x1000) | idem | (0x7440000000, 0x4000000), (0x76c8000000, 0x4000000) |
| desordenado | (0x76c9c00000, 0x1000), (0x7441c8f000, 0x10000) | idem | igual ao "dois longe" |
| maxspan | (0x0, 0x1000), (0x10000000, 0x1000) | 0x1000000, 0x20000000, 0x8000000, 8 | (0x0, 0x1000000), (0x10000000, 0x1000000) |
| maxout | 3 pools em 0x0, 0x40000000, 0x80000000 (size 0x1000) | 0x1000000, 0x1000000, 0xF0000000, 2 | retorno -1 |

## Aceite (o Claude roda)
`clang -O2 -Wall gwin.c test_gwin.c -o test_gwin.exe && ./test_gwin.exe` imprime `PASS 7` e retorna 0, sem warnings.
Não invente casos com valores diferentes dos da tabela.
