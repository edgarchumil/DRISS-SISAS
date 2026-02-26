$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backupDir = Join-Path $projectRoot 'backups\mensuales'
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$dbName = if ($env:DB_NAME) { $env:DB_NAME } else { 'sisas_db' }
$dbUser = if ($env:DB_USER) { $env:DB_USER } else { 'sisas_user' }
$dbPass = if ($env:DB_PASS) { $env:DB_PASS } else { 'sisas_pass' }
$dbHost = if ($env:DB_HOST) { $env:DB_HOST } else { '127.0.0.1' }
$dbPort = if ($env:DB_PORT) { $env:DB_PORT } else { '5432' }

$pgDumpCandidates = @(@(
    (Get-Command pg_dump -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe',
    'C:\Program Files\PostgreSQL\17\bin\pg_dump.exe',
    'C:\Program Files\PostgreSQL\18\bin\pg_dump.exe'
) | Where-Object { $_ -and (Test-Path $_) })

if (-not $pgDumpCandidates -or $pgDumpCandidates.Count -eq 0) {
    throw 'No se encontro pg_dump. Instala PostgreSQL client tools.'
}

$pgDump = $pgDumpCandidates | Select-Object -First 1
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outputFile = Join-Path $backupDir ("backup_{0}.sql" -f $timestamp)

$env:PGPASSWORD = $dbPass
& $pgDump `
    -h $dbHost `
    -p $dbPort `
    -U $dbUser `
    -d $dbName `
    --no-owner `
    --no-privileges `
    --encoding=UTF8 `
    -f $outputFile

if ($LASTEXITCODE -ne 0) {
    throw "pg_dump fallo con codigo $LASTEXITCODE"
}

Write-Output ("OK: respaldo creado en {0}" -f $outputFile)
