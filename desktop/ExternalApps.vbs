' Shared external-media discovery helpers. Loading this file starts no apps.
Function ReadMediaId(fileSystem, path)
    On Error Resume Next
    Err.Clear
    Dim stream
    ReadMediaId = ""
    If Not fileSystem.FileExists(path) Then Exit Function
    Set stream = fileSystem.OpenTextFile(path, 1)
    If Err.Number <> 0 Then Exit Function
    ReadMediaId = Trim(Replace(Replace(stream.ReadAll, vbCr, ""), vbLf, ""))
    stream.Close
End Function

Function FindMediaRoot(fileSystem, expectedId, roots)
    Dim root, marker
    FindMediaRoot = ""
    If expectedId = "" Then Exit Function
    For Each root In roots
        marker = fileSystem.BuildPath(root, "SimplicityBRS.media")
        If ReadMediaId(fileSystem, marker) = expectedId Then
            FindMediaRoot = root
            Exit Function
        End If
    Next
End Function

Sub EnsureAppFolder(fileSystem, path)
    Dim parent
    If Len(path) = 0 Or InStr(path, "%") > 0 Then Err.Raise 1002, "EnsureAppFolder", "Invalid or unexpanded settings directory: " & path
    If fileSystem.FolderExists(path) Then Exit Sub
    parent = fileSystem.GetParentFolderName(path)
    If Len(parent) = 0 Or LCase(parent) = LCase(path) Then Err.Raise 1003, "EnsureAppFolder", "Settings directory has no accessible parent: " & path
    EnsureAppFolder fileSystem, parent
    fileSystem.CreateFolder path
End Sub

Function AppSettingsRoot(fileSystem, candidate)
    If Len(candidate) = 0 Or InStr(candidate, "%") > 0 Then candidate = CStr(fileSystem.GetSpecialFolder(2))
    AppSettingsRoot = fileSystem.BuildPath(candidate, "SimplicityBRS\NotepadPP")
End Function

Function QuoteAppPath(path)
    QuoteAppPath = Chr(34) & path & Chr(34)
End Function

Function NotepadCommand(executable, settings)
    NotepadCommand = QuoteAppPath(executable) & " -multiInst -nosession -noPlugin -settingsDir=" & QuoteAppPath(settings)
End Function
