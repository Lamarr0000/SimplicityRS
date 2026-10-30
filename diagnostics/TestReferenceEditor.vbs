Option Explicit
Dim shell, fs, source, target, settings
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
If LCase(shell.ExpandEnvironmentStrings("%SystemRoot%")) <> "x:\windows" Then
    MsgBox "Run this compatibility test inside the recovery VM.", 48, "Simplicity reference test"
    WScript.Quit 1
End If
source = fs.BuildPath(fs.GetParentFolderName(WScript.ScriptFullName), "ReferenceNotepadPP")
target = "X:\Windows\Temp\SimplicityLegacyEditor-x64"
If Not fs.FolderExists(target) Then fs.CopyFolder source, target
Set settings = fs.CreateTextFile(fs.BuildPath(target, "config.xml"), True)
settings.WriteLine "<?xml version=""1.0"" encoding=""UTF-8"" ?>"
settings.WriteLine "<NotepadPlus><GUIConfigs>"
settings.WriteLine "<GUIConfig name=""MISC"" newStyleSaveDlg=""no"" />"
settings.WriteLine "<GUIConfig name=""noUpdate"">yes</GUIConfig>"
settings.WriteLine "<GUIConfig name=""RememberLastSession"">no</GUIConfig>"
settings.WriteLine "</GUIConfigs></NotepadPlus>"
settings.Close
shell.CurrentDirectory = target
shell.Run """" & fs.BuildPath(target, "notepad++.exe") & """ -multiInst -nosession -noPlugin", 1, False
