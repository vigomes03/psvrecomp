#!/usr/bin/env bash
# Build the host (pvhost.exe) from runtime/*.c + services + hle + nvn + platform/windows.c.
# Usage: build_host.sh <out_dir> [null|vulkan]   -> <out_dir>/pvhost.exe + pvhost.dll.a (import library for pvgame.dll)
#   null   (default): headless, NVN null backend (W03) -- what the boot gates use
#   vulkan: LAS's Vulkan renderer + SDL3 window + Maxwell shader translator (phase 4), -DPVR_VULKAN
set -u
OUT=$(cygpath -m "$1")  # clang is native: no /d/ paths
BACKEND=${2:-null}
P="D:/Dev/REA/Pokemon Decompile/runtime"
export PATH="/d/msys64/ucrt64/bin:$PATH"
export TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"
mkdir -p "$OUT/rt"
FLAGS="-O2 -g -fno-strict-aliasing -Wall -Wno-unused-function -D_FILE_OFFSET_BITS=64 -D_POSIX_THREAD_SAFE_FUNCTIONS -D_CRT_RAND_S -DWIN32_LEAN_AND_MEAN -DNOMINMAX -march=x86-64-v3"
NVN_CORE=("$P"/nvn/cmdbuf.c "$P"/nvn/formats.c "$P"/nvn/objects.c "$P"/nvn/tegra.c "$P"/nvn/xfb_layout.c)
INC=()
LIBS="-lwinmm -lole32 -lshell32 -ldbghelp -lbcrypt"
case $BACKEND in
  null)   NVN=("${NVN_CORE[@]}" "$P"/nvn/null_backend.c) ;;
  vulkan) NVN=("${NVN_CORE[@]}" "$P"/nvn/astc.c "$P"/nvn/output_scale.c "$P"/nvn/smaa_data.c
               "$P"/nvn/vulkan/*.c "$P"/nvn/maxwell/*.c)
          FLAGS="$FLAGS -DPVR_VULKAN"
          INC+=(-I"D:/Dev/REA/Pokemon Decompile/third_party/smaa/Textures")
          LIBS="$LIBS -lSDL3 -lvulkan-1 -lshaderc_shared" ;;
  *) echo "backend must be null or vulkan"; exit 2 ;;
esac
objs=()
fail=0
for f in "$P"/*.c "$P"/services/*.c "$P"/hle/*.c "${NVN[@]}" "$P"/platform/windows.c; do
  [ -f "$f" ] || continue
  d=$(basename "$(dirname "$f")")
  o="$OUT/rt/${d}_$(basename "$f" .c).o"
  clang $FLAGS -I"$P" "${INC[@]}" -c "$f" -o "$o" || fail=1
  objs+=("$o")
done
if [ "$BACKEND" = vulkan ]; then  # Vulkan Memory Allocator: header-only C++ (MSYS2 vulkan-memory-allocator)
  clang++ -O2 -std=c++17 -w -c "D:/Dev/REA/LASRecomp-main/LASRecomp-main/runtime/nvn/vulkan/vma.cpp" -o "$OUT/rt/vma.o" || fail=1
  objs+=("$OUT/rt/vma.o")
  LIBS="$LIBS -lstdc++"
fi
[ $fail = 0 ] || { echo "compile errors"; exit 1; }
# pvgame.dll calls the runtime (rt_dispatch, rt_svc, ...): the .exe exports everything and pvgame links its import lib
# (same as LAS: LDFLAGS += -Wl,--export-all-symbols -Wl,--out-implib,...).
clang -fuse-ld=lld -Wl,--error-limit=0 -Wl,--stack,16777216 -Wl,--export-all-symbols -Wl,--out-implib,"$OUT/pvhost.dll.a" \
  -o "$OUT/pvhost.exe" "${objs[@]}" $LIBS || exit 1
echo "built $OUT/pvhost.exe + pvhost.dll.a ($BACKEND)"
