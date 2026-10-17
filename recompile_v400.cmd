@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

if /i "%~1"=="--help" goto :help

set "BASH=D:\msys64\usr\bin\bash.exe"
set "EXEFS=dumps\v400\exefs"
set "GEN=lab\gen-v400"
set "JOBS=10"

if not exist "%BASH%" (
  echo ERROR: MSYS2 Bash not found: %BASH%
  exit /b 1
)
if not exist "%EXEFS%\" (
  echo ERROR: extracted v4.0.0 ExeFS not found: %EXEFS%
  echo Run extract_update_v400.cmd first.
  exit /b 1
)
if not exist "psvrecomp\recomp\venv\Scripts\python.exe" (
  echo ERROR: recompilation Python environment not found.
  exit /b 1
)

if /i not "%~1"=="--yes" (
  echo This regenerates C files and object files in %GEN%.
  echo It is CPU and disk intensive and can take a long time.
  set /p "ANSWER=Continue? [y/N] "
  if /i not "%ANSWER%"=="Y" (
    echo Cancelled.
    exit /b 0
  )
)

echo Recompiling PSV Recomp v4.0.0 with %JOBS% parallel jobs...
call "%BASH%" -lc "cd /d/Dev/REA/psvrecomp/recomp && ./gen_all.sh /d/Dev/REA/dumps/v400/exefs /d/Dev/REA/lab/gen-v400 %JOBS%"
if errorlevel 1 (
  echo ERROR: recompilation failed. Check %GEN%\gen_*.log and obj*\errors.log.
  exit /b 1
)

echo Complete: generated C and objects are in %GEN%.
exit /b 0

:help
echo Usage: recompile_v400.cmd [--yes]
echo Recompiles the extracted v4.0.0 ExeFS into C and x86-64 object files.
echo --yes skips the interactive confirmation.
exit /b 0
