#!/usr/bin/env bash
# Build the headless host (pvhost.exe) from runtime/*.c + services + hle + platform/windows.c.
# Usage: build_host.sh <out_dir>   -> <out_dir>/pvhost.exe + pvhost.dll.a (import library for pvgame.dll)
set -u
OUT=$(cygpath -m "$1")  # clang is native: no /d/ paths
P="D:/Dev/REA/Pokemon Decompile/runtime"
export PATH="/d/msys64/ucrt64/bin:$PATH"
export TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"
mkdir -p "$OUT/rt"
FLAGS="-O2 -g -fno-strict-aliasing -Wall -Wno-unused-function -D_FILE_OFFSET_BITS=64 -D_POSIX_THREAD_SAFE_FUNCTIONS -D_CRT_RAND_S -DWIN32_LEAN_AND_MEAN -DNOMINMAX -march=x86-64-v3"
objs=()
for f in "$P"/*.c "$P"/services/*.c "$P"/hle/*.c "$P"/nvn/*.c "$P"/platform/windows.c; do
  [ -f "$f" ] || continue
  o="$OUT/rt/$(basename "$(dirname "$f")")_$(basename "$f" .c).o"
  clang $FLAGS -I"$P" -c "$f" -o "$o"
  objs+=("$o")
done
# pvgame.dll calls the runtime (rt_dispatch, rt_svc, ...): the .exe exports everything and pvgame links its import lib
# (same as LAS: LDFLAGS += -Wl,--export-all-symbols -Wl,--out-implib,...).
clang -fuse-ld=lld -Wl,--stack,16777216 -Wl,--export-all-symbols -Wl,--out-implib,"$OUT/pvhost.dll.a" \
  -o "$OUT/pvhost.exe" "${objs[@]}" -lwinmm -lole32 -lshell32 -ldbghelp -lbcrypt || exit 1
echo "built $OUT/pvhost.exe + pvhost.dll.a"
