#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$BuildRoot = 'C:\RecoveryPE-Desktop',
    [string]$IconCodecSource = "$env:SystemRoot\System32\IconCodecService.dll",
    [string]$WindowsComponentSource = $env:SystemRoot
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$adk = 'C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit'
$environment = Join-Path $adk 'Deployment Tools\DandISetEnv.bat'
$packages = Join-Path $adk 'Windows Preinstallation Environment\amd64\WinPE_OCs'
$appCatalog = Get-Content (Join-Path $project 'apps\catalog.json') -Raw | ConvertFrom-Json
foreach ($app in $appCatalog.apps) {
    $appSource = Join-Path $project ('vendor\' + $app.vendorDirectory)
    if (!(Test-Path -LiteralPath (Join-Path $appSource $app.executable))) { throw 'App dependencies missing. Run scripts\Get-Dependencies.ps1 first.' }
    $archive = Join-Path $project ('vendor\' + ($app.downloadUrl.Split('/')[-1]))
    if (!(Test-Path -LiteralPath $archive)) { throw "App archive missing: $archive" }
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $app.archiveSha256) { throw "App archive checksum mismatch: $($app.name)" }
}
$mediaId = [guid]::NewGuid().ToString()
$BuildRoot = [IO.Path]::GetFullPath($BuildRoot)
if ($BuildRoot.Contains('"')) { throw 'Build path cannot contain a quote.' }
if (Test-Path -LiteralPath $BuildRoot) { throw "Build directory already exists: $BuildRoot. Use -BuildRoot with a new directory." }
foreach ($asset in @('SimplicityBRS-background.jpg','SimplicityBRS.ico')) {
    if (!(Test-Path -LiteralPath (Join-Path $project "assets\$asset"))) { throw "Missing branding asset: $asset" }
}
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
    # Modern Notepad++ embeds PNG-compressed icons. LoadIcon needs this decoder,
    # which can be absent from the minimal ADK image even with WinPE-HTA installed.
    $codecDestination = Join-Path $mount 'Windows\System32\IconCodecService.dll'
    if (!(Test-Path -LiteralPath $codecDestination)) {
        if (!(Test-Path -LiteralPath $IconCodecSource)) { throw "Icon decoder missing. Supply -IconCodecSource from matching x64 Windows media." }
        $codec = Get-Item -LiteralPath $IconCodecSource
        $peKernel = Get-Item -LiteralPath (Join-Path $mount 'Windows\System32\kernel32.dll')
        if ($codec.VersionInfo.FileBuildPart -ne $peKernel.VersionInfo.FileBuildPart -or $codec.VersionInfo.FileMajorPart -ne $peKernel.VersionInfo.FileMajorPart -or $codec.VersionInfo.FileMinorPart -ne $peKernel.VersionInfo.FileMinorPart) {
            throw 'Icon decoder Windows build does not match WinPE. Supply -IconCodecSource from matching Windows media.'
        }
        if ((Get-AuthenticodeSignature -LiteralPath $IconCodecSource).Status -ne 'Valid') { throw 'Icon decoder signature is not valid.' }
        $codecBytes = [IO.File]::ReadAllBytes($codec.FullName)
        $peOffset = [BitConverter]::ToInt32($codecBytes, 60)
        if ([BitConverter]::ToUInt16($codecBytes, $peOffset + 4) -ne 0x8664) { throw 'Icon decoder must be x64.' }
        Copy-Item -LiteralPath $codec.FullName -Destination $codecDestination
        Write-Host "Added Windows icon decoder $($codec.VersionInfo.FileVersion) for Notepad++ icon support."
    }
    # WinXShell's upstream NewBrowseDlg integration supplies these for modern
    # COM-based Open/Save dialogs. Keep existing PE binaries and add only gaps.
    $kernelVersion = (Get-Item -LiteralPath (Join-Path $mount 'Windows\System32\kernel32.dll')).VersionInfo
    # File-dialog creation also explicitly requires System32\ShellStyle.dll;
    # when absent it returns CLASS_E_CLASSNOTAVAILABLE before any dialog appears.
    foreach ($relative in @('System32\comctl32.dll','System32\ExplorerFrame.dll','System32\en-US\ExplorerFrame.dll.mui','SystemResources\ExplorerFrame.dll.mun','System32\shellstyle.dll','System32\en-US\shellstyle.dll.mui')) {
        $target = Join-Path $mount ('Windows\' + $relative)
        if (Test-Path -LiteralPath $target) { continue }
        $sourceFile = Join-Path $WindowsComponentSource $relative
        if (!(Test-Path -LiteralPath $sourceFile)) { throw "Required dialog component missing: $sourceFile" }
        $version = (Get-Item -LiteralPath $sourceFile).VersionInfo
        if ($version.ProductBuildPart -ne $kernelVersion.ProductBuildPart -or $version.ProductMajorPart -ne $kernelVersion.ProductMajorPart -or $version.ProductMinorPart -ne $kernelVersion.ProductMinorPart) {
            throw "Windows build mismatch for dialog component: $sourceFile. Supply -WindowsComponentSource from matching Windows media."
        }
        if ((Get-AuthenticodeSignature -LiteralPath $sourceFile).Status -ne 'Valid') { throw "Dialog component signature not valid: $sourceFile" }
        if ($relative.EndsWith('.dll')) {
            $componentBytes = [IO.File]::ReadAllBytes($sourceFile)
            $componentPeOffset = [BitConverter]::ToInt32($componentBytes, 60)
            if ([BitConverter]::ToUInt16($componentBytes, $componentPeOffset + 4) -ne 0x8664) { throw "Dialog component must be x64: $sourceFile" }
        }
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        Copy-Item -LiteralPath $sourceFile -Destination $target
        Write-Host "Added modern file-dialog component: $relative"
    }
    $recovery = Join-Path $mount 'RecoveryPE'
    New-Item -ItemType Directory -Path $recovery -Force | Out-Null
    Copy-Item (Join-Path $project 'launcher\RecoveryPE.hta'),(Join-Path $project 'launcher\list-disks.txt') $recovery
    Copy-Item (Join-Path $project 'assets\SimplicityBRS.ico'),(Join-Path $project 'assets\SimplicityBRS-background.jpg') $recovery
    Copy-Item (Join-Path $project 'desktop\InitDesktop.vbs'),(Join-Path $project 'desktop\StartDesktop.vbs') $recovery
    Copy-Item (Join-Path $project 'desktop\LaunchApp.vbs'),(Join-Path $project 'desktop\ExternalApps.vbs') $recovery
    Set-Content (Join-Path $recovery 'media-id.txt') $mediaId -Encoding ASCII
    # Only the desktop variant gets a File Manager button.
    $htaPath = Join-Path $recovery 'RecoveryPE.hta'
    $hta = Get-Content $htaPath -Raw
    $hta = $hta.Replace('Prototype 0.1','Desktop prototype 0.2')
    $hta = $hta.Replace('<button onclick="diskReport()">','<button onclick="run(''&quot;X:\\Program Files\\ExplorerPP\\Explorer++.exe&quot;'')">File Manager</button><button onclick="diskReport()">')
    $hta = $hta.Replace('720,620','720,720')
    $hta = $hta.Replace('<button onclick="run(''notepad.exe'')">Notepad</button>', '<button onclick="run(''notepad.exe'')">Notepad</button><button onclick="run(''wscript.exe //nologo X:\\RecoveryPE\\LaunchApp.vbs notepadpp'')">Notepad++</button>')
    $hta = $hta.Replace('scroll="no"','scroll="yes"')
    Set-Content $htaPath $hta -Encoding ASCII
    Copy-Item (Join-Path $project 'desktop\winpeshl.ini') (Join-Path $mount 'Windows\System32\winpeshl.ini') -Force
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
    $config.JS_DESKTOP.'::WP' = 'X:\RecoveryPE\SimplicityBRS-background.jpg'
    $config.JS_DESKTOP.'::WP_MODE' = 0
    $config.'::STARTMENU'.noconnections = $true
    $config.JS_DAEMON.clockarea_dbclick.command = 'cmd.exe'
    $config | ConvertTo-Json -Depth 20 | Set-Content $configPath -Encoding UTF8
    Copy-Item (Join-Path $project 'vendor\SOURCES.md') $recovery
    Invoke-Dism @('/Unmount-Image',"/MountDir:$mount",'/Commit')
    $mounted = $false
} finally {
    if ($mounted) { & dism.exe /Unmount-Image "/MountDir:$mount" /Discard }
}
Copy-Item (Join-Path $project 'assets\SimplicityBRS.ico') (Join-Path $BuildRoot 'media\SimplicityBRS.ico')
Set-Content (Join-Path $BuildRoot 'media\SimplicityBRS.media') $mediaId -Encoding ASCII
foreach ($app in $appCatalog.apps) {
    $appDestination = Join-Path $BuildRoot ('media\Programs\' + $app.vendorDirectory)
    New-Item -ItemType Directory -Path $appDestination -Force | Out-Null
    # Extract the verified archive afresh so locally modified vendor files cannot enter the ISO.
    $archive = Join-Path $project ('vendor\' + ($app.downloadUrl.Split('/')[-1]))
    Expand-Archive -LiteralPath $archive -DestinationPath $appDestination
}
@('[autorun]','icon=SimplicityBRS.ico','label=SimplicityBRS - Backup and Recovery Suite') | Set-Content (Join-Path $BuildRoot 'media\autorun.inf') -Encoding ASCII
$output = Join-Path $BuildRoot 'SimplicityBRS-Desktop.iso'
$isoCommand = 'call "{0}" && MakeWinPEMedia /ISO "{1}" "{2}"' -f $environment,$BuildRoot,$output
& $env:ComSpec /d /c $isoCommand
if ($LASTEXITCODE -ne 0) { throw 'Desktop ISO creation failed.' }
Write-Host "Created $output" -ForegroundColor Green
