<#
.SYNOPSIS
  One-command development setup for the Local AI Task Automation System (Phase 2).

.DESCRIPTION
  Safe to run more than once. It NEVER deletes your data, .venv, or an existing .env.
    1. Finds Python 3.12 or 3.13
    2. Creates (or validates) .venv
    3. Installs pinned dependencies (requirements-dev.txt)
    4. Installs the Playwright Chromium test browser (optional; skip with -SkipBrowserInstall)
    5. Creates .env from .env.example if missing
    6. Creates runtime folders and initialises the SQLite database
    7. Verifies the environment and runs the test suite (skip tests with -SkipTests)

  The virtual environment's python.exe is called directly, which is equivalent to
  activating it and avoids PowerShell execution-policy problems with Activate.ps1.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\install\setup.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipBrowserInstall,
    [switch]$SkipTests,
    [string]$PythonCommand
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $ProjectRoot

function Write-Step([string]$Message) { Write-Host ''; Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message)   { Write-Host "[ OK ] $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Stop-Setup([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    Write-Host ''
    Write-Host 'SETUP FAILED. See docs\TROUBLESHOOTING.md, then re-run this script.' -ForegroundColor Red
    exit 1
}

function Invoke-Checked {
    param([string]$Description, [string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { Stop-Setup "$Description failed (exit code $LASTEXITCODE)." }
}

function Get-PythonVersion {
    param([string]$Executable, [string[]]$PrefixArguments)
    try {
        $output = & $Executable @PrefixArguments -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $output) { return ([string]($output | Select-Object -First 1)).Trim() }
    } catch { }
    return $null
}

Write-Host 'Local AI Task Automation System - Phase 2 setup'
Write-Host "Project folder: $ProjectRoot"

# ---------------------------------------------------------------- 1. Python
Write-Step 'Step 1/7: locating Python 3.12 or 3.13'
$supported = @('3.12', '3.13')
$candidates = @()
if ($PythonCommand) {
    $candidates += , @($PythonCommand, @())
} else {
    $candidates += , @('py', @('-3.12'))
    $candidates += , @('py', @('-3.13'))
    $candidates += , @('python', @())
    $candidates += , @('python3', @())
}
$PythonExe = $null
$PythonPrefix = @()
foreach ($candidate in $candidates) {
    $version = Get-PythonVersion -Executable $candidate[0] -PrefixArguments $candidate[1]
    if ($version -and ($supported -contains $version)) {
        $PythonExe = $candidate[0]
        $PythonPrefix = $candidate[1]
        Write-Ok "Found Python $version via '$($candidate[0]) $($candidate[1] -join ' ')'"
        break
    }
}
if (-not $PythonExe) {
    Stop-Setup 'Python 3.12 or 3.13 was not found. Install Python 3.12.x from https://www.python.org/downloads/windows/ (tick "Add python.exe to PATH" and "py launcher"), then re-run.'
}

# ---------------------------------------------------------------- 2. venv
Write-Step 'Step 2/7: virtual environment (.venv)'
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (Test-Path $VenvPython) {
    $venvVersion = Get-PythonVersion -Executable $VenvPython -PrefixArguments @()
    if ($venvVersion -and ($supported -contains $venvVersion)) {
        Write-Ok "Existing .venv is valid (Python $venvVersion); reusing it"
    } else {
        Stop-Setup 'The existing .venv looks broken or uses an unsupported Python. Delete the .venv folder yourself (nothing else is stored in it) and re-run setup.'
    }
} else {
    Invoke-Checked 'Creating the virtual environment' $PythonExe ($PythonPrefix + @('-m', 'venv', '.venv'))
    Write-Ok 'Created .venv'
}

# ---------------------------------------------------------------- 3. dependencies
Write-Step 'Step 3/7: installing pinned dependencies (this can take a few minutes)'
Invoke-Checked 'Upgrading pip' $VenvPython @('-m', 'pip', 'install', '--upgrade', 'pip')
Invoke-Checked 'Installing requirements-dev.txt' $VenvPython @('-m', 'pip', 'install', '-r', 'requirements-dev.txt')
Invoke-Checked 'Checking dependency consistency (pip check)' $VenvPython @('-m', 'pip', 'check')
Write-Ok 'Dependencies installed and consistent'

# ---------------------------------------------------------------- 4. Playwright browser
Write-Step 'Step 4/7: Playwright browser binary'
if ($SkipBrowserInstall) {
    Write-Warn 'Skipped (-SkipBrowserInstall). Install later with: python -m playwright install chromium'
} else {
    & $VenvPython -m playwright install chromium
    if ($LASTEXITCODE -ne 0) {
        Write-Warn 'Chromium download failed. This is optional in Phase 2; see docs\TROUBLESHOOTING.md and retry later.'
    } else {
        Write-Ok 'Playwright Chromium installed'
    }
}

# ---------------------------------------------------------------- 5. .env
Write-Step 'Step 5/7: configuration file (.env)'
if (Test-Path '.env') {
    Write-Ok '.env already exists; left unchanged'
} else {
    Copy-Item '.env.example' '.env'
    Write-Ok 'Created .env from .env.example (contains no secrets)'
}

# ---------------------------------------------------------------- 6. folders + SQLite
Write-Step 'Step 6/7: runtime folders and SQLite database'
Invoke-Checked 'Initialising folders and database' $VenvPython @('scripts\install\init_environment.py')

# ---------------------------------------------------------------- 7. verify + tests
Write-Step 'Step 7/7: verification'
Invoke-Checked 'Environment verification' $VenvPython @('scripts\diagnostics\verify_environment.py')
if ($SkipTests) {
    Write-Warn 'Tests skipped (-SkipTests)'
} else {
    Invoke-Checked 'Running pytest' $VenvPython @('-m', 'pytest', '-q')
    Write-Ok 'All tests passed'
}

Write-Host ''
Write-Host 'SETUP COMPLETE.' -ForegroundColor Green
Write-Host 'Start the application with:  powershell -ExecutionPolicy Bypass -File scripts\start.ps1'
Write-Host 'Then open:                   http://127.0.0.1:8000'
exit 0
