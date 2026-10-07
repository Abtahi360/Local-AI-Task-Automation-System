<#
.SYNOPSIS
  Start the Local AI Task Automation backend (FastAPI + Uvicorn) on localhost.

.DESCRIPTION
  Uses the project's .venv (calls .venv\Scripts\python.exe directly, which is
  equivalent to activating it), verifies dependencies and the configured port,
  then starts the server. Press Ctrl+C to stop.
  Host and port come from .env (defaults 127.0.0.1:8000); the API is never exposed
  beyond this computer unless ALLOW_NON_LOCAL_BIND=true is set deliberately.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\start.ps1
  powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -Reload
#>
[CmdletBinding()]
param([switch]$Reload)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $ProjectRoot

function Stop-Start([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    exit 1
}

$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) {
    Stop-Start 'The virtual environment was not found. Run scripts\install\setup.ps1 first.'
}

& $VenvPython -c "import fastapi, uvicorn, sqlalchemy, alembic, pydantic_settings, playwright"
if ($LASTEXITCODE -ne 0) {
    Stop-Start 'Required packages are missing from .venv. Run scripts\install\setup.ps1 again.'
}

$settingsLines = & $VenvPython -c "from backend.core.config import Settings; s = Settings(); print(s.app_host); print(s.app_port)"
if ($LASTEXITCODE -ne 0 -or $settingsLines.Count -lt 2) {
    Stop-Start 'Configuration could not be loaded. Check your .env file (see docs\TROUBLESHOOTING.md).'
}
$HostAddress = ([string]$settingsLines[0]).Trim()
$Port = [int]([string]$settingsLines[1]).Trim()

# Friendly check that the port is free before starting.
$ip = $null
if (-not [System.Net.IPAddress]::TryParse($HostAddress, [ref]$ip)) { $ip = [System.Net.IPAddress]::Loopback }
$listener = New-Object System.Net.Sockets.TcpListener($ip, $Port)
try {
    $listener.Start()
    $listener.Stop()
} catch {
    Stop-Start "Port $Port is already in use. Close the other program or change APP_PORT in .env."
}

Write-Host 'Local AI Task Automation System' -ForegroundColor Cyan
Write-Host "Local URL: http://${HostAddress}:${Port}" -ForegroundColor Green
Write-Host 'Press Ctrl+C to stop.'

$serverArguments = @('-m', 'backend')
if ($Reload) { $serverArguments += '--reload' }
& $VenvPython @serverArguments
exit $LASTEXITCODE
