' Starts the existing preview through normal Windows UAC. No settings are changed.
Option Explicit
Dim fs, root, python, script, app, arguments
If WScript.Arguments.Count > 0 Then
    If WScript.Arguments.Item(0) = "--validate-only" Then WScript.Quit 0
End If
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
python = "C:\SimplicityAI-Lab\ThemHands\.venv\Scripts\pythonw.exe"
script = fs.BuildPath(root, "desktop_preview.py")
If Not fs.FileExists(python) Or Not fs.FileExists(script) Then
    MsgBox "The preview runtime or source is missing.", 16, "SimplicityAI"
    WScript.Quit 1
End If
arguments = Chr(34) & script & Chr(34) & " --batch"
Set app = CreateObject("Shell.Application")
app.ShellExecute python, arguments, root, "runas", 1
