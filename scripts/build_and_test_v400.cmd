@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0.." || exit /b 1

if /i "%~1"=="--help" goto :help

set "BASH=D:\msys64\usr\bin\bash.exe"
set "GEN=lab\gen-v400"
set "HOST=D:/Dev/REA/lab/host-test-v400"

if not exist "%BASH%" (
  echo ERROR: MSYS2 Bash not found: %BASH%
  exit /b 1
)
if not exist "%GEN%\obj\" (
  echo ERROR: generated objects not found in %GEN%.
  echo Run scripts\recompile_v400.cmd first.
  exit /b 1
)
if not exist "%GEN%\obj_subsdk0\" (
  echo ERROR: generated objects not found in %GEN%.
  echo Run scripts\recompile_v400.cmd first.
  exit /b 1
)
if not exist "%GEN%\obj_sdk\" (
  echo ERROR: generated objects not found in %GEN%.
  echo Run scripts\recompile_v400.cmd first.
  exit /b 1
)
tasklist /fi "imagename eq pvhost.exe" | findstr /i /c:"pvhost.exe" >nul
if not errorlevel 1 (
  echo ERROR: pvhost.exe is already running. Close the game before building.
  exit /b 1
)

echo [1/2] Building an isolated Vulkan host in lab\host-test-v400...
call "%BASH%" -lc "cd /d/Dev/REA/psvrecomp/recomp && ./build_host.sh D:/Dev/REA/lab/host-test-v400 vulkan"
if errorlevel 1 (
  echo ERROR: Vulkan host build failed.
  exit /b 1
)

echo [2/2] Linking pvgame.dll and running a 30-second automated boot test...
call "%BASH%" -lc "cd /d/Dev/REA/psvrecomp/recomp && SDL_AUDIO_DRIVER=dummy ./run_boot.sh /d/Dev/REA/lab/gen-v400 /d/Dev/REA/lab/host-test-v400 30 v400"
if errorlevel 1 (
  echo ERROR: link or boot test failed. See lab\host-test-v400\boot.log.
  exit /b 1
)

echo Complete: see lab\host-test-v400\boot.log.
exit /b 0

:help
echo Usage: scripts\build_and_test_v400.cmd
echo Builds an isolated Vulkan host, links pvgame.dll, and runs a 30-second automatic boot test.
echo It uses lab\host-test-v400 and never overwrites the manual-play host directory.
exit /b 0
