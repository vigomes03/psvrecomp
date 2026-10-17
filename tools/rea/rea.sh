#!/usr/bin/env bash
# REA wrapper for local agents (Hermes / git-bash). Keeps output small for 64k-context models.
#   rea.sh <command> <target> [args...]      -> lean output (evidence_id, confidence, normalized_result), max 2000 tokens
#   REA_RAW=1 rea.sh ...                     -> full Evidence envelope (big; avoid in local models)
#   REA_TOKENS=4000 rea.sh ...               -> raise the token window
#   REA_OFFSET=2000 rea.sh ...               -> read the next window of a long result
export GHIDRA_INSTALL_DIR='D:\Tools\ghidra_12.1.4_PUBLIC'
export JAVA_HOME='D:\Tools\jdk-21.0.12.1+1'
# REA's native addon needs real Windows temp paths; MSYS shells set TMP=/tmp, which breaks its private runtime dir.
export TMP="$LOCALAPPDATA\\Temp" TEMP="$LOCALAPPDATA\\Temp"
NODE="/c/Program Files/nodejs/node.exe"
REA="D:/Dev/REA/ref/rea-main/rea-main/scripts/rea.mjs"
if [ -n "$REA_RAW" ] || [ "$1" = "--help" ] || [ "$1" = "doctor" ] || [[ " $* " == *" --help "* ]]; then
  exec "$NODE" "$REA" "$@"
fi
exec "$NODE" "$REA" "$@" \
  --filter-output evidence_id,confidence,normalized_result \
  --token-limit "${REA_TOKENS:-2000}" --token-offset "${REA_OFFSET:-0}"
