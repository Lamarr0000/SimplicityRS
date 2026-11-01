#Requires -RunAsAdministrator
$ErrorActionPreference='Stop'
$relay='C:\SimplicityAI-Lab\ModelRelay'
$python='C:\SimplicityAI-Lab\ThemHands\runtime\python\cpython-3.14.10-windows-x86_64-none\python.exe'
$name='SimplicityAI-VMModelRelay'
if(-not(Test-Path -LiteralPath $python)){throw 'Expected relay runtime missing'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$acl=New-Object Security.AccessControl.DirectorySecurity
$acl.SetAccessRuleProtection($true,$false)
foreach($account in @($identity,'S-1-5-18','S-1-5-32-544')){
    if($account -like 'S-1-*'){$principal=New-Object Security.Principal.SecurityIdentifier($account)}else{$principal=$account}
    $rule=New-Object Security.AccessControl.FileSystemAccessRule($principal,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule)
}
Set-Acl -LiteralPath $relay -AclObject $acl
if(Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue){throw 'Relay firewall rule already exists; inspect it instead of overwriting'}
New-NetFirewallRule -Name $name -DisplayName 'SimplicityAI model relay - single VM only' -Direction Inbound -Action Allow -Protocol TCP -LocalAddress '192.168.182.1' -LocalPort 11436 -RemoteAddress '192.168.182.131' -Program $python -Profile Any | Out-Null
@{ok=$true;localAddress='192.168.182.1';remoteAddress='192.168.182.131';port=11436;rule=$name}|ConvertTo-Json|Set-Content -LiteralPath "$relay\firewall-ready.json" -Encoding UTF8
