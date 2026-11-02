param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('system','storage','devices','drivers','services','events','updates','security','startup')]
    [string]$Area,
    [ValidateLength(0,80)][string]$Query=''
)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$result=[ordered]@{area=$Area;scope='Windows running SimplicityAI only';checked_utc=[DateTime]::UtcNow.ToString('o');changes_made=$false;sections=@();limitations=@('Read-only observations are not a diagnosis. Unavailable checks remain unknown. Results may be bounded; no repairs or setting changes requested.')}
function Section([string]$Name,[scriptblock]$Collect) {
    try {
        $rows=@(& $Collect)
        if ($Query) {$rows=@($rows | Where-Object {($_ | ConvertTo-Json -Depth 4 -Compress).IndexOf($Query,[StringComparison]::OrdinalIgnoreCase) -ge 0})}
        $section=@{name=$Name;status='available';matching_count=$rows.Count;returned_count=[Math]::Min(20,$rows.Count);truncated=($rows.Count -gt 20);data=@($rows | Select-Object -First 20)}
        if ($Name -like 'Device Manager*') {$section.problem_count=@($rows | Where-Object {$null -ne $_.ConfigManagerErrorCode -and $_.ConfigManagerErrorCode -ne 0}).Count}
        $result.sections+=$section
    } catch {
        if ($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound*') {$result.sections+=@{name=$Name;status='available';matching_count=0;returned_count=0;truncated=$false;data=@();note='No matching records in this bounded query.'}}
        else {$result.sections+=@{name=$Name;status='unknown';reason=$_.Exception.Message}}
    }
}
function Read-Events([string]$Log,[int[]]$Levels,[int]$Days,[int]$Maximum,[string]$Provider='') {
    $levelsExpression=($Levels | ForEach-Object {"Level=$_"}) -join ' or '
    $milliseconds=[long]$Days*24*60*60*1000
    $providerExpression=if ($Provider) {" and Provider[@Name='$Provider']"} else {''}
    $xpath="*[System[($levelsExpression) and TimeCreated[timediff(@SystemTime) <= $milliseconds]$providerExpression]]"
    $queryObject=New-Object System.Diagnostics.Eventing.Reader.EventLogQuery($Log,[System.Diagnostics.Eventing.Reader.PathType]::LogName,$xpath)
    $queryObject.ReverseDirection=$true
    $reader=New-Object System.Diagnostics.Eventing.Reader.EventLogReader($queryObject)
    try {
        for ($i=0;$i -lt $Maximum;$i++) {
            $event=$reader.ReadEvent()
            if ($null -eq $event) {break}
            try {
                $message=try {$event.FormatDescription()} catch {'Message unavailable'}
                [pscustomobject]@{TimeCreatedUTC=$event.TimeCreated.ToUniversalTime().ToString('o');ProviderName=$event.ProviderName;Id=$event.Id;Level=$event.Level;Message=if ($message) {$message.Substring(0,[Math]::Min(400,$message.Length))} else {''}}
            } finally {$event.Dispose()}
        }
    } finally {$reader.Dispose()}
}
switch ($Area) {
    'system' {
        Section 'Windows' {Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,LastBootUpTime,TotalVisibleMemorySize,FreePhysicalMemory}
        Section 'Computer' {Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,NumberOfLogicalProcessors,TotalPhysicalMemory}
        Section 'Processor' {Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors}
        Section 'Graphics' {Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,DriverDate,Status,ConfigManagerErrorCode}
    }
    'storage' {
        Section 'Volumes; bytes, decimal GB and binary GiB are explicitly distinguished' {Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,VolumeName,DriveType,FileSystem,Size,FreeSpace,@{Name='SizeGiB';Expression={if ($null -ne $_.Size){[Math]::Round($_.Size/1GB,2)}else{$null}}},@{Name='FreeGiB';Expression={if ($null -ne $_.FreeSpace){[Math]::Round($_.FreeSpace/1GB,2)}else{$null}}},@{Name='SizeGB';Expression={if ($null -ne $_.Size){[Math]::Round($_.Size/1000000000,2)}else{$null}}},@{Name='FreeGB';Expression={if ($null -ne $_.FreeSpace){[Math]::Round($_.FreeSpace/1000000000,2)}else{$null}}},@{Name='FreePercent';Expression={if ($_.Size -gt 0){[Math]::Round(100*$_.FreeSpace/$_.Size,1)}else{$null}}}}
        Section 'Disks (provider status is not a complete physical-health test)' {Get-CimInstance Win32_DiskDrive | Select-Object Index,Model,InterfaceType,Size,Status}
        Section 'Partitions' {Get-CimInstance Win32_DiskPartition | Select-Object DiskIndex,Index,Name,Type,Size,BootPartition}
        Section 'Storage health provider' {Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus,OperationalStatus,Size}
    }
    'devices' {
        Section 'Device Manager inventory; problem codes first' {Get-CimInstance Win32_PnPEntity | Sort-Object @{Expression={if ($_.ConfigManagerErrorCode -ne 0){0}else{1}}},Name | Select-Object Name,PNPClass,Status,ConfigManagerErrorCode,DeviceID}
    }
    'drivers' {
        Section 'Installed signed-driver records (not an update-availability check)' {Get-CimInstance Win32_PnPSignedDriver | Sort-Object DeviceName | Select-Object DeviceName,Manufacturer,DriverProviderName,DriverVersion,DriverDate,IsSigned,InfName}
    }
    'services' {
        Section 'Service status; stopped automatic services first' {Get-CimInstance Win32_Service | Sort-Object @{Expression={if ($_.StartMode -eq 'Auto' -and $_.State -ne 'Running'){0}else{1}}},Name | Select-Object Name,DisplayName,State,StartMode,ExitCode}
    }
    'events' {
        Section 'Newest System errors, critical events and warnings over seven days (newest 100 sampled)' {Read-Events 'System' @(1,2,3) 7 100}
        Section 'Newest Application errors over seven days (newest 40 sampled)' {Read-Events 'Application' @(1,2) 7 40}
    }
    'updates' {
        Section 'Recorded hotfixes (not a complete update history or online scan)' {Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 40 HotFixID,Description,InstalledOn}
        Section 'Recent Windows Update failure events (newest 30 sampled)' {Read-Events 'System' @(2) 14 30 'Microsoft-Windows-WindowsUpdateClient'}
    }
    'security' {
        Section 'BitLocker status only; no recovery keys' {Get-BitLockerVolume | Select-Object MountPoint,VolumeStatus,ProtectionStatus,EncryptionPercentage,LockStatus}
        Section 'TPM status' {Get-Tpm | Select-Object TpmPresent,TpmReady,TpmEnabled,TpmActivated,LockedOut,ManufacturerIdTxt,ManufacturerVersion}
        Section 'Secure Boot status' {[pscustomobject]@{SecureBootEnabled=(Confirm-SecureBootUEFI)}}
        Section 'Defender status (not a malware scan)' {Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureLastUpdated,QuickScanEndTime,FullScanEndTime}
    }
    'startup' {
        Section 'Startup entries; names and locations only, no command lines' {Get-CimInstance Win32_StartupCommand | Select-Object Name,Location}
        Section 'Power and battery status' {Get-CimInstance Win32_Battery | Select-Object Name,BatteryStatus,EstimatedChargeRemaining,EstimatedRunTime,Status}
        Section 'Current boot configuration (not boot-file integrity)' {
            $text=& "$env:SystemRoot\System32\bcdedit.exe" /enum '{current}' 2>&1
            if ($LASTEXITCODE -ne 0) {throw 'Boot configuration unavailable; administrator access or a supported BCD store may be required.'}
            [pscustomobject]@{Output=($text -join "`n");BootFileIntegrity='Not tested'}
        }
    }
}
$result | ConvertTo-Json -Depth 7 -Compress
