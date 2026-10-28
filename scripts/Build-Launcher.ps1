#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
$adkRoot = 'C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit'
$work = 'C:\RecoveryPE'
$mount = Join-Path $work 'mount'
$wim = Join-Path $work 'media\sources\boot.wim'
$output = Join-Path $work 'RecoveryPE-Launcher.iso'
$source = Join-Path (Split-Path $PSScriptRoot -Parent) 'launcher'
$packages = Join-Path $adkRoot 'Windows Preinstallation Environment\amd64\WinPE_OCs'
function Invoke-Dism([string[]]$Arguments) {
    & dism.exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "DISM failed with exit code $LASTEXITCODE" }
}
if (!(Test-Path $wim)) { throw "Missing base image: $wim" }
if (Test-Path $output) { throw "Output already exists: $output. Rename it before rebuilding." }
$backup = Join-Path $work 'boot-baseline.wim'
if (!(Test-Path $backup)) { Copy-Item $wim $backup }
$mounted = $false
try {
    Invoke-Dism @('/Mount-Image',"/ImageFile:$wim",'/Index:1',"/MountDir:$mount")
    $mounted = $true
    foreach ($name in @('WinPE-Scripting','WinPE-HTA')) {
        Invoke-Dism @("/Image:$mount",'/Add-Package',"/PackagePath:$packages\$name.cab")
        Invoke-Dism @("/Image:$mount",'/Add-Package',"/PackagePath:$packages\en-us\${name}_en-us.cab")
    }
    $destination = Join-Path $mount 'RecoveryPE'
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Copy-Item "$source\RecoveryPE.hta","$source\list-disks.txt" $destination
    Copy-Item "$source\startnet.cmd" (Join-Path $mount 'Windows\System32\startnet.cmd') -Force
    Invoke-Dism @('/Unmount-Image',"/MountDir:$mount",'/Commit')
    $mounted = $false
} finally {
    if ($mounted) { & dism.exe /Unmount-Image "/MountDir:$mount" /Discard }
}
$environment = Join-Path $adkRoot 'Deployment Tools\DandISetEnv.bat'
$buildCommand = 'call "{0}" && MakeWinPEMedia /ISO "{1}" "{2}"' -f $environment,$work,$output
& $env:ComSpec /d /c $buildCommand
if ($LASTEXITCODE -ne 0) { throw 'ISO creation failed.' }
Write-Host "Created $output" -ForegroundColor Green
