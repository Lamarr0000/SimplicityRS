Option Explicit
Dim sh
Set sh = CreateObject("WScript.Shell")
' Run inside the existing Explorer session; do not replace PECMD/profile setup.
sh.RegWrite "HKCU\Software\Classes\.txt\", "SimplicityBRS.Text", "REG_SZ"
sh.RegWrite "HKCU\Software\Classes\SimplicityBRS.Text\", "Text document", "REG_SZ"
sh.RegWrite "HKCU\Software\Classes\SimplicityBRS.Text\shell\", "open", "REG_SZ"
sh.RegWrite "HKCU\Software\Classes\SimplicityBRS.Text\shell\open\command\", """X:\Windows\System32\notepad.exe"" ""%1""", "REG_SZ"
' Explicitly show only This PC and Recycle Bin among Explorer namespace icons.
Dim mode, item, base
For Each mode In Array("NewStartPanel", "ClassicStartMenu")
    base = "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\" & mode & "\"
    For Each item In Array("{59031a47-3f72-44a7-89c5-5595fe6b30ee}", "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}", "{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}", "{645FF040-5081-101B-9F08-00AA002F954E}", "{20D04FE0-3AEA-1069-A2D8-08002B30309D}")
        If item = "{645FF040-5081-101B-9F08-00AA002F954E}" Or item = "{20D04FE0-3AEA-1069-A2D8-08002B30309D}" Then
            sh.RegWrite base & item, 0, "REG_DWORD"
        Else
            sh.RegWrite base & item, 1, "REG_DWORD"
        End If
    Next
Next
sh.Run "mshta.exe X:\RecoveryPE\RecoveryPE.hta", 1, False
