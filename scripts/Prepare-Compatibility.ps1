[CmdletBinding()]
param(
    [string]$BuilderRoot = 'C:\SimplicityBRS-Compatibility\builder\Win10XPE',
    [string]$SourceRoot = 'H:\',
    [string]$WorkspaceRoot = 'C:\SimplicityBRS-Compatibility'
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$core = Join-Path $BuilderRoot 'Projects\Win10XPE\Core.script'
if (!(Test-Path -LiteralPath $core)) { throw 'Extract the official Win10XPE 2023-08-23 package first.' }
if (!(Test-Path -LiteralPath (Join-Path $SourceRoot 'sources\install.wim'))) { throw 'Source must be a mounted/extracted Windows ISO with install.wim.' }
$sourceVersion = (Get-Item -LiteralPath (Join-Path $SourceRoot 'setup.exe')).VersionInfo
if ($sourceVersion.FileBuildPart -ne 22000) { throw 'This first comparison preset was prepared for the available Windows 11 build 22000 source only.' }
$stagedSource = Join-Path $WorkspaceRoot 'WindowsSource'
New-Item -ItemType Directory -Force -Path $stagedSource | Out-Null
# Copy only: no mirror/delete switches, no changes to the mounted ISO.
& robocopy.exe $SourceRoot $stagedSource /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -ge 8) { throw "Windows source staging failed: $LASTEXITCODE" }

$backup = $core + '.before-simplicity'
if (!(Test-Path -LiteralPath $backup)) { Copy-Item -LiteralPath $core -Destination $backup }
$text = Get-Content -LiteralPath $core -Raw
foreach ($setting in @('Admin_CheckBox','Network_CheckBox','WoW64_CheckBox','Explorer_RadioButton','VCRuntime_CheckBox','Custom_CheckBox')) {
    $pattern = '(?m)^(' + [regex]::Escape($setting) + '=.*?,)(False|True)(,.*)$'
    if ($text -notmatch $pattern) { throw "Builder interface changed: $setting" }
    $text = [regex]::Replace($text, $pattern, '${1}True${3}')
}
# Retain external Programs and use Explorer rather than WinXShell.
foreach ($setting in @('AllInRam_CheckBox','WinXShell_RadioButton','DrvInstPatch_CheckBox')) {
    $pattern = '(?m)^(' + [regex]::Escape($setting) + '=.*?,)(False|True)(,.*)$'
    if ($text -notmatch $pattern) { throw "Builder interface changed: $setting" }
    $text = [regex]::Replace($text, $pattern, '${1}False${3}')
}
Set-Content -LiteralPath $core -Value $text -NoNewline -Encoding Default
$isoScript = Join-Path $BuilderRoot 'Projects\Win10XPE\CreateISO.script'
$isoText = Get-Content -LiteralPath $isoScript -Raw
$isoText = [regex]::Replace($isoText, '(?m)^(IsoRoot_CheckBox=.*?,)(False|True)(,.*)$', '${1}True${3}')
Set-Content -LiteralPath $isoScript -Value $isoText -NoNewline -Encoding Default

$payload = Join-Path $BuilderRoot 'Custom\x64\IsoRoot\Programs\SimplicityTest\NotepadPP'
$desktop = Join-Path $BuilderRoot 'Custom\x64\AdditionalFiles\Users\Public\Desktop'
New-Item -ItemType Directory -Force -Path $payload,$desktop | Out-Null
$app = (Get-Content (Join-Path $project 'apps\catalog.json') -Raw | ConvertFrom-Json).apps | Where-Object id -eq 'notepadpp'
$archive = Join-Path $project ('vendor\' + ($app.downloadUrl.Split('/')[-1]))
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $app.archiveSha256) { throw 'Notepad++ archive checksum mismatch.' }
Expand-Archive -LiteralPath $archive -DestinationPath $payload -Force
$testLauncher = @'
@echo off
set "NPP=Y:\Programs\SimplicityTest\NotepadPP\notepad++.exe"
if not exist "%NPP%" (
  echo The external application media was not mounted at Y:.
  pause
  exit /b 1
)
if not exist "%TEMP%\SimplicityNppSettings" mkdir "%TEMP%\SimplicityNppSettings"
start "" /D "%TEMP%" "%NPP%" -multiInst -nosession -noPlugin -settingsDir="%TEMP%\SimplicityNppSettings"
'@
Set-Content -LiteralPath (Join-Path $desktop 'Test latest Notepad++.cmd') -Value $testLauncher -Encoding ASCII
Copy-Item -LiteralPath (Join-Path $project 'assets\SimplicityBRS-background.jpg') -Destination (Join-Path $BuilderRoot 'Custom\Wallpaper\img0.jpg')
Write-Host "Compatibility preset staged. Source folder: $stagedSource"
Write-Host 'No image has been built. Open the builder as administrator, select this source folder and an x64 edition, review Build Core, then build.'
Write-Host 'Keep VMware user-operated. Test filename entry, Save, File > Open, and double-click before porting the main launcher.'
