param([ValidateSet('inventory','export')][string]$Operation,[string]$Source,[string]$Destination)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
try {
    $admin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $admin) {throw 'Administrator permission required. Reopen the isolated Voice Pilot as administrator; no export was performed.'}
    Import-Module Dism -ErrorAction Stop
    $options=@{ErrorAction='Stop';WarningAction='SilentlyContinue'}
    if ($Source -eq 'online') {$options.Online=$true} else {$options.Path=$Source}
    if ($Operation -eq 'inventory') {$rows=@(Get-WindowsDriver @options)}
    else {
        $options.Destination=$Destination
        $options.LogPath=Join-Path $Destination 'dism-export.log'
        $options.ScratchDirectory=Join-Path $Destination 'scratch'
        [void][IO.Directory]::CreateDirectory($options.ScratchDirectory)
        $rows=@(Export-WindowsDriver @options)
    }
    $records=@($rows | Select-Object Driver,OriginalFileName,ProviderName,ClassName,Version,Date,BootCritical)
    @{ok=$true;packages=$records;count=$records.Count;operation=$Operation} | ConvertTo-Json -Depth 5 -Compress
} catch {
    @{ok=$false;error=$_.Exception.Message;operation=$Operation} | ConvertTo-Json -Compress
    exit 1
}
