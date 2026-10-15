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
  Feitos em 14/10: `pl:u` (fontes compartilhadas, cartão W05, gate pl run_id=c25dcb8f3b), `csrng`, `btm:u` + `IBtmUserCore`.
- [ ] 2.5 🧠 Threads: o Pokémon cria muitas. Validar `ArbitrateLock/Unlock`, `WaitProcessWideKey`,
  `WaitForAddress/SignalToAddress` sob carga (teste de estresse próprio).
  Corrigidos em 14/10, todos herdados do kernel do LAS e diferentes do Horizon:
  (a) no timeout, `WaitProcessWideKeyAtomic` NÃO readquire o mutex (quem readquire é o nn::os/libnx);
  (b) `block_current` sobrescrevia com timeout um wake que chegou junto; (c) mutex/condvar consumiam o
  `CancelSynchronization` destinado ao próximo `WaitSynchronization`. **Ainda aberto:** o boot trava
  de forma intermitente entre 16 e 512 frames, nas duas versões; a thread principal fica em `WaitAny` com 0 handles.
  Para investigar, use `PVR_DUMP_THREADS=1`.
  **Resolvido em 14/10 (qwen, cartões com referências):**
  - W06 (d): a key do condvar agora é gravada ANTES de liberar o mutex. O `Signal` do nn::os só chama o kernel se
    key ≠ 0. Referência: Eden `k_condition_variable.cpp` Wait. host v400 run_id=8574b2a012.
  - W07: comandos NVN grandes são divididos em pedaços que cabem nos chunks de 1024 B do jogo.
    gate cmdbuf_split run_id=dd87dec48f.
  - W08: o mapa de memória virou um mapa de intervalos (split/merge). A lista antiga estourava em
    "too many regions" com a VAMM. gate regions run_id=4054feb2b8.
- [x] 2.6 🧠 NVN/áudio em modo stub: backend NVN nulo (W03, gate nvn_null run_id=2c624c489d) + SDL de áudio nulo
  (W04, gate sdl_null run_id=7bcb24a69b). Boot com frames: base run_id=6c576b773b (`present #64`) e
  v400 run_id=e796f17e2a (`frame_presented`).
- [ ] 2.7 🤖 Log estruturado de boot: sequência de SVCs/IPC; comparar com o log do Eden rodando o mesmo dump.

## Estado (14/10, fim do dia)
Nas duas versões o boot chega a apresentar frames pelo backend NVN nulo: base `present #64` (run_id=6c576b773b) e v400
`frame_presented` (run_id=e796f17e2a). O ponto de parada varia de 16 a 512 frames (ver 2.5).
O que foi preciso:
- **setjmp/longjmp do guest.** O código recompilado chama funções como C, e o `longjmp` volta para o meio de
  uma função. Agora o `gen.py` gera um checkpoint (`setjmp` do CRT) em cada `bl setjmp`, e o `runtime/setjmp.c`
  faz a HLE do `longjmp`. O `__builtin_setjmp` do clang não serve no Win64 (restaura o rbp errado).
- **`SamplerBuilder` compactado.** Cabe nos 0x40 bytes que o jogo reserva na pilha; antes, `SetBorderColor` sobrescrevia x29/x30.
- **`GetInfo(20)`** (UserExceptionContextAddress) passou a devolver uma página válida.
- **`HOST()` da NVN** passou a aceitar NULL (`BindProgram(cb, NULL)`).

Ferramentas novas:
- `recomp/disas.py`;
- `recomp/regen_changed.sh` (regera e recompila só os chunks que mudaram);
- `PVR_GEN_PCLINES=1` (`#line` com o PC do guest, para o addr2line);
- `PVR_TRACE_HLE=1`;
- `PVR_DUMP_THREADS=1`.

Critério M2 (60 s de `present` sem FATAL), medido com `--min-stage frames_60,survived_time_limit --repeat 4`:
- **base v1.0.0: atingido, 4 de 4** (`present #1024` em cada uma), run_id=977d5ee1c3;
- **v4.0.0: 3 de 4** (run_id=1e0e69e1fc FAIL). A rodada 2 caiu com `c0000005 accessing 0x58` dentro do código do
  jogo (main 0x700160be6c, chamado de 0x7000d2ff7c), depois de 512 frames. É o próximo item de estudo.
Atenção: até 14/10, `frames_60` passava sem nenhum frame quando o jogo só sobrevivia até o limite de tempo. O
`stage_ok` do gates.py corrige isso e tem teste.

## Critério de saída (M2)
Log mostra: módulos carregados → `nnMain` → N threads → serviços abertos → loop chamando `nvnQueuePresentTexture`
(stub) repetidamente por 60 s sem `FATAL`.

## Riscos
- Exclusive monitor por compare-and-swap (o LAS faz assim): o padrão ABA pode aparecer com mais threads; observar.
- Serviços com estado complexo (`am`/applet, `hid`) precisam de respostas plausíveis para o jogo não travar esperando.
