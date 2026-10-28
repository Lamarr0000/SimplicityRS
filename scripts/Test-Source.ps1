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
foreach ($relative in @('RecoveryPE.code-workspace','.vscode\tasks.json','vendor\manifest.json')) {
    Get-Content (Join-Path $project $relative) -Raw | ConvertFrom-Json | Out-Null
}
if ($failed) { throw 'PowerShell syntax validation failed.' }
Write-Host 'PowerShell syntax and workspace JSON checks passed. Runtime testing still requires WinPE.' -ForegroundColor Green
