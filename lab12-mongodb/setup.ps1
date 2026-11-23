$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (!(Test-Path .env)) {
  $lines = foreach ($name in 'ADMIN','READ','WRITE','HR') {
    $bytes = New-Object byte[] 24
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    'LAB12_' + $name + '_PASSWORD=' + ([BitConverter]::ToString($bytes).Replace('-','').ToLowerInvariant())
  }
  $lines | Set-Content .env -Encoding ASCII
}
if (!(Test-Path evidence)) { New-Item -ItemType Directory evidence | Out-Null }
