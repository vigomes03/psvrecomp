# Ambiente do workspace REA (verificado em 14/10/2026)

Máquina: Windows 11, RTX 3070 Ti 8 GB, 32 GB RAM, C: quase cheio, então **tudo vai no D:**.

## Ferramentas instaladas

| Ferramenta | Caminho | Para quê | Verificação |
|---|---|---|---|
| REA (snapshot do `main`, v6.4.0) | `D:\Dev\REA\ref\rea-main\rea-main` | RE via CLI/MCP | `rea doctor --provider ghidra` verde |
| Addon nativo Windows do REA | `ref\rea-main\rea-main\native\windows\build` | Ghidra no Windows exige | `npm run verify:windows-native:artifact` |
| Ghidra 12.1.4 | `D:\Tools\ghidra_12.1.4_PUBLIC` (`GHIDRA_INSTALL_DIR`) | decompilação | ✅ |
| Temurin JDK 21 | `D:\Tools\jdk-21.0.12.1+1` (`JAVA_HOME`) | Ghidra | ✅ |
| MinGW-w64 (WinLibs GCC 16.2) | `D:\Tools\mingw64` | compilar o addon do REA | ✅ |
| MSYS2 UCRT64 (clang 23, lld, make, SDL3, FFmpeg, Vulkan, shaderc, SPIRV-Tools, gdb) | `D:\msys64` | compilar LASRecomp / código nativo | ✅ `lasrecomp.exe` compila e abre |
| Python 3.12 (uv) + unicorn 2.1.4, capstone 5.0.9, lz4 | `ref\LASRecomp-main\...\tools\venv` | lifter / testes diferenciais | `test_simd.py` registrado no pipeline de 14/10 (0 falhas) |
| Zig 0.17.0 | `ref\LASRecomp-main\...\build\zig` | `zig cc` | hash registrado em `docs/pipeline-log.md` |
| hactool (SciresM, `1d64a83`, compilado do fonte com WinLibs) | `D:\Tools\hactool\hactool.exe` (fonte em `D:\Tools\src\hactool`) | ler/extrair XCI/NCA/RomFS | ✅ lê o cabeçalho do XCI sem chaves |
| Ollama + `qwen3-coder-64k` | serviço local `127.0.0.1:11434` | worker local | ✅ |

## Recompilar o addon nativo do REA (se `native/windows/src` mudar)
O artefato do npm 6.4.0 **não serve** para este snapshot (`privateBridgeDescriptorAccess`).
1. PATH com `D:\Tools\mingw64\bin` na frente; existem cópias `x86_64-w64-mingw32-dlltool.exe` e `x86_64-w64-mingw32-as.exe`.
2. `node --import <arquivo que faz Object.defineProperty(process,'platform',{value:'linux'})> scripts/build-windows-native.mjs`
3. `npm run verify:windows-native:artifact`

## Armadilhas conhecidas
- **`TMP=/tmp` quebra o REA.** Com o MSYS2 na frente do PATH, `TMP`/`TEMP` viram `/tmp`, e o self-test nativo falha
  (`Create private object relative to its admitted parent`). `tools/rea/rea.sh` e `rea_worker.py` já forçam o Temp do Windows.
- **Não deixe o MSYS2 permanentemente no PATH do terminal**: exporte só no comando que compila.
- REA MCP completo = 207 ferramentas (~220k tokens). No Hermes, `tools.include` com 21 ferramentas + `compact` (~8k).
- Cada chamada CLI do REA reimporta no Ghidra (~20 s). A sessão MCP mantém o Ghidra aberto.
- Janelas de teste não rodam sob `timeout` do MSYS: use Python `subprocess` com `timeout`.
- **`make` do MSYS2 + gcc nativo perde o `TMP`** (gcc: `Cannot create temporary file in C:\WINDOWS\`). Para projetos com Makefile simples use o `mingw32-make` do WinLibs, com `TMP` apontando para o Temp do Windows.
- Variáveis de usuário gravadas com `setx`: `GHIDRA_INSTALL_DIR`, `JAVA_HOME`.

## Runtime em janela (PSV Recomp, Vulkan) — verificado em 15/10/2026
- Build: `bash "psvrecomp/recomp/build_host.sh" /d/Dev/REA/lab/host-vk vulkan` (clang/SDL3/shaderc do
  `D:\msys64\ucrt64`, só dentro do comando). Saída `lab/host-vk/pvhost.exe` + `pvgame.dll`.
- `recomp/run_window.cmd` põe `D:\msys64\ucrt64\bin` no PATH (DLLs SDL3, shaderc, libstdc++), limpa as variáveis de
  debug e abre a janela no monitor 2 (`PVR_DISPLAY`). `tools/verify/run_auto.sh` é a versão do pipeline.
- GPU: RTX 3070 Ti, Vulkan 1.3. Desempenho medido pelo [USER] em 15/10: 5-10 fps em interiores, ~3 fps em área aberta,
  CPU ~9 %, GPU quase ociosa (gargalo no lado do CPU/sincronização, não na placa).

## Ainda NÃO instalado (próximo passo para o projeto Pokémon)
- **Chaves**: `prod.keys` (e `title.keys`, se houver) tiradas do **seu** console com Lockpick_RCM →
  colocar em `D:\Dev\REA\keys\` (ignorado pelo git). Sem elas, o hactool só lê o cabeçalho do XCI.
- ROM/dump: `roms/Pokémon Violet.xci`, cartucho 8 GB; partições `update` (225 arquivos, firmware), `logo`, `normal` (vazia),
  `secure` (o jogo, NCAs criptografados). Extração vai para `dumps/` (ignorado).
- Formatos de asset da Game Freak (TRPAK/FlatBuffers etc.) ainda sem ferramenta escolhida.
