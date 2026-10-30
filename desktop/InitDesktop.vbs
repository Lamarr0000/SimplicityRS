Option Explicit
Dim sh, fs, profile, desktop, programs, quicklaunch
Set sh = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
profile = sh.ExpandEnvironmentStrings("%USERPROFILE%")
desktop = profile & "\Desktop"
programs = profile & "\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
quicklaunch = profile & "\AppData\Roaming\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
EnsureFolder desktop
EnsureFolder programs
EnsureFolder quicklaunch
EnsureFolder profile & "\AppData\Local"
EnsureFolder profile & "\Documents"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\Personal", profile & "\Documents", "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Personal", profile & "\Documents", "REG_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\AppData", profile & "\AppData\Roaming", "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\AppData", profile & "\AppData\Roaming", "REG_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\Start Menu", fs.GetParentFolderName(programs), "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Start Menu", fs.GetParentFolderName(programs), "REG_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\Desktop", desktop, "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Desktop", desktop, "REG_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\Programs", programs, "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Programs", programs, "REG_SZ"
' Use a direct Win32 text handler in the PE session rather than an inherited
' shell association that may require an interactive user token or app activation.
sh.RegWrite "HKCU\Software\Classes\.txt\", "SimplicityBRS.Text", "REG_SZ"
sh.RegWrite "HKCU\Software\Classes\SimplicityBRS.Text\", "Text document", "REG_SZ"
sh.RegWrite "HKCU\Software\Classes\SimplicityBRS.Text\DefaultIcon\", "X:\Windows\System32\notepad.exe,0", "REG_SZ"
sh.RegWrite "HKCU\Software\Classes\SimplicityBRS.Text\shell\", "open", "REG_SZ"
sh.RegWrite "HKCU\Software\Classes\SimplicityBRS.Text\shell\open\command\", """X:\Windows\System32\notepad.exe"" ""%1""", "REG_SZ"
AddLink "SimplicityBRS", "X:\Windows\System32\mshta.exe", "X:\RecoveryPE\RecoveryPE.hta"
AddLink "File Manager", "X:\Program Files\ExplorerPP\Explorer++.exe", ""
AddLink "Command Prompt", "X:\Windows\System32\cmd.exe", ""
AddLink "Notepad", "X:\Windows\System32\notepad.exe", ""
AddLink "Notepad++", "X:\Windows\System32\wscript.exe", "//nologo X:\RecoveryPE\LaunchApp.vbs notepadpp"
EnsureExplorerFrameRegistration
' StructuredQuery self-registration failed in Desktop-09 and did not repair
' file dialogs. Keep that unverified operation out of normal desktop startup.
Sub EnsureExplorerFrameRegistration()
    Dim key, existing
    key = "HKCR\CLSID\{056440FD-8568-48e7-A632-72157243B55B}\InprocServer32\"
    On Error Resume Next
    existing = sh.RegRead(key)
    If Err.Number = 0 And Len(existing) > 0 Then Exit Sub
    Err.Clear
    On Error GoTo 0
    key = "HKLM\SOFTWARE\Classes\CLSID\{056440FD-8568-48e7-A632-72157243B55B}\InprocServer32\"
    sh.RegWrite key, "X:\Windows\System32\ExplorerFrame.dll", "REG_SZ"
    sh.RegWrite key & "ThreadingModel", "Apartment", "REG_SZ"
End Sub
Sub EnsureFolder(path)
  If fs.FolderExists(path) Then Exit Sub
  EnsureFolder fs.GetParentFolderName(path)
  fs.CreateFolder path
End Sub
Sub AddLink(name, target, arguments)
  Dim folder, link
  For Each folder In Array(desktop, programs, quicklaunch)
    Set link = sh.CreateShortcut(folder & "\" & name & ".lnk")
    link.TargetPath = target
    link.Arguments = arguments
    link.WorkingDirectory = "X:\RecoveryPE"
    If name = "SimplicityBRS" Then link.IconLocation = "X:\RecoveryPE\SimplicityBRS.ico,0"
    If name = "Notepad++" Then link.IconLocation = "X:\Windows\System32\notepad.exe,0"
    link.Save
  Next
End Sub
