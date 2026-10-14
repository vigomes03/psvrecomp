# Fase 2: Runtime mínimo e boot headless

**Objetivo:** o jogo recompilado inicializa e chega ao loop principal **sem gráficos e sem áudio** (as chamadas NVN e de
áudio viram stubs que registram e respondem "ok").

**No Zelda:** `rt.h` (janela fixa de memória `0x70_0000_0000`), `loader.c` (NSO + relocs + símbolos),
`kernel.c` (handles, threads, mutex/condvar por arbitragem, memória, ~50 SVCs), `ipc.c` + `services/`
(20 serviços), `dispatch.c` (cache + busca binária + HLE por nome), `main.c` (boot via `nn::init::Start`).

## Tarefas
- [ ] 2.1 🧠 Janela de memória: o Pokémon precisa de mais heap que o Zelda. Medir no npdm/`SetHeapSize` e ajustar
  `GUEST_HI` (o Windows reserva com `VirtualAlloc` e faz commit sob demanda).
- [ ] 2.2 🧠 Loader com N módulos + `rtld` (ou HLE do rtld como no LAS: `rtld_init_sdk`/`rtld_init_main`).
- [ ] 2.3 🤖 Kernel: completar os SVCs que o jogo chamar e o LAS não implementa (log `[svc] UNIMPLEMENTED 0xNN`
  vira cartão: semântica tirada do Switchbrew + leitura do Eden `src/core/hle/kernel`).
- [ ] 2.4 🤖 Serviços IPC: um cartão por serviço novo (lista da fase 0). Online (`nifm`, `friends`, `bcat`, `npns`,
  `prepo`, `ssl`, `nsd`...) → **stub "sem rede"**. Critério: o jogo segue sem erro fatal.
- [ ] 2.5 🧠 Threads: o Pokémon cria muitas. Validar `ArbitrateLock/Unlock`, `WaitProcessWideKey`,
  `WaitForAddress/SignalToAddress` sob carga (teste de estresse próprio).
- [ ] 2.6 🧠 NVN/áudio em modo stub (registra o nome, devolve sucesso/handles falsos).
- [ ] 2.7 🤖 Log estruturado de boot: sequência de SVCs/IPC; comparar com o log do Eden rodando o mesmo dump.

## Critério de saída (M2)
Log mostra: módulos carregados → `nnMain` → N threads → serviços abertos → loop chamando `nvnQueuePresentTexture`
(stub) repetidamente por 60 s sem `FATAL`.

## Riscos
- Exclusive monitor por compare-and-swap (o LAS faz assim): o padrão ABA pode aparecer com mais threads; observar.
- Serviços com estado complexo (`am`/applet, `hid`) precisam de respostas plausíveis para o jogo não travar esperando.
