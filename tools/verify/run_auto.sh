#!/usr/bin/env bash
# ===== AUTOMATIC (Claude's pipeline): scripted input + screenshots + frame stats, retries on crash.
# Usage: tools/verify/run_auto.sh [seconds=240] [tag=auto] [extra VAR=value ...]
#   Input: A every 1 s from 3 s, left stick right for 300 ms every 5 s (passes "choose a look"), as found 15/10.
#   Override with PVR_AUTOPRESS / PVR_INPUT in the environment (e.g. PVR_INPUT=3000:A,6000:STICK_DOWN:300).
#   Output: lab/host-vk/<tag>.log, frames in lab/host-vk/build/frames (every 100 frames), stats printed.
#   Retries up to 3x when the run dies (FATAL / access violation: the intermittent Lua panic of v400).
# Manual play (you at the keyboard / gamepad) is "Pokemon Decompile/recomp/run_window.cmd".
set -u
SECS=${1:-240}
TAG=${2:-auto}
shift 2 2>/dev/null || shift $#
H=${PVR_HOST_DIR:-/d/Dev/REA/lab/host-vk}  # (another build dir while [USER] plays from host-vk)
export PATH="/d/msys64/ucrt64/bin:$PATH"
export PVR_SYSFONT_DIR=${PVR_SYSFONT_DIR:-D:/Dev/REA/lab/sysfont}
export PVR_DISPLAY=${PVR_DISPLAY:-2}  # (window on the 2nd monitor: [USER] works on the primary)
export SDL_AUDIO_DRIVER=${SDL_AUDIO_DRIVER:-dummy}  # (pipeline runs are silent: same audio timing, nothing on the speakers;
                                                  #  run_window.cmd keeps the sound. SDL_AUDIO_DRIVER= unset/other to hear)
export PVR_AUTOPRESS=${PVR_AUTOPRESS:-A:1000:100:3000}
if [ -z "${PVR_INPUT:-}" ]; then
  PVR_INPUT=$(python -c "print(','.join(f'{t}:STICK_RIGHT:300' for t in range(5500, $SECS*1000+5000, 5000)))")
fi
export PVR_INPUT
export LARECOMP_SCREENSHOT_EVERY=${LARECOMP_SCREENSHOT_EVERY:-100} LARECOMP_SCREENSHOT_FROM=${LARECOMP_SCREENSHOT_FROM:-100}
export PVR_RUN_SECONDS=$SECS
# Saves: the pipeline NEVER uses lab/host-vk/save ([USER]'s manual-play save). It plays in save_auto, reset before
# every run from SAVE_SEED=<dir with save_0/...> when given (e.g. SAVE_SEED=D:/Dev/REA/lab/saves/user_antes_batalha_20261015).
export LARECOMP_SAVE_DIR=${LARECOMP_SAVE_DIR:-D:/Dev/REA/lab/host-vk/save_auto}
cd "$H" || exit 1
for i in 1 2 3; do
  if [ -n "${SAVE_SEED:-}" ]; then rm -rf "$LARECOMP_SAVE_DIR" && cp -r "$SAVE_SEED" "$LARECOMP_SAVE_DIR"; fi
  rm -rf build && mkdir -p build/frames
  env "$@" ./pvhost.exe D:/Dev/REA/dumps/v400/exefs D:/Dev/REA/dumps/v400/romfs > "$TAG.log" 2>&1
  bad=$(grep -c "FATAL\|exception c0000005" "$TAG.log")
  echo "run $i: bad=$bad last=$(grep -o 'frame [0-9]*' "$TAG.log" | tail -1) log=$H/$TAG.log"
  [ "$bad" = 0 ] && break
  cp "$TAG.log" "$TAG.run$i.log"  # (the next try overwrites $TAG.log: keep the failed one)
done
python D:/Dev/REA/tools/verify/frame_stats.py build/frames/*.png | awk '{print $1, "mean", $5, "colors", $7}' | tr -d "{},'"
[ "$bad" = 0 ]
