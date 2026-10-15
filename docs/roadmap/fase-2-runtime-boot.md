# Fase 2: Runtime mínimo e boot headless

**Objetivo:** o jogo recompilado inicializa e chega ao loop principal **sem gráficos e sem áudio** (as chamadas NVN e de
áudio viram stubs que registram e respondem "ok").

**No Zelda:** `rt.h` (janela fixa de memória `0x70_0000_0000`), `loader.c` (NSO + relocs + símbolos),
`kernel.c` (handles, threads, mutex/condvar por arbitragem, memória, ~50 SVCs), `ipc.c` + `services/`
(20 serviços), `dispatch.c` (cache + busca binária + HLE por nome), `main.c` (boot via `nn::init::Start`).

## Tarefas
- [x] 2.1 🧠 Janela de memória (boot run_id=6ea004c868): `GUEST_HI` = 0x80_0000_0000, alias region 48 GiB em
  0x74_0000_0000. O `nninitStartup` do jogo cria `StandardAllocator(nullptr, 12 GiB)` sobre a VAMM do nn::os
  (`GetInfo(16)` != 0 + `MapPhysicalMemory`, que não pode zerar páginas já mapeadas).
- [x] 2.2 🧠 Loader com N módulos + HLE do rtld (boot run_id=6ea004c868). Bases e build ids vêm do `pvgame.dll`
  (`layout.py --header`): o host recusa um exefs de outra versão. Todos os DT_INIT rodam em x3 (depois do
  `nninitStartup`), porque os construtores do sdk chamam o `malloc` do jogo, que usa TLS do main.
- [ ] 2.3 🤖 Kernel: completar os SVCs que o jogo chamar e o LAS não implementa (log `[svc] UNIMPLEMENTED 0xNN`
  vira cartão: semântica tirada do Switchbrew + leitura do Eden `src/core/hle/kernel`).
- [ ] 2.4 🤖 Serviços IPC: um cartão por serviço novo (lista da fase 0). Online (`nifm`, `friends`, `bcat`, `npns`,
  `prepo`, `ssl`, `nsd`...) → **stub "sem rede"**. Critério: o jogo segue sem erro fatal.
- [ ] 2.5 🧠 Threads: o Pokémon cria muitas. Validar `ArbitrateLock/Unlock`, `WaitProcessWideKey`,
  `WaitForAddress/SignalToAddress` sob carga (teste de estresse próprio).
- [ ] 2.6 🧠 NVN/áudio em modo stub (registra o nome, devolve sucesso/handles falsos).
- [ ] 2.7 🤖 Log estruturado de boot: sequência de SVCs/IPC; comparar com o log do Eden rodando o mesmo dump.

## Estado (14/10)
Boot real, v1.0.0 (run_id=6ea004c868) e v4.0.0 (run_id=e56d4aa1d1): os 3 módulos carregam, os ~2.100 construtores
do `main` rodam, o `nnMain` abre `time:u`/`hid`/`fsp-srv`, lê o romfs (`dumps/<v>/romfs.bin`) e cria ~12 threads.
Para no `NvOsDrvOpen` (a NVN do SDK tenta abrir o driver da GPU via `nvdrv`): é a tarefa 2.6.
Foi preciso: TIPC no IPC (o `sm:` do SDK 13 não usa mais CMIF) e a ordem dos DT_INIT acima.

## Critério de saída (M2)
Log mostra: módulos carregados → `nnMain` → N threads → serviços abertos → loop chamando `nvnQueuePresentTexture`
(stub) repetidamente por 60 s sem `FATAL`.

## Riscos
- Exclusive monitor por compare-and-swap (o LAS faz assim): o padrão ABA pode aparecer com mais threads; observar.
- Serviços com estado complexo (`am`/applet, `hid`) precisam de respostas plausíveis para o jogo não travar esperando.
