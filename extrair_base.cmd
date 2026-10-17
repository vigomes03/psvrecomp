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
  echo ERRO: ROM base ausente: %ROM%
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
if exist "%OUT%\secure\" (
  echo ERRO: %OUT% ja existe. O script nao sobrescreve dumps existentes.
  echo Mova ou arquive o dump anterior antes de extrair novamente.
  exit /b 1
)

mkdir "%OUT%\secure" "%OUT%\exefs" "%OUT%\romfs" || exit /b 1

echo [1/2] Extraindo a particao secure do cartucho...
"%HACTOOL%" -k "%KEYS%" -t xci --securedir="%OUT%\secure" "%ROM%" > "%LOG%" 2>&1
if errorlevel 1 goto :hactool_failed

for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=(Get-ChildItem -LiteralPath '%OUT%\secure' -Filter *.nca -File ^| Sort-Object Length -Descending ^| Select-Object -First 1).FullName; if ($p) { [Console]::Write($p) }"`) do set "PROGRAM=%%F"
if not defined PROGRAM (
  echo ERRO: nenhum NCA de programa foi encontrado em %OUT%\secure.
  exit /b 1
)

echo [2/2] Extraindo ExeFS e RomFS do maior NCA de programa...
"%HACTOOL%" -k "%KEYS%" -t nca --exefsdir="%OUT%\exefs" --romfsdir="%OUT%\romfs" "%PROGRAM%" > "%LOG%" 2>&1
if errorlevel 1 goto :hactool_failed

del "%LOG%" >nul 2>&1
echo.
echo Concluido: %OUT%\secure, %OUT%\exefs e %OUT%\romfs
exit /b 0

:hactool_failed
echo ERRO: hactool falhou. O diagnostico local esta em %LOG%.
echo Nao envie esse arquivo: ferramentas de extracao podem registrar dados sensiveis das chaves.
exit /b 1

:help
echo Uso: extrair_base.cmd
echo Extrai a ROM base de roms\Pokémon Violet.xci para dumps\base\.
echo Requer keys\game.keys e D:\Tools\hactool\hactool.exe.
exit /b 0
