param(
    [switch]$NoTunnel,
    [switch]$QuickTunnel,
    [switch]$WithMigrations,
    [string]$TunnelName = $env:TUNNEL_NAME,
    [string]$TunnelDomain = $env:TUNNEL_DOMAIN,
    [string]$TunnelToken = $env:TUNNEL_TOKEN,
    [string]$DbName = $env:DB_NAME,
    [string]$DbUser = $env:DB_USER,
    [string]$DbPass = $env:DB_PASS,
    [string]$DbHost = $env:DB_HOST,
    [string]$DbPort = $env:DB_PORT,
    [string]$PublicHostHeader = 'localhost:4200'
)

if (-not $TunnelName) { $TunnelName = 'driss-sisas' }
if (-not $TunnelDomain) { $TunnelDomain = 'www.driss-sisas.com' }
if (-not $DbName) { $DbName = 'sisas_db' }
if (-not $DbUser) { $DbUser = 'sisas_user' }
if (-not $DbPass) { $DbPass = 'sisas_pass' }
if (-not $DbHost) { $DbHost = '127.0.0.1' }
if (-not $DbPort) { $DbPort = '5432' }

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$logsDir = Join-Path $root '.logs'
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$nodePath = 'C:\Program Files\nodejs'
$nodeExe = Join-Path $nodePath 'node.exe'
$npmCli = Join-Path $nodePath 'node_modules\npm\bin\npm-cli.js'
$psqlExe = 'C:\Program Files\PostgreSQL\16\bin\psql.exe'
$cfExe = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter cloudflared*.exe -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName

if (-not (Test-Path $nodeExe)) { throw "No se encontro $nodeExe" }
if (-not (Test-Path $npmCli)) { throw "No se encontro $npmCli" }
if (-not (Test-Path $psqlExe)) { throw "No se encontro $psqlExe" }
if (-not $NoTunnel -and -not $cfExe) { throw 'No se encontro cloudflared.exe' }

if (Test-Path '.\backend\.venv\Scripts\python.exe') {
    $py = '.\backend\.venv\Scripts\python.exe'
} else {
    $py = 'python'
}

$env:DJANGO_SETTINGS_MODULE = 'config.settings'
$env:DB_NAME = $DbName
$env:DB_USER = $DbUser
$env:DB_PASS = $DbPass
$env:DB_HOST = $DbHost
$env:DB_PORT = $DbPort
$env:DEBUG = '1'
$env:ALLOWED_HOSTS = '*'

Write-Host '[init] Validando conexion PostgreSQL...'
$env:PGPASSWORD = $DbPass
$psqlCmd = '"' + $psqlExe + '" -h ' + $DbHost + ' -p ' + $DbPort + ' -U ' + $DbUser + ' -d ' + $DbName + ' -c "select 1;" >nul 2>nul'
cmd /c $psqlCmd
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo conectar a PostgreSQL con DB='$DbName' USER='$DbUser' HOST='$DbHost' PORT='$DbPort'."
}

if ($WithMigrations) {
    Write-Host '[init] Migraciones contra PostgreSQL...'
    & $py .\backend\manage.py migrate
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la migracion a PostgreSQL.' }
}

$backendOut = Join-Path $logsDir 'backend.out.log'
$backendErr = Join-Path $logsDir 'backend.err.log'
$frontendOut = Join-Path $logsDir 'frontend.out.log'
$frontendErr = Join-Path $logsDir 'frontend.err.log'
$tunnelOut = Join-Path $logsDir 'tunnel.out.log'
$tunnelErr = Join-Path $logsDir 'tunnel.err.log'

Remove-Item $backendOut,$backendErr,$frontendOut,$frontendErr,$tunnelOut,$tunnelErr -Force -ErrorAction SilentlyContinue

$backendCmd = @"
`$env:DJANGO_SETTINGS_MODULE='config.settings'
`$env:DB_NAME='$DbName'
`$env:DB_USER='$DbUser'
`$env:DB_PASS='$DbPass'
`$env:DB_HOST='$DbHost'
`$env:DB_PORT='$DbPort'
`$env:DEBUG='1'
`$env:ALLOWED_HOSTS='*'
& '$((Resolve-Path $py).Path)' manage.py runserver 0.0.0.0:8000
"@
Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-Command',$backendCmd) -WorkingDirectory (Join-Path $root 'backend') -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru | Out-Null

$frontendCmd = @"
`$env:Path='$nodePath;'+`$env:Path
& '$nodeExe' '$npmCli' run start:local -- --host 0.0.0.0 --port 4200 --allowed-hosts all
"@
Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-Command',$frontendCmd) -WorkingDirectory (Join-Path $root 'frontend') -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru | Out-Null

$tunnelMode = 'none'
if (-not $NoTunnel) {
    if ($QuickTunnel) {
        $tunnelMode = 'quick'
        $tunnelArgs = @(
            'tunnel'
            '--url', 'http://localhost:4200'
            '--http-host-header', $PublicHostHeader
        )
    } else {
        $tunnelMode = 'named'
        if ([string]::IsNullOrWhiteSpace($TunnelToken)) {
            throw "Falta TUNNEL_TOKEN para '$TunnelName'."
        }
        $TunnelToken = $TunnelToken.Trim()
        $tunnelArgs = @(
            'tunnel', 'run'
            '--token', $TunnelToken
            '--url', 'http://localhost:4200'
            '--http-host-header', $PublicHostHeader
        )
    }
    Start-Process -FilePath $cfExe -WindowStyle Hidden -ArgumentList $tunnelArgs -WorkingDirectory $root -RedirectStandardOutput $tunnelOut -RedirectStandardError $tunnelErr -PassThru | Out-Null
}

Start-Sleep -Seconds 8

$backendUp = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 8000 } | Select-Object -First 1
$frontendUp = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 4200 } | Select-Object -First 1
if (-not $backendUp -or -not $frontendUp) {
    throw 'No se levantaron backend/frontend. Revisa .logs\\backend.err.log y .logs\\frontend.err.log'
}

$tunnelPid = $null
if (-not $NoTunnel) {
    $t = Get-Process -Name cloudflared -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1
    if ($t) { $tunnelPid = $t.Id }
}
if (-not $NoTunnel -and -not $tunnelPid) {
    throw 'No se pudo iniciar cloudflared. Revisa .logs\\tunnel.err.log'
}

[ordered]@{
    backend = $backendUp.OwningProcess
    frontend = $frontendUp.OwningProcess
    tunnel = $tunnelPid
} | ConvertTo-Json | Set-Content (Join-Path $logsDir 'pids.json')

Write-Host '[ok] Servicios arriba'
Write-Host '  Frontend: http://localhost:4200'
Write-Host '  Backend : http://localhost:8000'
if (-not $NoTunnel) {
    if ($tunnelMode -eq 'named') {
        Write-Host "  Dominio : https://$TunnelDomain"
    } else {
        $match = Select-String -Path $tunnelErr -Pattern 'https://[-0-9a-z]+\.trycloudflare\.com' | Select-Object -First 1
        if ($match) { Write-Host "  Tunnel  : $($match.Matches[0].Value)" }
    }
}
Write-Host '  Logs    : .logs\*.log'

