#!/usr/bin/env bash
# Compile every chunk of a generated module in parallel. Usage: compile_chunks.sh <gen_dir> <obj_dir> [jobs]
# Errors -> <obj_dir>/errors.log (one "FAIL <file>" line per failed chunk).
set -u
GEN=$1; OBJ=$2; JOBS=${3:-10}
RT="D:/Dev/REA/Pokemon Decompile/runtime"
export PATH="/d/msys64/ucrt64/bin:$PATH"
export TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"
mkdir -p "$OBJ"; : > "$OBJ/errors.log"
export RT OBJ
ls "$GEN"/*.c | xargs -P "$JOBS" -I{} sh -c '
  o="$OBJ/$(basename {} .c).o"
  clang -O1 -fno-strict-aliasing -Wno-return-type -Wno-unused-label -march=x86-64-v3 -fvisibility=hidden \
        -I"$RT" -c {} -o "$o" 2>>"$OBJ/errors.log" || echo "FAIL {}" >> "$OBJ/errors.log"'
echo "objs: $(ls "$OBJ"/*.o 2>/dev/null | wc -l)  fails: $(grep -c '^FAIL' "$OBJ/errors.log")"
