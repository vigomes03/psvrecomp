@echo off
rem ===== MANUAL: you play. Double-click, or: run_window.cmd [host_dir] [version] [seconds] [monitor]
rem   host_dir: build_host.sh <dir> vulkan output that also holds pvgame.dll (default D:\Dev\REA\lab\host-vk)
rem   version : dumps\<version> (default v400)      seconds: 0 = until the window is closed (default 0)
rem   monitor : 1, 2, ... (default 2; or set PVR_DISPLAY before). The monitor list is at the top of window.log.
rem   No scripted input here (PVR_INPUT / PVR_AUTOPRESS are cleared): keyboard + gamepad only.
rem   Keyboard: WASD left stick, arrows d-pad, K or Space = A, J = B, I = X, L = Y, Q/E = L/R, 1/3 = ZL/ZR,
rem             Enter = +, Backspace = -, F/R = stick clicks, numpad 8/4/5/6 = right stick.
rem   Gamepad (Xbox/PS/Switch Pro, plug in before or during the run): Switch layout by position.
rem   The automatic run (Claude's pipeline) is tools\verify\run_auto.sh.
rem pvhost.exe needs SDL3.dll, libshaderc_shared.dll, libstdc++-6.dll, libwinpthread-1.dll from MSYS2 UCRT64.
setlocal
set "HOSTDIR=%~1"
if "%HOSTDIR%"=="" set "HOSTDIR=D:\Dev\REA\lab\host-vk"
set "VER=%~2"
if "%VER%"=="" set "VER=v400"
set "PVR_RUN_SECONDS=%~3"
if "%PVR_RUN_SECONDS%"=="" set "PVR_RUN_SECONDS=0"
if not "%~4"=="" set "PVR_DISPLAY=%~4"
if not defined PVR_DISPLAY set "PVR_DISPLAY=2"
set "PVR_INPUT="
set "PVR_AUTOPRESS="
set "PVR_DBG_FS="
set "PVR_DBG_PC="
set "LARECOMP_DEBUG_FRAME="
set "PATH=D:\msys64\ucrt64\bin;%PATH%"
if not defined PVR_SYSFONT_DIR set "PVR_SYSFONT_DIR=D:/Dev/REA/lab/sysfont"
if not exist "%HOSTDIR%\pvgame.dll" (
  echo pvgame.dll missing in %HOSTDIR%: run build_host.sh %HOSTDIR% vulkan, then run_boot.sh to link it.
  exit /b 1
)
cd /d "%HOSTDIR%"
echo log: %HOSTDIR%\window.log
pvhost.exe "D:/Dev/REA/dumps/%VER%/exefs" "D:/Dev/REA/dumps/%VER%/romfs" > window.log 2>&1
echo exit=%ERRORLEVEL%
endlocal
