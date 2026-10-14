#!/usr/bin/env bash
# M1 link check: build m1_host.exe (runtime symbols as traps, exported via an import library), link every generated
# object + pvgame_entry into pvgame.dll against it, then run the host to validate the tables.
# Usage: link_m1.sh <genfull_dir>   (expects obj/, obj_subsdk0/, obj_sdk/ from compile_chunks.sh)
set -eu
G=$1
P="D:/Dev/REA/Pokemon Decompile"
export PATH="/d/msys64/ucrt64/bin:$PATH"
export TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"
cd "$G"
mkdir -p m1
clang -O1 -Wall -Wno-dll-attribute-on-redeclaration -I"$P/runtime" "$P/recomp/m1_host.c" -o m1/m1_host.exe -fuse-ld=lld \
      -Wl,--out-implib,m1/m1_host.dll.a
clang -O1 -march=x86-64-v3 -fvisibility=hidden -I"$P/runtime" -c "$P/recomp/pvgame_entry.c" -o m1/pvgame_entry.o
ls obj/*.o obj_subsdk0/*.o obj_sdk/*.o | sed 's/.*/"&"/' > m1/objs.rsp
echo m1/pvgame_entry.o >> m1/objs.rsp
start=$(date +%s)
clang -shared -fuse-ld=lld -o m1/pvgame.dll @m1/objs.rsp m1/m1_host.dll.a
echo "link: $(( $(date +%s) - start )) s, pvgame.dll $(du -h m1/pvgame.dll | cut -f1)"
cd m1 && ./m1_host.exe pvgame.dll
