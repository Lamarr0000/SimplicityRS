param([string]$RuntimePath=(Join-Path $PSScriptRoot 'window-runtime'))
$ErrorActionPreference='Stop'
$compiler=Join-Path $env:SystemRoot 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$icon=Join-Path $PSScriptRoot '..\..\assets\SimplicityBRS.ico'
& $compiler /nologo /target:winexe /platform:x64 "/win32icon:$icon" "/win32manifest:$PSScriptRoot\AppWindow.manifest" "/out:$RuntimePath\SimplicityAI.exe" /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll "/reference:$RuntimePath\Microsoft.Web.WebView2.Core.dll" "/reference:$RuntimePath\Microsoft.Web.WebView2.WinForms.dll" (Join-Path $PSScriptRoot 'AppWindow.cs')
if($LASTEXITCODE -ne 0){throw 'Native app compilation failed'}
@'
<?xml version="1.0" encoding="utf-8" ?>
<configuration><startup><supportedRuntime version="v4.0" sku=".NETFramework,Version=v4.8"/></startup><System.Windows.Forms.ApplicationConfigurationSection><add key="DpiAwareness" value="PerMonitorV2"/></System.Windows.Forms.ApplicationConfigurationSection></configuration>
'@ | Set-Content -LiteralPath (Join-Path $RuntimePath 'SimplicityAI.exe.config') -Encoding UTF8
