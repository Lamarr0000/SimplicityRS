Option Explicit
Dim fs, source, project, stream, root, first, second, command
Set fs = CreateObject("Scripting.FileSystemObject")
project = fs.GetParentFolderName(fs.GetParentFolderName(WScript.ScriptFullName))
Set source = fs.OpenTextFile(fs.BuildPath(project, "desktop\ExternalApps.vbs"), 1)
ExecuteGlobal source.ReadAll
source.Close
root = fs.BuildPath(fs.GetSpecialFolder(2), fs.GetTempName)
fs.CreateFolder root
first = fs.BuildPath(root, "OtherMedia")
second = fs.BuildPath(root, "CurrentMedia")
fs.CreateFolder first
fs.CreateFolder second
Set stream = fs.CreateTextFile(fs.BuildPath(first, "SimplicityBRS.media"), True)
stream.WriteLine "older-build"
stream.Close
Set stream = fs.CreateTextFile(fs.BuildPath(second, "SimplicityBRS.media"), True)
stream.WriteLine "current-build"
stream.Close
AssertEqual FindMediaRoot(fs, "current-build", Array(first, second)), second, "Select matching build instead of first media"
AssertEqual FindMediaRoot(fs, "missing-build", Array(first, second)), "", "Reject mismatched media"
AssertEqual FindMediaRoot(fs, "", Array(first, second)), "", "Reject empty build ID"
AssertEqual FindMediaRoot(fs, "current-build", Array(root, second)), second, "Skip roots without marker"
command = NotepadCommand("D:\Programs\NotepadPP\notepad++.exe", "X:\User Settings\NotepadPP")
AssertEqual command, """D:\Programs\NotepadPP\notepad++.exe"" -multiInst -nosession -noPlugin -settingsDir=""X:\User Settings\NotepadPP""", "Quote executable and writable settings paths"
EnsureAppFolder fs, fs.BuildPath(root, "Settings\Editor")
If Not fs.FolderExists(fs.BuildPath(root, "Settings\Editor")) Then Err.Raise 1001, , "Settings directory creation failed"
AssertEqual AppSettingsRoot(fs, "%LOCALAPPDATA%"), fs.BuildPath(CStr(fs.GetSpecialFolder(2)), "SimplicityBRS\NotepadPP"), "Fallback when PE leaves LOCALAPPDATA undefined"
AssertEqual AppSettingsRoot(fs, root), fs.BuildPath(root, "SimplicityBRS\NotepadPP"), "Retain valid app data path"
On Error Resume Next
EnsureAppFolder fs, ""
If Err.Number <> 1002 Then WScript.Quit 1
Err.Clear
EnsureAppFolder fs, "%LOCALAPPDATA%\Missing"
If Err.Number <> 1002 Then WScript.Quit 1
Err.Clear
On Error GoTo 0
fs.DeleteFile fs.BuildPath(first, "SimplicityBRS.media")
fs.DeleteFile fs.BuildPath(second, "SimplicityBRS.media")
fs.DeleteFolder first
fs.DeleteFolder second
fs.DeleteFolder fs.BuildPath(root, "Settings\Editor")
fs.DeleteFolder fs.BuildPath(root, "Settings")
fs.DeleteFolder root
WScript.Echo "External media discovery and command-line tests passed."
Sub AssertEqual(actual, expected, description)
    If actual <> expected Then
        WScript.Echo description & ": unexpected result " & actual
        WScript.Quit 1
    End If
End Sub
