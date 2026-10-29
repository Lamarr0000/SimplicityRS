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
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\AppData", profile & "\AppData\Roaming", "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\AppData", profile & "\AppData\Roaming", "REG_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\Start Menu", fs.GetParentFolderName(programs), "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Start Menu", fs.GetParentFolderName(programs), "REG_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\Desktop", desktop, "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Desktop", desktop, "REG_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders\Programs", programs, "REG_EXPAND_SZ"
sh.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Programs", programs, "REG_SZ"
AddLink "SimplicityBRS", "X:\Windows\System32\mshta.exe", "X:\RecoveryPE\RecoveryPE.hta"
AddLink "File Manager", "X:\Program Files\ExplorerPP\Explorer++.exe", ""
AddLink "Command Prompt", "X:\Windows\System32\cmd.exe", ""
AddLink "Notepad", "X:\Windows\System32\notepad.exe", ""
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
    link.Save
  Next
End Sub
