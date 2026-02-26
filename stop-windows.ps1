$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidsFile = Join-Path $root '.logs\pids.json'

$toStop = @()
if (Test-Path $pidsFile) {
    $pids = Get-Content -Raw $pidsFile | ConvertFrom-Json
    foreach ($name in @('backend','frontend','tunnel')) {
        $procId = $pids.$name
        if ($procId) { $toStop += [int]$procId }
    }
}

foreach ($port in @(8000,4200)) {
    $owner = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -eq $port } |
        Select-Object -First 1 -ExpandProperty OwningProcess
    if ($owner) { $toStop += [int]$owner }
}

$cf = Get-Process -Name cloudflared -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id
if ($cf) { $toStop += $cf }

$toStop = $toStop | Select-Object -Unique
if (-not $toStop -or $toStop.Count -eq 0) {
    Write-Host '[stop] no hay procesos activos del sistema'
    exit 0
}

foreach ($procId in $toStop) {
    try {
        Stop-Process -Id $procId -Force -ErrorAction Stop
        Write-Host "[stop] proceso $procId detenido"
    } catch {
        Write-Host "[stop] proceso $procId ya no estaba activo"
    }
}
