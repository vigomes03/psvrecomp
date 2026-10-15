#!/usr/bin/env bash
# Boot run: link pvgame.dll (generated objects of one dump version + pvgame_entry with that version's layout) against
# the runtime import library (pvhost.dll.a from build_host.sh), then run pvhost.exe headless. Log -> <host_dir>/boot.log
# Usage: run_boot.sh <gen_dir> <host_dir> [seconds] [version]     version = dumps/<version> (base | v400), default base
set -u
G=$(cygpath -m "${1:?gen dir}"); H=$(cygpath -m "${2:?host dir}"); SECS=${3:-60}; VER=${4:-base}
EXEFS=D:/Dev/REA/dumps/$VER/exefs; ROMFS=D:/Dev/REA/dumps/$VER/romfs
P="D:/Dev/REA/Pokemon Decompile"
export PATH="/d/msys64/ucrt64/bin:$PATH"
export TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"
"$P/recomp/venv/Scripts/python.exe" "$P/recomp/layout.py" "$EXEFS" --header "$H/layout_gen.h" --version "$VER" || exit 1
clang -O1 -march=x86-64-v3 -fvisibility=hidden -I"$H" -I"$P/runtime" -c "$P/recomp/pvgame_entry.c" -o "$H/pvgame_entry.o" || exit 1
ls "$G"/obj/*.o "$G"/obj_subsdk0/*.o "$G"/obj_sdk/*.o | sed 's/.*/"&"/' > "$H/objs.rsp"
echo "\"$H/pvgame_entry.o\"" >> "$H/objs.rsp"
rm -f "$H/pvgame.dll"
clang -shared -fuse-ld=lld -Wl,-Map,"$H/pvgame.map" -o "$H/pvgame.dll" @"$H/objs.rsp" "$H/pvhost.dll.a" || exit 1
echo "pvgame.dll linked ($(du -h "$H/pvgame.dll" | cut -f1), $VER); running ${SECS}s headless..."
cd "$H" && PVR_SYSFONT_DIR="${PVR_SYSFONT_DIR:-D:/Dev/REA/lab/sysfont}" PVR_RUN_SECONDS=$SECS ./pvhost.exe "$EXEFS" "$ROMFS" > boot.log 2>&1
echo "exit=$?  log lines: $(wc -l < boot.log)"
