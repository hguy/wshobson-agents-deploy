#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launches the Claude Code → target migration tool.
.DESCRIPTION
    Checks prerequisites (Python 3.12+, git), offers auto-install with -y.
.PARAMETER y
    Auto-confirm prerequisite installations (skip prompts).
.PARAMETER Command
    The migration command to run: convert, install, remove, or swap.
.PARAMETER Args
    Additional arguments passed through to the Python CLI.
#>
param(
    [switch]$y,
    [Parameter(Position = 0)]
    [string]$Command = '',
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Args
)

$ScriptDir = Split-Path -Parent $PSCommandPath
$CmdPath = Join-Path $ScriptDir "$Command.py"

if (-not $Command) {
    Write-Error "No command specified. Usage: agents.ps1 [-y] <convert|install|remove|swap> [args...]"
    exit 1
}

if (-not (Test-Path $CmdPath)) {
    Write-Error "Unknown command '$Command'. Valid: convert, install, remove, swap"
    exit 1
}

# ----- Utility -----
function Confirm-OrAuto {
    param([string]$Prompt)
    if ($y) { return $true }
    $reply = Read-Host "$Prompt (Y/n)"
    return ($reply -eq '' -or $reply -match '^[Yy]')
}

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

# ----- Python check -----
function Test-PythonVersion {
    param([string]$Exe)
    try {
        $ver = & $Exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -and [version]$ver -ge [version]"3.12") { return $true }
    } catch {}
    return $false
}

function Install-Python {
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        Write-Host "Installing Python 3.12 via uv..." -ForegroundColor Cyan
        & uv python install 3.12
        if ($LASTEXITCODE -ne 0) { throw "uv install failed" }
        return "uv"
    }
    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Write-Host "Installing Python 3.12 via winget..." -ForegroundColor Cyan
        & winget install -e --id Python.Python.3.12 --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw "winget install failed" }
        Refresh-Path
        return "winget"
    }
    if (Get-Command "choco" -ErrorAction SilentlyContinue) {
        Write-Host "Installing Python 3.12 via Chocolatey..." -ForegroundColor Cyan
        & choco install python -y --version 3.12
        if ($LASTEXITCODE -ne 0) { throw "choco install failed" }
        return "choco"
    }
    Write-Host "No supported package manager found." -ForegroundColor Red
    Write-Host "Install Python 3.12+ manually from: https://www.python.org/downloads/" -ForegroundColor Yellow
    throw "unsupported platform"
}

function Resolve-Python {
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        $uvPythons = uv python list 2>$null | Where-Object { $_ -match '(\d+\.\d+)' }
        if ($uvPythons -match '3\.1[2-9]|3\.[2-9]\d') {
            return "uv"
        }
    }
    foreach ($exe in @("python3", "python", "py")) {
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            if (Test-PythonVersion $exe) { return $exe }
        }
    }
    return $null
}

$Runner = Resolve-Python

if (-not $Runner) {
    Write-Host "Python 3.12+ is required but not found." -ForegroundColor Yellow
    if (Confirm-OrAuto "Install Python 3.12 now?") {
        try {
            $method = Install-Python
            if ($method -eq "uv") { $Runner = "uv" }
            else {
                $Runner = Resolve-Python
                if (-not $Runner) {
                    # Re-check after PATH refresh
                    foreach ($exe in @("python3", "python", "py")) {
                        if (Get-Command $exe -ErrorAction SilentlyContinue) {
                            if (Test-PythonVersion $exe) { $Runner = $exe; break }
                        }
                    }
                }
            }
        } catch {
            Write-Error "Failed to install Python. Install Python 3.12+ manually."
            exit 1
        }
    } else {
        Write-Host "Aborted. Python 3.12+ is required." -ForegroundColor Red
        exit 1
    }
}

if (-not $Runner) {
    Write-Error "Python 3.12+ not found after install attempt."
    exit 1
}

# ----- uv check (recommended) -----
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "uv (Python package manager) not found. Using system Python directly." -ForegroundColor Yellow
    Write-Host "Install uv for faster dependency management: https://docs.astral.sh/uv/" -ForegroundColor Gray
}

# ----- Git check (convert only) -----
if ($Command -eq 'convert' -and -not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "git is required for 'convert' (clones the source repo)." -ForegroundColor Yellow
    if (Confirm-OrAuto "Install git now?") {
        if (Get-Command "winget" -ErrorAction SilentlyContinue) {
            & winget install --id Git.Git -e --source winget --accept-source-agreements
            Refresh-Path
        } elseif (Get-Command "choco" -ErrorAction SilentlyContinue) {
            & choco install git -y
        } else {
            Write-Error "No supported package manager found."
            Write-Error "Install git from: https://git-scm.com/downloads"
            exit 1
        }
        if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
            Write-Error "git still not found after install attempt."
            exit 1
        }
    } else {
        Write-Host "Aborted. git is required for 'convert'." -ForegroundColor Red
        exit 1
    }
}

# ----- Run -----
switch ($Runner) {
    "uv" { & uv run python $CmdPath @Args; exit $LASTEXITCODE }
    default { & $Runner $CmdPath @Args; exit $LASTEXITCODE }
}
