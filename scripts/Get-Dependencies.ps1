[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$manifest = Get-Content (Join-Path $project 'vendor\manifest.json') -Raw | ConvertFrom-Json
$vendor = Join-Path $project 'vendor'
$shellDir = Join-Path $vendor 'WinXShell'
$explorerDir = Join-Path $vendor 'ExplorerPP'
New-Item -ItemType Directory -Path $shellDir,$explorerDir -Force | Out-Null
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
foreach ($file in $manifest.files | Where-Object { $_.path.StartsWith('vendor/WinXShell/') }) {
    $relative = $file.path.Substring('vendor/WinXShell/'.Length)
    $target = Join-Path $shellDir $relative
    if ((Test-Path $target) -and ((Get-FileHash $target -Algorithm SHA256).Hash -eq $file.sha256)) { continue }
    New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
    $url = 'https://raw.githubusercontent.com/slorelee/wimbuilder2/{0}/vendor/WinXShell/X_PF/WinXShell/{1}' -f $manifest.winxshellCommit,$relative
    Invoke-WebRequest -UseBasicParsing $url -OutFile $target
    if ((Get-FileHash $target -Algorithm SHA256).Hash -ne $file.sha256) { throw "Downloaded file checksum mismatch: $relative" }
}
$explorerFiles = @($manifest.files | Where-Object { $_.path.StartsWith('vendor/ExplorerPP/') })
$needsExplorer = $false
foreach ($file in $explorerFiles) {
    $target = Join-Path $project $file.path
    if (!(Test-Path $target)) { $needsExplorer = $true; break }
    if ((Get-FileHash $target -Algorithm SHA256).Hash -ne $file.sha256) { $needsExplorer = $true; break }
}
if ($needsExplorer) {
    $archive = Join-Path $vendor 'explorerpp_x64.zip'
    $url = 'https://github.com/derceg/explorerplusplus/releases/download/version-{0}/explorerpp_x64.zip' -f $manifest.explorerPlusPlusVersion
    Invoke-WebRequest -UseBasicParsing $url -OutFile $archive
    Expand-Archive $archive $explorerDir -Force
}
foreach ($file in $manifest.files) {
    $target = Join-Path $project $file.path
    if ((Get-FileHash $target -Algorithm SHA256).Hash -ne $file.sha256) { throw "Dependency checksum mismatch: $($file.path)" }
}
Write-Host 'Dependencies are present and match the recorded SHA-256 checksums.' -ForegroundColor Green
$catalog = Get-Content (Join-Path $project 'apps\catalog.json') -Raw | ConvertFrom-Json
foreach ($app in $catalog.apps) {
    $archive = Join-Path $vendor ($app.downloadUrl.Split('/')[-1])
    if (!(Test-Path $archive) -or ((Get-FileHash $archive -Algorithm SHA256).Hash -ne $app.archiveSha256)) {
        Invoke-WebRequest -UseBasicParsing $app.downloadUrl -OutFile $archive
    }
    if ((Get-FileHash $archive -Algorithm SHA256).Hash -ne $app.archiveSha256) { throw "App checksum mismatch: $($app.name)" }
    $destination = Join-Path $vendor $app.vendorDirectory
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Expand-Archive -LiteralPath $archive -DestinationPath $destination -Force
    Write-Host "$($app.name) $($app.version) downloaded and checksum verified."
}
