#!/usr/bin/env bash
# Fase 2 boot run: link pvgame.dll against the real runtime (pvhost.dll.a from build_host.sh), then run pvhost.exe
# headless on the extracted game. Log -> <host_dir>/boot.log
# Usage: run_boot.sh <genfull_dir> <host_dir> [seconds]
set -u
G=$(cygpath -m "${1:?genfull dir}"); H=$(cygpath -m "${2:?host dir}"); SECS=${3:-60}
EXEFS=D:/Dev/REA/dumps/base/exefs; ROMFS=D:/Dev/REA/dumps/base/romfs
P="D:/Dev/REA/Pokemon Decompile"
export PATH="/d/msys64/ucrt64/bin:$PATH"
export TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"
clang -O1 -march=x86-64-v3 -fvisibility=hidden -I"$P/runtime" -c "$P/recomp/pvgame_entry.c" -o "$H/pvgame_entry.o" || exit 1
ls "$G"/obj/*.o "$G"/obj_subsdk0/*.o "$G"/obj_sdk/*.o | sed 's/.*/"&"/' > "$H/objs.rsp"
echo "\"$H/pvgame_entry.o\"" >> "$H/objs.rsp"
clang -shared -fuse-ld=lld -Wl,-Map,"$H/pvgame.map" -o "$H/pvgame.dll" @"$H/objs.rsp" "$H/pvhost.dll.a" || exit 1
echo "pvgame.dll linked ($(du -h "$H/pvgame.dll" | cut -f1)); running ${SECS}s headless..."
cd "$H" && PVR_RUN_SECONDS=$SECS ./pvhost.exe "$EXEFS" "$ROMFS" > boot.log 2>&1
echo "exit=$?  log lines: $(wc -l < boot.log)"
