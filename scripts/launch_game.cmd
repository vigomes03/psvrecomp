@echo off
setlocal EnableExtensions
cd /d "%~dp0.." || exit /b 1

if /i "%~1"=="--help" goto :help

call "psvrecomp\recomp\run_window.cmd" %*
exit /b %ERRORLEVEL%

:help
echo Usage: scripts\launch_game.cmd [host_dir] [version] [seconds] [monitor]
echo Starts PSV Recomp for manual play through psvrecomp\recomp\run_window.cmd.
exit /b 0
