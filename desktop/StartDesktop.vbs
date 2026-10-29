Option Explicit
Dim sh, environment, result
Set sh = CreateObject("WScript.Shell")
Set environment = sh.Environment("PROCESS")

' Winpeshl waits for this windowless host instead of a startup console.
result = sh.Run("wpeinit.exe", 0, True)
If result <> 0 Then StartupFailure "Windows PE initialization failed: " & result

environment("USERPROFILE") = "X:\Users\Default"
environment("APPDATA") = "X:\Users\Default\AppData\Roaming"
environment("LOCALAPPDATA") = "X:\Users\Default\AppData\Local"
result = sh.Run("cscript.exe //nologo X:\RecoveryPE\InitDesktop.vbs", 0, True)
If result <> 0 Then StartupFailure "Desktop shortcut setup failed: " & result

sh.Run "mshta.exe X:\RecoveryPE\RecoveryPE.hta", 1, False
' Keep the startup host alive for the lifetime of the desktop shell.
' Command prompts launched from the desktop are independent child tools.
result = sh.Run("""X:\Program Files\WinXShell\WinXShell.exe"" -winpe", 1, True)
If result <> 0 Then StartupFailure "Desktop shell exited with an error: " & result

Sub StartupFailure(message)
    MsgBox message & vbCrLf & "A diagnostic command prompt will open.", 16, "SimplicityBRS startup"
    sh.Run "cmd.exe /k", 1, True
    WScript.Quit 1
End Sub
