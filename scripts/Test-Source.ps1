$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$failed = $false
Get-ChildItem $PSScriptRoot -Filter '*.ps1' | ForEach-Object {
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$parseErrors) | Out-Null
    if ($parseErrors.Count) {
        $failed = $true
        $parseErrors | ForEach-Object { Write-Warning $_.Message }
    }
}
foreach ($relative in @('RecoveryPE.code-workspace','.vscode\tasks.json','vendor\manifest.json','apps\catalog.json')) {
    Get-Content (Join-Path $project $relative) -Raw | ConvertFrom-Json | Out-Null
}
if ($failed) { throw 'PowerShell syntax validation failed.' }
foreach ($script in Get-ChildItem (Join-Path $project 'desktop') -Filter '*.vbs') {
    # Compile the complete VBScript but exit before any startup actions can run on the host.
    $probe = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString() + '.vbs')
    try {
        $body = (Get-Content $script.FullName -Raw) -replace '(?im)^Option Explicit\s*$', ''
        Set-Content $probe ("Option Explicit`r`nWScript.Quit 0`r`n" + $body) -Encoding ASCII
        $probeOutput = & cscript.exe //nologo $probe 2>&1
        if ($LASTEXITCODE -ne 0 -or $probeOutput) { throw "VBScript syntax validation failed: $($script.Name): $probeOutput" }
    } finally { Remove-Item -LiteralPath $probe -ErrorAction SilentlyContinue }
}
$testOutput = & cscript.exe //nologo (Join-Path $project 'tests\Test-ExternalApps.vbs') 2>&1
if ($LASTEXITCODE -ne 0 -or ($testOutput -join "`n") -ne 'External media discovery and command-line tests passed.') { throw "External app runtime helper checks failed: $testOutput" }
Write-Host $testOutput
Write-Host 'PowerShell syntax and workspace JSON checks passed. Runtime testing still requires WinPE.' -ForegroundColor Green
