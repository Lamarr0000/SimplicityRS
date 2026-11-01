$ErrorActionPreference='Stop'
$target='C:\SimplicityAI\ThemHands'
$source=Join-Path $PSScriptRoot 'App-Window-Update'
if(-not(Test-Path -LiteralPath "$target\app.py")){throw 'Expected SimplicityAI installation missing. No files changed.'}
$running=@(Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -like 'python*' -and $_.CommandLine -like '*app.py*' -and $_.CommandLine -like '*C:\SimplicityAI\ThemHands*') -or
    $_.ExecutablePath -eq "$target\window-runtime\SimplicityAI.exe"
})
if($running.Count){throw 'Exit SimplicityAI first. For the old browser build use Stop-ThemHands-VM.cmd. No files changed.'}
$manifest=Get-Content -LiteralPath (Join-Path $source 'payload.json') -Raw | ConvertFrom-Json
foreach($item in $manifest.files.PSObject.Properties){
    if($item.Name -notmatch '^(window-runtime/)?[A-Za-z0-9._-]+$'){throw 'Invalid package filename'}
    $path=Join-Path $source $item.Name
    if(-not(Test-Path -LiteralPath $path)){throw "Missing update file: $($item.Name)"}
    if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value){throw "Update file hash mismatch: $($item.Name)"}
}
$backup=Join-Path $target ('backup-app-window-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach($item in $manifest.files.PSObject.Properties){
    $destination=Join-Path $target $item.Name
    if(Test-Path -LiteralPath $destination){
        $saved=Join-Path $backup $item.Name
        New-Item -ItemType Directory -Force -Path (Split-Path $saved) | Out-Null
        Copy-Item -LiteralPath $destination -Destination $saved
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
    Copy-Item -LiteralPath (Join-Path $source $item.Name) -Destination $destination
}
Write-Host "Installed SimplicityAI app window 0.5.1. Previous files: $backup"
Write-Host 'Open Start-ThemHands.cmd as before. Exit or the window X stops the app and its local service.'
Write-Host 'The window requires the Microsoft Edge WebView2 Runtime normally included with Windows 11. No model download, microphone recording or network/security setting changes were performed.'
