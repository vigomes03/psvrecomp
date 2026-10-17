#!/usr/bin/env bash
# Recompile every module of one dump version: gen.py (C) + compile_chunks.sh (objects), bases from layout.py.
# Usage: gen_all.sh <exefs_dir> <out_dir> [jobs]   e.g. gen_all.sh ../../dumps/v400/exefs /d/Dev/REA/lab/gen-v400
# Output: <out_dir>/{main,subsdk0,sdk}/*.c and <out_dir>/{obj,obj_subsdk0,obj_sdk}/*.o (the layout run_boot.sh links).
set -eu
EXEFS=$1; OUT=$2; JOBS=${3:-10}
cd "$(dirname "$0")"
PY=venv/Scripts/python.exe
WOUT=$(cygpath -m "$OUT"); WEX=$(cygpath -m "$EXEFS")
mkdir -p "$OUT"
"$PY" layout.py "$WEX" | tee "$OUT/layout.txt"
while read -r name base _; do
  b=${base#base=0x}
  case $name in main) obj=obj ;; *) obj=obj_$name ;; esac
  echo "== $name @ 0x$b"
  rm -rf "$OUT/$name" "$OUT/$obj"
  start=$(date +%s)
  "$PY" gen.py "$name" "$WEX/$name" "0x$b" "$WOUT/$name" --simd c > "$OUT/gen_$name.log" 2>&1 || { echo "gen.py $name FAILED"; tail -5 "$OUT/gen_$name.log"; exit 1; }
  echo "   gen $(( $(date +%s) - start )) s, $(ls "$OUT/$name"/*.c | wc -l) files"
  start=$(date +%s)
  bash compile_chunks.sh "$WOUT/$name" "$WOUT/$obj" "$JOBS"
  echo "   compile $(( $(date +%s) - start )) s"
  if grep -q '^FAIL' "$OUT/$obj/errors.log"; then echo "compile errors in $name"; exit 1; fi
done < <(grep -E '^(main|subsdk0|sdk) ' "$OUT/layout.txt")
