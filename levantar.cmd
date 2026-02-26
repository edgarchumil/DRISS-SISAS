@echo off
setlocal
for /f "delims=" %%i in ('powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable(''TUNNEL_TOKEN'',''User'')"') do set "TUNNEL_TOKEN=%%i"
for /f "delims=" %%i in ('powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable(''TUNNEL_NAME'',''User'')"') do set "TUNNEL_NAME=%%i"
if "%TUNNEL_NAME%"=="" set "TUNNEL_NAME=driss-sisas"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-windows.ps1" %*
endlocal
