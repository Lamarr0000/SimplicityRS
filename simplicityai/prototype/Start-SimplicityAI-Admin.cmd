@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -Command "$root=$pwd.Path; $python=Join-Path $root 'runtime\python.exe'; if(-not(Test-Path -LiteralPath $python)){throw 'Expected VM portable runtime not found'}; Start-Process -FilePath $python -ArgumentList ('"'+(Join-Path $root 'launcher.py')+'"') -WorkingDirectory $root -Verb RunAs -WindowStyle Hidden"
if errorlevel 1 pause
