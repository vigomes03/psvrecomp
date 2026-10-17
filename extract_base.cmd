@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

if /i "%~1"=="--help" goto :help

set "ROM=roms\Pokémon Violet.xci"
set "KEYS=keys\game.keys"
set "HACTOOL=D:\Tools\hactool\hactool.exe"
set "OUT=dumps\base"
set "LOG=%TEMP%\psvrecomp_extract_base.log"

if not exist "%ROM%" (
  echo ERROR: base ROM not found: %ROM%
  exit /b 1
)
if not exist "%KEYS%" (
  echo ERROR: keys not found: %KEYS%
  exit /b 1
)
if not exist "%HACTOOL%" (
  echo ERROR: hactool not found: %HACTOOL%
  exit /b 1
)
if exist "%OUT%\secure\" (
  echo ERROR: %OUT% already exists. This script never overwrites an existing dump.
  echo Move or archive the previous dump before extracting again.
  exit /b 1
)

mkdir "%OUT%\secure" "%OUT%\exefs" "%OUT%\romfs" || exit /b 1

echo [1/2] Extracting the cartridge secure partition...
"%HACTOOL%" -k "%KEYS%" -t xci --securedir="%OUT%\secure" "%ROM%" > "%LOG%" 2>&1
if errorlevel 1 goto :hactool_failed

for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=(Get-ChildItem -LiteralPath '%OUT%\secure' -Filter *.nca -File ^| Sort-Object Length -Descending ^| Select-Object -First 1).FullName; if ($p) { [Console]::Write($p) }"`) do set "PROGRAM=%%F"
if not defined PROGRAM (
  echo ERROR: no program NCA was found in %OUT%\secure.
  exit /b 1
)

echo [2/2] Extracting ExeFS and RomFS from the largest program NCA...
"%HACTOOL%" -k "%KEYS%" -t nca --exefsdir="%OUT%\exefs" --romfsdir="%OUT%\romfs" "%PROGRAM%" > "%LOG%" 2>&1
if errorlevel 1 goto :hactool_failed

del "%LOG%" >nul 2>&1
echo.
echo Complete: %OUT%\secure, %OUT%\exefs and %OUT%\romfs
exit /b 0

:hactool_failed
echo ERROR: hactool failed. The local diagnostic is at %LOG%.
echo Do not share this file: extraction tools can record sensitive key data.
exit /b 1

:help
echo Usage: extract_base.cmd
echo Extracts roms\Pokémon Violet.xci into dumps\base\.
echo Requires keys\game.keys and D:\Tools\hactool\hactool.exe.
exit /b 0
