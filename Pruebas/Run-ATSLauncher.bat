@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".ats_core\src\Start-NXLauncher.ps1"
endlocal
