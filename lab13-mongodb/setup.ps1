$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path .env)) {
    $a = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    $b = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    @("LAB13_PASSWORD=$a", "LAB13_MONITOR_PASSWORD=$b") | Set-Content .env -Encoding ASCII
    Write-Host 'Local credentials generated.'
}
