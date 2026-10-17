#!/usr/bin/env bash
# Incremental rebuild of one dump version after a gen.py change: regenerate C for every module (gen.py only rewrites
# files whose text changed) and recompile just the chunks newer than their object.
# Usage: regen_changed.sh <exefs_dir> <gen_dir> [jobs]
set -eu
EXEFS=$1; OUT=$2; JOBS=${3:-10}
cd "$(dirname "$0")"
PY=venv/Scripts/python.exe
WOUT=$(cygpath -m "$OUT"); WEX=$(cygpath -m "$EXEFS")
RT="D:/Dev/REA/psvrecomp/runtime"
export PATH="/d/msys64/ucrt64/bin:$PATH"
export TMP="$(cygpath -w "$LOCALAPPDATA")\\Temp" TEMP="$(cygpath -w "$LOCALAPPDATA")\\Temp"
"$PY" layout.py "$WEX" > "$OUT/layout.txt"
while read -r name base _; do
  b=${base#base=0x}
  case $name in main) obj=obj ;; *) obj=obj_$name ;; esac
  "$PY" gen.py "$name" "$WEX/$name" "0x$b" "$WOUT/$name" --simd c > "$OUT/gen_$name.log" 2>&1 || { echo "gen.py $name FAILED"; exit 1; }
  changed=()
  for f in "$OUT/$name"/*.c; do
    o="$OUT/$obj/$(basename "$f" .c).o"
    [ "$f" -nt "$o" ] && changed+=("$f")
  done
  echo "$name: ${#changed[@]} chunks changed"
  [ ${#changed[@]} -eq 0 ] && continue
  printf '%s\n' "${changed[@]}" | xargs -P "$JOBS" -I{} sh -c '
    clang -O1 -fno-strict-aliasing -Wno-return-type -Wno-unused-label -march=x86-64-v3 -fvisibility=hidden \
      -I"'"$RT"'" -c "$(cygpath -m "{}")" -o "'"$WOUT/$obj"'/$(basename "{}" .c).o" || echo "FAIL {}"'
done < <(grep -E '^(main|subsdk0|sdk) ' "$OUT/layout.txt")
