@echo off
wpeinit
set USERPROFILE=X:\Users\Default
set APPDATA=%USERPROFILE%\AppData\Roaming
set LOCALAPPDATA=%USERPROFILE%\AppData\Local
cscript.exe //nologo X:\RecoveryPE\InitDesktop.vbs
start "RecoveryPE launcher" mshta.exe X:\RecoveryPE\RecoveryPE.hta
start "" /wait "X:\Program Files\WinXShell\WinXShell.exe" -winpe
echo Desktop shell exited. You can restart it with:
echo "X:\Program Files\WinXShell\WinXShell.exe" -winpe
