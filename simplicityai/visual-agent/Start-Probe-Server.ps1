$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\SimplicityAI-Lab\VisualAgent'
if (Get-NetTCPConnection -LocalPort 8772 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Port 8772 is occupied; existing service was not touched.'
}
# All paths are local. Do not use -hf or runtime model downloads.
& "$taskRoot\runtime\llama-server.exe" `
    -m "$taskRoot\UI-TARS-1.5-7B.Q4_K_M.gguf" `
    --mmproj "$taskRoot\UI-TARS-1.5-7B.mmproj-f16.gguf" `
    --host 127.0.0.1 --port 8772 --alias ui-tars `
    -c 4096 -ngl 99 -t 6 --parallel 1 --image-min-tokens 1024
exit $LASTEXITCODE
