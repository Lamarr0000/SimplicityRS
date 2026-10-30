[CmdletBinding()]
param(
    [string]$SourceMedia = 'C:\SimplicityBRS-Compatibility\LauncherTest04\media',
    [string]$BuildRoot = 'C:\SimplicityBRS-Compatibility\CleanDesktop05',
    [string]$OutputIso = 'C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-05.iso'
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$tools = 'C:\SimplicityBRS-Compatibility\builder\Win10XPE\Projects\Tools'
$seven = "$env:LOCALAPPDATA\SimplicityBRS\toolchains\7zip\full\7z.exe"
$zig = "$env:LOCALAPPDATA\SimplicityBRS\toolchains\zig-x86_64-windows-0.15.2\zig.exe"
$oscdimg = 'C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg\oscdimg.exe'
if (Test-Path -LiteralPath $OutputIso) { throw 'Output ISO already exists.' }
if (Test-Path -LiteralPath "$BuildRoot\media") { throw 'Build media already exists.' }
New-Item -ItemType Directory -Force -Path "$BuildRoot\overlay\RecoveryPE" | Out-Null
Copy-Item -LiteralPath $SourceMedia -Destination "$BuildRoot\media" -Recurse
& $seven x "$SourceMedia\sources\boot.wim" "-o$BuildRoot\original" 'Windows\System32\Pecmd.ini' -y | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Startup extraction failed.' }
$startup = Get-Content "$BuildRoot\original\Windows\System32\Pecmd.ini" -Raw
# Do not remove Start menu links or the fixed display configuration from 02.
$startup = [regex]::Replace($startup, '(?im)^LINK %Desktop%[^\r\n]*', '// Desktop shortcut omitted by Simplicity clean-desktop preset.')
New-Item -ItemType Directory -Force -Path "$BuildRoot\overlay\Windows\System32" | Out-Null
Set-Content "$BuildRoot\overlay\Windows\System32\Pecmd.ini" $startup -Encoding ASCII
Copy-Item (Join-Path $project 'launcher\SimplicityDesktop.hta') "$BuildRoot\overlay\RecoveryPE\RecoveryPE.hta"
Copy-Item (Join-Path $project 'desktop\CompatibilityStartup.vbs') "$BuildRoot\overlay\RecoveryPE"
& $zig cc -target x86_64-windows-gnu -O2 -municode '-Wl,--subsystem,windows' (Join-Path $project 'desktop\LauncherOpacity.c') -o "$BuildRoot\overlay\RecoveryPE\LauncherOpacity.exe" -luser32
if ($LASTEXITCODE -ne 0) { throw 'Opacity helper compilation failed.' }
$commands = @("add '$BuildRoot\overlay' '/'")
foreach ($profile in @('Default','Administrator','Public')) {
    $commands += "delete '/Users/$profile/Desktop/Notepad++.lnk'"
    if ($profile -ne 'Public') { $commands += "delete '/Users/$profile/Desktop/SimplicityBRS.lnk'" }
}
$commands += "delete '/Users/Public/Desktop/Test latest Notepad++.cmd'"
$commands | & "$tools\wimlib-imagex.exe" update "$BuildRoot\media\sources\boot.wim" 1 --no-acls
if ($LASTEXITCODE -ne 0) { throw 'Clean-desktop WIM update failed.' }
& $seven x "$BuildRoot\media\sources\boot.wim" "-o$BuildRoot\verify" 'RecoveryPE\RecoveryPE.hta' 'RecoveryPE\LauncherOpacity.exe' 'Windows\System32\Pecmd.ini' -y | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Updated WIM extraction failed.' }
foreach ($relative in @('RecoveryPE\RecoveryPE.hta','RecoveryPE\LauncherOpacity.exe','Windows\System32\Pecmd.ini')) {
    if ((Get-FileHash "$BuildRoot\verify\$relative").Hash -ne (Get-FileHash "$BuildRoot\overlay\$relative").Hash) { throw "WIM verification failed: $relative" }
}
& $oscdimg -m -o -u2 -udfver102 -lSIMPLICITY_TEST "-bootdata:2#p0,e,b$BuildRoot\media\boot\etfsboot.com#pEF,e,b$BuildRoot\media\efi\microsoft\boot\efisys.bin" "$BuildRoot\media" $OutputIso
if ($LASTEXITCODE -ne 0) { throw 'ISO packaging failed.' }
Write-Host "Created: $OutputIso"
