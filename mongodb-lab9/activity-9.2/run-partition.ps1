$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
function D { & docker @args; if ($LASTEXITCODE -ne 0) { throw "Docker failed: $args" } }
function P { D compose run --rm --no-deps -T runner python activity-9.2/partition.py @args }
$network = 'mongodb-lab9_default'
$isolated = @{}
function Disconnect-Node($node) {
    $id = (D compose ps -q $node | Select-Object -Last 1).Trim()
    if (-not $id) { throw "Missing container $node" }
    D network disconnect $network $id
    $script:isolated[$node] = $id
    P event disconnected $node
}
function Reconnect-Node($node) {
    D network connect --alias $node $network $script:isolated[$node]
    $script:isolated.Remove($node)
    P event reconnected $node
}
try {
    P ready
    D compose up -d --no-deps observer
    $primary = (P primary | Select-Object -Last 1).Trim()
    if ($primary -notin @('mongo1','mongo2','mongo3')) { throw "Unexpected primary $primary" }
    $secondaries = @('mongo1','mongo2','mongo3') | Where-Object { $_ -ne $primary }
    $marker = [guid]::NewGuid().ToString('N')
    P event phase-one $primary
    Disconnect-Node $secondaries[0]
    P probe $primary one-secondary $marker 1 majority
    Start-Sleep -Seconds 30
    Reconnect-Node $secondaries[0]
    P catchup $secondaries[0] $marker
    P ready
    $primary = (P primary | Select-Object -Last 1).Trim()
    if ($primary -notin @('mongo1','mongo2','mongo3')) { throw "Unexpected primary $primary" }
    $secondaries = @('mongo1','mongo2','mongo3') | Where-Object { $_ -ne $primary }
    P event phase-two $primary
    Disconnect-Node $secondaries[0]
    # Avoid a slow runner launch between second disconnect and probe where possible.
    Disconnect-Node $secondaries[1]
    P probe $primary no-majority ([guid]::NewGuid().ToString('N')) majority
    P no-primary $primary
    Start-Sleep -Seconds 3
} finally {
    foreach ($node in @($isolated.Keys)) {
        try { Reconnect-Node $node } catch { Write-Warning "Reconnect failed for $node : $_" }
    }
    try { P ready; P event recovered } finally { D compose stop observer }
}
