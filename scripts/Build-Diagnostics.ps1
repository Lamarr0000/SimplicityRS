[CmdletBinding()]
param([string]$OutputDirectory = 'C:\Simplicity-Diagnostics')
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$zig = Join-Path $env:LOCALAPPDATA 'SimplicityBRS\toolchains\zig-x86_64-windows-0.15.2\zig.exe'
if (!(Test-Path $zig)) { throw 'Diagnostic compiler missing. See diagnostics/README.md.' }
$oscdimg = 'C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe'
if (Test-Path $OutputDirectory) { throw 'Choose a new output directory to preserve earlier diagnostics.' }
$payload = Join-Path $OutputDirectory 'media'
New-Item -ItemType Directory -Path $payload -Force | Out-Null
$executable = Join-Path $payload 'FileDialogProbe.exe'
& $zig cc -target x86_64-windows-gnu -Os -municode (Join-Path $project 'diagnostics\FileDialogProbe.c') -o $executable -lole32 -lshell32 -luuid
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic compilation failed.' }
$reference = Join-Path $payload 'FullWindows'
New-Item -ItemType Directory -Path (Join-Path $reference 'en-US') -Force | Out-Null
foreach ($relative in @('comdlg32.dll','en-US\comdlg32.dll.mui')) {
    $source = Join-Path $env:SystemRoot ('System32\' + $relative)
    if ((Get-AuthenticodeSignature -LiteralPath $source).Status -ne 'Valid') { throw "Windows reference signature invalid: $source" }
    if ((Get-Item -LiteralPath $source).VersionInfo.ProductBuildPart -ne 26100) { throw 'Reference DLL must be from Windows build family 26100 for this PE comparison.' }
    Copy-Item -LiteralPath $source -Destination (Join-Path $reference $relative)
}
@('@echo off','"%~dp0FileDialogProbe.exe" --wait') | Set-Content (Join-Path $payload 'Run-Diagnostic.cmd') -Encoding ASCII
Copy-Item (Join-Path $project 'diagnostics\README.md') $payload
$iso = Join-Path $OutputDirectory 'Simplicity-Diagnostics.iso'
& $oscdimg -n -lSIMPLICITY_DIAG $payload $iso
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic ISO creation failed.' }
Write-Host "Created $iso" -ForegroundColor Green
