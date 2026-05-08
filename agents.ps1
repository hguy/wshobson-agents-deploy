#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launches the WsHobson Agents Anywhere migration tool.
.DESCRIPTION
    Checks prerequisites (Python 3.12+, git, uv), prints install commands
    for missing tools, and exits. Retry after installing prerequisites.
.PARAMETER Command
    The migration command: convert, install, remove, or swap.
.PARAMETER Args
    Additional arguments passed through to the Python CLI.
#>
param(
    [Parameter(Position = 0)]
    [string]$Command = '',
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Args
)

$ScriptDir = Split-Path -Parent $PSCommandPath
$CmdPath = Join-Path $ScriptDir "$Command.py"

if (-not $Command) {
    Write-Error "No command specified. Usage: agents.ps1 <convert|install|remove|swap> [args...]"
    exit 1
}

if (-not (Test-Path $CmdPath)) {
    Write-Error "Unknown command '$Command'. Valid: convert, install, remove, swap"
    exit 1
}

$Missing = @()

# ----- Python 3.12+ -----
function Test-PythonVersion {
    param([string]$Exe)
    try {
        $ver = & $Exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -and [version]$ver -ge [version]"3.12") { return $true }
    } catch {}
    return $false
}

$PythonOK = $false
# Check uv-managed Python first
if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    $uvPythons = uv python list 2>$null | Where-Object { $_ -match '3\.1[2-9]|3\.[2-9]\d' }
    if ($uvPythons) { $PythonOK = $true }
}
# Check system Python
if (-not $PythonOK) {
    foreach ($exe in @("python3", "python", "py")) {
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            if (Test-PythonVersion $exe) { $PythonOK = $true; break }
        }
    }
}

if (-not $PythonOK) {
    $Missing += "Python 3.12+`n  Install: winget install -e --id Python.Python.3.12`n  Or download: https://www.python.org/downloads/"
}

# ----- Git (required for convert) -----
if ($Command -eq 'convert' -and -not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    $Missing += "git`n  Install: winget install --id Git.Git -e --source winget`n  Or download: https://git-scm.com/downloads"
}

# ----- uv (recommended) -----
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "Warning: uv (Python package manager) not found. Recommended for faster dependency management." -ForegroundColor Yellow
    Write-Host "  Install: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Gray
    Write-Host ""
}

# ----- Report missing prerequisites -----
if ($Missing.Count -gt 0) {
    Write-Host "Missing prerequisites:" -ForegroundColor Red
    foreach ($item in $Missing) {
        Write-Host "  - $item" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Install the missing tools above, open a new terminal, and retry." -ForegroundColor Cyan
    exit 1
}

# ----- Run -----
if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    & uv run python $CmdPath @Args
} else {
    # Find the Python we validated earlier
    foreach ($exe in @("python3", "python", "py")) {
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            if (Test-PythonVersion $exe) { & $exe $CmdPath @Args; break }
        }
    }
}
exit $LASTEXITCODE
