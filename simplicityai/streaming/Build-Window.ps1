$ErrorActionPreference='Stop'
# Adapt our existing window source, not installed Codex/ChatGPT code.
$destination='C:\SimplicityAI-Lab\StreamingPrototype\window-runtime'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
$source=Join-Path $PSScriptRoot '..\prototype\AppWindow.cs'
$text=(Get-Content -LiteralPath $source -Raw).Replace('8769','8770').Replace('"SimplicityAI", "WebView2"','"SimplicityAI", "StreamingPrototype-WebView2"').Replace('Text = "SimplicityAI"','Text = "SimplicityAI — streaming prototype"')
# Keep the authenticated session file and logs outside the repository.
$text=$text.Replace('Path.Combine(root, "..", "session-url.txt")','Path.Combine(root, "..", "session-url.txt")')
$generated=Join-Path $destination 'AppWindow.cs'
$text | Set-Content -LiteralPath $generated -Encoding UTF8
foreach($name in @('Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll','WebView2Loader.dll','LICENSE.txt')){
    Copy-Item -LiteralPath (Join-Path 'C:\SimplicityAI-Lab\ThemHands\window-runtime' $name) -Destination $destination
}
$compiler=Join-Path $env:SystemRoot 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$manifest=Join-Path $PSScriptRoot '..\prototype\AppWindow.manifest'
$icon=Join-Path $PSScriptRoot '..\..\assets\SimplicityBRS.ico'
& $compiler /nologo /target:winexe /platform:x64 "/win32icon:$icon" "/win32manifest:$manifest" "/out:$destination\SimplicityAI.exe" /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll "/reference:$destination\Microsoft.Web.WebView2.Core.dll" "/reference:$destination\Microsoft.Web.WebView2.WinForms.dll" $generated
if($LASTEXITCODE -ne 0){throw 'Streaming window compilation failed'}
Copy-Item -LiteralPath 'C:\SimplicityAI-Lab\ThemHands\window-runtime\SimplicityAI.exe.config' -Destination $destination
