Option Explicit
Dim fs, sh, library, folder, expectedId, drive, roots(), count, media, executable, settings
Set fs = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
Set library = fs.OpenTextFile(fs.BuildPath(folder, "ExternalApps.vbs"), 1)
ExecuteGlobal library.ReadAll
library.Close
If WScript.Arguments.Count <> 1 Then Fail "No application was selected."
If LCase(WScript.Arguments(0)) <> "notepadpp" Then Fail "Unknown application."
expectedId = ReadMediaId(fs, fs.BuildPath(folder, "media-id.txt"))
count = 0
For Each drive In fs.Drives
    If drive.IsReady Then
        ReDim Preserve roots(count)
        roots(count) = drive.RootFolder.Path
        count = count + 1
    End If
Next
If count = 0 Then Fail "No ready application media was found."
media = FindMediaRoot(fs, expectedId, roots)
If media = "" Then Fail "Attach this build's ISO or USB containing the Programs folder, then try again."
executable = fs.BuildPath(media, "Programs\NotepadPP\notepad++.exe")
If Not fs.FileExists(executable) Then Fail "Notepad++ is missing from the application media."
settings = AppSettingsRoot(fs, sh.ExpandEnvironmentStrings("%LOCALAPPDATA%"))
On Error Resume Next
EnsureAppFolder fs, settings
If Err.Number <> 0 Then Fail "Could not prepare writable settings: " & Err.Description
On Error GoTo 0
On Error Resume Next
sh.CurrentDirectory = sh.ExpandEnvironmentStrings("%USERPROFILE%") & "\Documents"
If Err.Number <> 0 Then
    Err.Clear
    sh.CurrentDirectory = CStr(fs.GetSpecialFolder(2))
End If
On Error GoTo 0
sh.Run NotepadCommand(executable, settings), 1, False

Sub Fail(message)
    MsgBox message, 48, "SimplicityBRS applications"
    WScript.Quit 1
End Sub
