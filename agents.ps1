#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launches the Claude Code → OpenCode migration tool.
.DESCRIPTION
    Ensures Python 3.12+ is available (prompts to install if missing),
    then delegates to the Python migration CLI.
.PARAMETER Command
    The migration command to run: convert, install, remove, or swap.
.PARAMETER Args
    Additional arguments passed through to the Python CLI.
#>
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('convert', 'install', 'remove', 'swap')]
    [string]$Command,

    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Args
)

$ScriptDir = Split-Path -Parent $PSCommandPath
$CmdPath = Join-Path $ScriptDir "$Command.py"

if (-not (Test-Path $CmdPath)) {
    Write-Error "$Command.py not found alongside agents.ps1"
    exit 1
}

# ----- Python prerequisite check -----
function Test-PythonVersion {
    param([string]$Exe)
    try {
        $ver = & $Exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -and [version]$ver -ge [version]"3.12") { return $true }
    } catch {}
    return $false
}

function Install-Python {
    Write-Host "Python 3.12+ is required but not found." -ForegroundColor Yellow
    $reply = Read-Host "Install Python 3.12 now? (Y/n)"
    if ($reply -eq '' -or $reply -match '^[Yy]') {
        if (Get-Command "uv" -ErrorAction SilentlyContinue) {
            Write-Host "Installing Python 3.12 via uv..." -ForegroundColor Cyan
            & uv python install 3.12
            if ($LASTEXITCODE -ne 0) { throw "uv install failed" }
            return "uv"
        }
        elseif (Get-Command "winget" -ErrorAction SilentlyContinue) {
            Write-Host "Installing Python 3.12 via winget..." -ForegroundColor Cyan
            & winget install -e --id Python.Python.3.12 --accept-source-agreements
            if ($LASTEXITCODE -ne 0) { throw "winget install failed" }
            # Refresh PATH so the new Python is found
            $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
            return "winget"
        }
        elseif (Get-Command "choco" -ErrorAction SilentlyContinue) {
            Write-Host "Installing Python 3.12 via Chocolatey..." -ForegroundColor Cyan
            & choco install python -y --version 3.12
            if ($LASTEXITCODE -ne 0) { throw "choco install failed" }
            return "choco"
        }
        else {
            Write-Host "No supported package manager found." -ForegroundColor Red
            Write-Host "Install Python 3.12+ manually from: https://www.python.org/downloads/" -ForegroundColor Yellow
            throw "unsupported platform"
        }
    }
    else {
        Write-Host "Aborted. Python 3.12+ is required." -ForegroundColor Red
        exit 1
    }
}

# Resolve Python: try uv python, then system python, then install
$Runner = $null

if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    # uv can list managed Python versions
    $uvPythons = uv python list 2>$null | Where-Object { $_ -match '(\d+\.\d+)' }
    if ($uvPythons -match '3\.1[2-9]|3\.[2-9]\d') {
        $Runner = "uv"
    }
}

if (-not $Runner) {
    foreach ($exe in @("python3", "python", "py")) {
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            if (Test-PythonVersion $exe) {
                $Runner = $exe
                break
            }
        }
    }
}

if (-not $Runner) {
    try {
        $method = Install-Python
        if ($method -eq "uv") { $Runner = "uv" }
        else {
            foreach ($exe in @("python3", "python", "py")) {
                if (Get-Command $exe -ErrorAction SilentlyContinue) {
                    if (Test-PythonVersion $exe) { $Runner = $exe; break }
                }
            }
        }
    } catch {
        Write-Error "Failed to install Python. Install Python 3.12+ manually."
        exit 1
    }
}

if (-not $Runner) {
    Write-Error "Python 3.12+ not found after install attempt."
    exit 1
}

# ----- Git prerequisite check (convert only) -----
if ($Command -eq 'convert' -and -not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Error "git is required for 'convert' (clones the source repo). Install git from: https://git-scm.com/downloads"
    exit 1
}

# ----- Run -----
switch ($Runner) {
    "uv" { & uv run python $CmdPath @Args; exit $LASTEXITCODE }
    default { & $Runner $CmdPath @Args; exit $LASTEXITCODE }
}
