# W01: helpers C para exclusivos em par de 64 bits (LDXP/LDAXP/STXP/STLXP)

## Objetivo
Escrever o arquivo `runtime/excl_pair.h` com 4 funções `static inline` que emulam os acessos exclusivos em par
(128 bits) do AArch64 no PC x86-64, no mesmo estilo dos exclusivos simples que já existem em `cpu.h`.

## API que JÁ EXISTE (não declare de novo; inclua "cpu.h")
```c
typedef struct Cpu {
    uint64_t x[32]; uint64_t sp; uint64_t pc; uint64_t nzcv; uint64_t tpidr; uint64_t tpidrro;
    uint64_t excl_addr;     // endereço reservado pelo último load exclusivo; ~0ull = sem reserva
    uint64_t excl_val;      // valor lido pelo load exclusivo (metade BAIXA, bytes a..a+7)
    void *thread; uint64_t fpcr; uint64_t fpsr;
    uint64_t excl_val_hi;   // metade ALTA (bytes a+8..a+15)
    ...
} Cpu;
```
Padrão existente para 64 bits (copie a lógica, não o macro):
```c
static inline uint64_t ldx64(Cpu *c, uint64_t a) {
    uint64_t v = __atomic_load_n((uint64_t *)(uintptr_t)a, __ATOMIC_ACQUIRE);
    c->excl_addr = a; c->excl_val = v; return v; }
static inline uint32_t stx64(Cpu *c, uint64_t a, uint64_t v) {
    if (c->excl_addr != a) return 1;
    c->excl_addr = ~0ull;
    uint64_t expected = c->excl_val;
    return !__atomic_compare_exchange_n((uint64_t *)(uintptr_t)a, &expected, v, 0, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST); }
```

## O que escrever (exatamente estas 4 assinaturas)
```c
#pragma once
#include "cpu.h"
// load exclusivo em par: *lo = mem[a..a+7], *hi = mem[a+8..a+15]; reserva o monitor
static inline void ldxp64(Cpu *c, uint64_t a, uint64_t *lo, uint64_t *hi);
// igual, com semântica acquire (LDAXP)
static inline void ldaxp64(Cpu *c, uint64_t a, uint64_t *lo, uint64_t *hi);
// store exclusivo em par: devolve 0 se gravou lo/hi, 1 se falhou (reserva diferente ou memória mudou)
static inline uint32_t stxp64(Cpu *c, uint64_t a, uint64_t lo, uint64_t hi);
// igual, com semântica release (STLXP)
static inline uint32_t stlxp64(Cpu *c, uint64_t a, uint64_t lo, uint64_t hi);
```
Regras:
- Use `unsigned __int128` e `__atomic_load_n` / `__atomic_compare_exchange_n` de 16 bytes (o endereço é alinhado a 16).
- Valor de 128 bits = `(unsigned __int128)hi << 64 | lo` (little-endian: `lo` fica no endereço menor).
- No load: `c->excl_addr = a; c->excl_val = lo; c->excl_val_hi = hi;`.
- No store: se `c->excl_addr != a` devolve 1 sem gravar; senão zera a reserva (`c->excl_addr = ~0ull`) e faz CAS
  comparando com `(excl_val_hi, excl_val)`; devolve 0 se o CAS gravou, 1 se não.
- Nada além das 4 funções e do `#pragma once` / `#include`.

## Aceite (o Claude roda)
1. Compila com `clang -O1 -march=x86-64-v3` sem warnings, e **sem** depender de `libatomic` (link de um teste sem `-latomic`).
2. Teste: `ldxp64` lê os dois valores certos; `stxp64` logo depois devolve 0 e grava; segundo `stxp64` sem novo load
   devolve 1; `stxp64` após outra thread mudar a memória devolve 1 e não grava.
