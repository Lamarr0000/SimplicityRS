#Requires -RunAsAdministrator
[CmdletBinding()]
param([string]$BuildRoot = 'C:\RecoveryPE-Desktop')
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$adk = 'C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit'
$environment = Join-Path $adk 'Deployment Tools\DandISetEnv.bat'
$packages = Join-Path $adk 'Windows Preinstallation Environment\amd64\WinPE_OCs'
$BuildRoot = [IO.Path]::GetFullPath($BuildRoot)
if ($BuildRoot.Contains('"')) { throw 'Build path cannot contain a quote.' }
if (Test-Path -LiteralPath $BuildRoot) { throw "Build directory already exists: $BuildRoot. Use -BuildRoot with a new directory." }
$manifest = Get-Content (Join-Path $project 'vendor\manifest.json') -Raw | ConvertFrom-Json
foreach ($file in $manifest.files) {
    $path = Join-Path $project $file.path
    if (!(Test-Path -LiteralPath $path)) { throw "Missing dependency: $path" }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $file.sha256) { throw "Dependency checksum changed: $path" }
}
function Invoke-Dism([string[]]$Arguments) {
    & dism.exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "DISM failed with exit code $LASTEXITCODE" }
}
$copyCommand = 'call "{0}" && copype amd64 "{1}"' -f $environment,$BuildRoot
& $env:ComSpec /d /c $copyCommand
if ($LASTEXITCODE -ne 0) { throw 'Creating the fresh WinPE working directory failed.' }
$mount = Join-Path $BuildRoot 'mount'
$wim = Join-Path $BuildRoot 'media\sources\boot.wim'
$mounted = $false
try {
    Invoke-Dism @('/Mount-Image',"/ImageFile:$wim",'/Index:1',"/MountDir:$mount")
    $mounted = $true
    foreach ($name in @('WinPE-Scripting','WinPE-HTA')) {
        Invoke-Dism @("/Image:$mount",'/Add-Package',"/PackagePath:$packages\$name.cab")
        Invoke-Dism @("/Image:$mount",'/Add-Package',"/PackagePath:$packages\en-us\${name}_en-us.cab")
    }
    $recovery = Join-Path $mount 'RecoveryPE'
    New-Item -ItemType Directory -Path $recovery -Force | Out-Null
    Copy-Item (Join-Path $project 'launcher\RecoveryPE.hta'),(Join-Path $project 'launcher\list-disks.txt') $recovery
    Copy-Item (Join-Path $project 'desktop\InitDesktop.vbs') $recovery
    # Only the desktop variant gets a File Manager button.
    $htaPath = Join-Path $recovery 'RecoveryPE.hta'
    $hta = Get-Content $htaPath -Raw
    $hta = $hta.Replace('Prototype 0.1','Desktop prototype 0.2')
    $hta = $hta.Replace('<button onclick="diskReport()">','<button onclick="run(''&quot;X:\\Program Files\\ExplorerPP\\Explorer++.exe&quot;'')">File Manager</button><button onclick="diskReport()">')
    $hta = $hta.Replace('720,620','720,720')
    Set-Content $htaPath $hta -Encoding ASCII
    Copy-Item (Join-Path $project 'desktop\startnet.cmd') (Join-Path $mount 'Windows\System32\startnet.cmd') -Force
    $shell = Join-Path $mount 'Program Files\WinXShell'
    $explorer = Join-Path $mount 'Program Files\ExplorerPP'
    New-Item -ItemType Directory -Path $shell,$explorer -Force | Out-Null
    Copy-Item (Join-Path $project 'vendor\WinXShell\*') $shell -Recurse
    Copy-Item (Join-Path $shell 'WinXShell_x64.exe') (Join-Path $shell 'WinXShell.exe')
    Copy-Item (Join-Path $project 'vendor\ExplorerPP\*') $explorer -Recurse
    $configPath = Join-Path $shell 'WinXShell.jcfg'
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    $config.JS_FILEEXPLORER | Add-Member -NotePropertyName '3rd_filename' -NotePropertyValue 'X:\Program Files\ExplorerPP\Explorer++.exe' -Force
    $config.JS_FILEEXPLORER.'WIN+E' | Add-Member -NotePropertyName '3rd_filename' -NotePropertyValue 'X:\Program Files\ExplorerPP\Explorer++.exe' -Force
    $config.JS_DESKTOP.bkcolor = @(21,35,51)
    $config.'::STARTMENU'.noconnections = $true
    $config.JS_DAEMON.clockarea_dbclick.command = 'cmd.exe'
    $config | ConvertTo-Json -Depth 20 | Set-Content $configPath -Encoding UTF8
    Copy-Item (Join-Path $project 'vendor\SOURCES.md') $recovery
    Invoke-Dism @('/Unmount-Image',"/MountDir:$mount",'/Commit')
    $mounted = $false
} finally {
    if ($mounted) { & dism.exe /Unmount-Image "/MountDir:$mount" /Discard }
}
$output = Join-Path $BuildRoot 'RecoveryPE-Desktop.iso'
$isoCommand = 'call "{0}" && MakeWinPEMedia /ISO "{1}" "{2}"' -f $environment,$BuildRoot,$output
& $env:ComSpec /d /c $isoCommand
if ($LASTEXITCODE -ne 0) { throw 'Desktop ISO creation failed.' }
Write-Host "Created $output" -ForegroundColor Green
