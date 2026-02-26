# Requiere privilegios de Administrador (se auto-eleva si es necesario)
$ErrorActionPreference = 'Stop'

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).
    IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  $args = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', ('"{0}"' -f $PSCommandPath)
  )
  Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList ($args -join ' ')
  exit 0
}

$repo = 'C:\Users\USUARIO\DRISS-SISAS'
$startPs1 = Join-Path $repo 'start-windows.ps1'
$detener = Join-Path $repo 'detener.cmd'
$taskUser = "$env:USERDOMAIN\$env:USERNAME"

if (!(Test-Path $startPs1)) { throw "No existe: $startPs1" }
if (!(Test-Path $detener)) { throw "No existe: $detener" }

# Accion para iniciar sistema
$actionStart = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$startPs1`"" -WorkingDirectory $repo

# Trigger al arrancar equipo (con delay para red)
$triggerStartup = New-ScheduledTaskTrigger -AtStartup
$triggerStartup.Delay = 'PT45S'

# Trigger al iniciar sesion del usuario
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $taskUser
$triggerLogon.Delay = 'PT20S'

# Ajustes de robustez
$settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -MultipleInstances IgnoreNew

# Principal con privilegios altos
$principalUser = New-ScheduledTaskPrincipal -UserId $taskUser -LogonType S4U -RunLevel Highest

# Crear/actualizar tarea principal
Register-ScheduledTask `
  -TaskName 'DRISS-SISAS Autostart' `
  -Action $actionStart `
  -Trigger @($triggerStartup, $triggerLogon) `
  -Settings $settings `
  -Principal $principalUser `
  -Force | Out-Null

# Tarea opcional de recovery de red: intenta levantar cada 10 min si hay fallo
$triggerRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date).Date
$triggerRepeat.Repetition.Interval = 'PT10M'
$triggerRepeat.Repetition.Duration = 'P1D'
Register-ScheduledTask `
  -TaskName 'DRISS-SISAS Recovery' `
  -Action $actionStart `
  -Trigger $triggerRepeat `
  -Settings $settings `
  -Principal $principalUser `
  -Force | Out-Null

# Tarea de apagado rapido manual (opcional)
$actionStop = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c `"$detener`"" -WorkingDirectory $repo
$triggerStop = New-ScheduledTaskTrigger -AtLogOn -User $taskUser
$triggerStop.Enabled = $false
Register-ScheduledTask `
  -TaskName 'DRISS-SISAS Stop (Manual)' `
  -Action $actionStop `
  -Trigger $triggerStop `
  -Settings $settings `
  -Principal $principalUser `
  -Force | Out-Null

Write-Host '[ok] Tareas creadas/actualizadas:'
Get-ScheduledTask -TaskName 'DRISS-SISAS*' | Select-Object TaskName,State | Format-Table -AutoSize

Write-Host '\n[run] Ejecutando inicio ahora...'
Start-ScheduledTask -TaskName 'DRISS-SISAS Autostart'
