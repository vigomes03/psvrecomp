@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

if /i "%~1"=="--help" goto :help

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
  echo ERRO: update ausente: %UPDATE%
  exit /b 1
)
if not exist "%KEYS%" (
  echo ERRO: chaves ausentes: %KEYS%
  exit /b 1
)
if not exist "%HACTOOL%" (
  echo ERRO: hactool ausente: %HACTOOL%
  exit /b 1
)
if not exist "%HACTOOLNET%" (
  echo ERRO: hactoolnet ausente em D:\Tools\hactoolnet ou tools\hactoolnet.
  exit /b 1
)
if not exist "%BASE%\" (
  echo ERRO: extraia primeiro a ROM base com extrair_base.cmd.
  exit /b 1
)
if exist "%UPDATEOUT%\" (
  echo ERRO: %UPDATEOUT% ja existe. O script nao sobrescreve dumps existentes.
  exit /b 1
)
if exist "%V400%\" (
  echo ERRO: %V400% ja existe. O script nao sobrescreve dumps existentes.
  exit /b 1
)

mkdir "%UPDATEOUT%" "%V400%\exefs" "%V400%\romfs" || exit /b 1

echo [1/4] Extraindo os NCAs do update...
"%HACTOOL%" -k "%KEYS%" -t pfs0 --outdir="%UPDATEOUT%" "%UPDATE%" > "%LOG%" 2>&1
if errorlevel 1 goto :extract_failed

for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=(Get-ChildItem -LiteralPath '%UPDATEOUT%' -Filter *.tik -File ^| Select-Object -First 1).FullName; if ($p) { [Console]::Write($p) }"`) do set "TIK=%%F"
if not defined TIK (
  echo ERRO: ticket .tik nao encontrado em %UPDATEOUT%.
  exit /b 1
)
for /f "usebackq delims=" %%K in (`powershell -NoProfile -Command "$b=[IO.File]::ReadAllBytes('%TIK%'); if ($b.Length -lt 400) { exit 2 }; [Console]::Write([BitConverter]::ToString($b[384..399]).Replace('-','').ToLowerInvariant())"`) do set "TITLEKEY=%%K"
if not defined TITLEKEY (
  echo ERRO: nao foi possivel obter a title key do ticket.
  exit /b 1
)
for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=(Get-ChildItem -LiteralPath '%BASE%' -Filter *.nca -File ^| Sort-Object Length -Descending ^| Select-Object -First 1).FullName; if ($p) { [Console]::Write($p) }"`) do set "BASEPROGRAM=%%F"
for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=(Get-ChildItem -LiteralPath '%UPDATEOUT%' -Filter *.nca -File ^| Sort-Object Length -Descending ^| Select-Object -First 1).FullName; if ($p) { [Console]::Write($p) }"`) do set "UPDATEPROGRAM=%%F"
if not defined BASEPROGRAM (
  echo ERRO: NCA de programa base nao encontrado.
  exit /b 1
)
if not defined UPDATEPROGRAM (
  echo ERRO: NCA de programa do update nao encontrado.
  exit /b 1
)

echo [2/4] Extraindo ExeFS v4.0.0 com hactool...
"%HACTOOL%" -k "%KEYS%" -t nca --titlekey "%TITLEKEY%" --exefsdir="%V400%\exefs" "%UPDATEPROGRAM%" > "%LOG%" 2>&1
if errorlevel 1 goto :extract_failed

if not defined DOTNET_ROOT_X86 if exist "D:\Tools\dotnet8-x86\dotnet.exe" set "DOTNET_ROOT_X86=D:\Tools\dotnet8-x86"
echo [3/4] Aplicando o update ao RomFS com hactoolnet...
"%HACTOOLNET%" -k "%KEYS%" --disablekeywarns -y -t nca --titlekey "%TITLEKEY%" --basenca "%BASEPROGRAM%" --romfsdir "%V400%\romfs" "%UPDATEPROGRAM%" > "%LOG%" 2>&1
if errorlevel 1 goto :extract_failed

echo [4/4] Validando os NSOs extraidos...
for %%F in ("%V400%\exefs\*.nso") do python psvrecomp\recomp\nso_verify.py "%%~fF" || goto :verify_failed

set "TITLEKEY="
del "%LOG%" >nul 2>&1
echo.
echo Concluido: %UPDATEOUT%, %V400%\exefs e %V400%\romfs
exit /b 0

:extract_failed
set "TITLEKEY="
echo ERRO: a extracao falhou. O diagnostico local esta em %LOG%.
echo Nao envie esse arquivo: ferramentas de extracao podem registrar dados sensiveis das chaves.
exit /b 1

:verify_failed
set "TITLEKEY="
echo ERRO: a verificacao de NSO falhou. A extracao foi mantida para investigacao local.
exit /b 1

:help
echo Uso: extrair_update_v400.cmd
echo Extrai roms\Pokémon Violet Update V4.0.0.nsp para dumps\update e dumps\v400.
echo Requer a base ja extraida, keys\game.keys, hactool e hactoolnet com .NET 8 x86.
exit /b 0
