@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0.." || exit /b 1

if /i "%~1"=="--help" goto :help

set "PYTHON=psvrecomp\recomp\venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo ERROR: recompilation Python environment not found: %PYTHON%.
  exit /b 1
)

set "UPDATE=roms\Pokémon Violet Update V4.0.0.nsp"
set "KEYS=keys\game.keys"
set "HACTOOL=D:\Tools\hactool\hactool.exe"
set "HACTOOLNET=D:\Tools\hactoolnet\hactoolnet.exe"
if not exist "%HACTOOLNET%" set "HACTOOLNET=tools\hactoolnet\hactoolnet.exe"
set "BASE=dumps\base\secure"
set "UPDATEOUT=dumps\update\nsp"
set "V400=dumps\v400"
set "LOG=%TEMP%\psvrecomp_extract_update.log"

if not exist "%UPDATE%" (
  echo ERROR: update not found: %UPDATE%
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
if not exist "%HACTOOLNET%" (
  echo ERROR: hactoolnet not found in D:\Tools\hactoolnet or tools\hactoolnet.
  exit /b 1
)
if not exist "%BASE%\" (
  echo ERROR: extract the base ROM first with scripts\extract_base.cmd.
  exit /b 1
)
if exist "%UPDATEOUT%\" (
  echo ERROR: %UPDATEOUT% already exists. This script never overwrites an existing dump.
  exit /b 1
)
if exist "%V400%\" (
  echo ERROR: %V400% already exists. This script never overwrites an existing dump.
  exit /b 1
)

mkdir "%UPDATEOUT%" "%V400%\exefs" "%V400%\romfs" || exit /b 1

echo [1/4] Extracting update NCAs...
"%HACTOOL%" -k "%KEYS%" -t pfs0 --outdir="%UPDATEOUT%" "%UPDATE%" > "%LOG%" 2>&1
if errorlevel 1 goto :extract_failed

for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=(Get-ChildItem -LiteralPath '%UPDATEOUT%' -Filter *.tik -File ^| Select-Object -First 1).FullName; if ($p) { [Console]::Write($p) }"`) do set "TIK=%%F"
if not defined TIK (
  echo ERROR: .tik ticket not found in %UPDATEOUT%.
  exit /b 1
)
for /f "usebackq delims=" %%K in (`powershell -NoProfile -Command "$b=[IO.File]::ReadAllBytes('%TIK%'); if ($b.Length -lt 400) { exit 2 }; [Console]::Write([BitConverter]::ToString($b[384..399]).Replace('-','').ToLowerInvariant())"`) do set "TITLEKEY=%%K"
if not defined TITLEKEY (
  echo ERROR: could not read the title key from the ticket.
  exit /b 1
)
for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=(Get-ChildItem -LiteralPath '%BASE%' -Filter *.nca -File ^| Sort-Object Length -Descending ^| Select-Object -First 1).FullName; if ($p) { [Console]::Write($p) }"`) do set "BASEPROGRAM=%%F"
for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=(Get-ChildItem -LiteralPath '%UPDATEOUT%' -Filter *.nca -File ^| Sort-Object Length -Descending ^| Select-Object -First 1).FullName; if ($p) { [Console]::Write($p) }"`) do set "UPDATEPROGRAM=%%F"
if not defined BASEPROGRAM (
  echo ERROR: base program NCA not found.
  exit /b 1
)
if not defined UPDATEPROGRAM (
  echo ERROR: update program NCA not found.
  exit /b 1
)

echo [2/4] Extracting v4.0.0 ExeFS with hactool...
"%HACTOOL%" -k "%KEYS%" -t nca --titlekey "%TITLEKEY%" --exefsdir="%V400%\exefs" "%UPDATEPROGRAM%" > "%LOG%" 2>&1
if errorlevel 1 goto :extract_failed

if not defined DOTNET_ROOT_X86 if exist "D:\Tools\dotnet8-x86\dotnet.exe" set "DOTNET_ROOT_X86=D:\Tools\dotnet8-x86"
echo [3/4] Applying the update to RomFS with hactoolnet...
"%HACTOOLNET%" -k "%KEYS%" --disablekeywarns -y -t nca --titlekey "%TITLEKEY%" --basenca "%BASEPROGRAM%" --romfsdir "%V400%\romfs" "%UPDATEPROGRAM%" > "%LOG%" 2>&1
if errorlevel 1 goto :extract_failed

echo [4/4] Validating extracted NSOs...
for %%F in (main sdk subsdk0) do (
  if not exist "%V400%\exefs\%%F" goto :verify_failed
  "%PYTHON%" psvrecomp\recomp\nso_verify.py "%V400%\exefs\%%F" || goto :verify_failed
)

set "TITLEKEY="
del "%LOG%" >nul 2>&1
echo.
echo Complete: %UPDATEOUT%, %V400%\exefs and %V400%\romfs
exit /b 0

:extract_failed
set "TITLEKEY="
echo ERROR: extraction failed. The local diagnostic is at %LOG%.
echo Do not share this file: extraction tools can record sensitive key data.
exit /b 1

:verify_failed
set "TITLEKEY="
echo ERROR: NSO verification failed. The extraction was kept for local investigation.
exit /b 1

:help
echo Usage: scripts\extract_update_v400.cmd
echo Extracts roms\Pokémon Violet Update V4.0.0.nsp into dumps\update and dumps\v400.
echo Requires an extracted base, keys\game.keys, hactool, and hactoolnet with .NET 8 x86.
exit /b 0
