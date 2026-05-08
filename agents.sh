#!/usr/bin/env bash
# Launches the Claude Code → OpenCode migration tool.
# Ensures Python 3.12+ is available, prompts to install if missing.
# Usage: ./agents.sh <convert|install|remove|swap> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD="$1"
CMD_PATH="$SCRIPT_DIR/$CMD.py"

if [ ! -f "$CMD_PATH" ]; then
    echo "Error: $CMD.py not found alongside agents.sh" >&2
    exit 1
fi
shift

# ----- Python prerequisite check -----
check_python() {
    if command -v python3 &>/dev/null; then
        py="python3"
    elif command -v python &>/dev/null; then
        py="python"
    else
        return 1
    fi
    ver=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    if [ -z "$ver" ]; then return 1; fi
    major="${ver%.*}"
    minor="${ver#*.}"
    [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; }
}

install_python() {
    # 1. Try uv (cross-platform, no system pkg mgr needed)
    if command -v uv &>/dev/null; then
        echo "Installing Python 3.12 via uv..." >&2
        uv python install 3.12
        return $?
    fi

    # 2. macOS
    if [[ "$(uname)" == "Darwin" ]]; then
        if command -v brew &>/dev/null; then
            echo "Installing Python 3.12 via Homebrew..." >&2
            brew install python@3.12
            return $?
        fi
    fi

    # 3. Linux
    if [[ "$(uname)" == "Linux" ]]; then
        if command -v apt &>/dev/null; then
            echo "Installing Python 3.12 via apt..." >&2
            sudo apt update && sudo apt install -y python3.12 python3.12-venv
            return $?
        fi
        if command -v dnf &>/dev/null; then
            echo "Installing Python 3.12 via dnf..." >&2
            sudo dnf install -y python3.12
            return $?
        fi
        if command -v yum &>/dev/null; then
            echo "Installing Python 3.12 via yum..." >&2
            sudo yum install -y python3.12
            return $?
        fi
    fi

    echo "Error: No supported package manager found." >&2
    echo "Install Python 3.12+ manually from: https://www.python.org/downloads/" >&2
    return 1
}

if ! check_python; then
    echo "Python 3.12+ is required but not found." >&2
    read -r -p "Install Python 3.12 now? (Y/n): " REPLY
    REPLY="${REPLY:-Y}"
    if [[ "$REPLY" =~ ^[Yy] ]]; then
        if ! install_python; then
            echo "Error: Failed to install Python." >&2
            exit 1
        fi
        # Re-check PATH for newly installed python
        hash -r 2>/dev/null || true
        if ! check_python; then
            echo "Error: Python 3.12+ still not found after install." >&2
            exit 1
        fi
    else
        echo "Aborted. Python 3.12+ is required." >&2
        exit 1
    fi
fi

# Determine which python to use
if command -v python3 &>/dev/null; then
    py="python3"
else
    py="python"
fi

# ----- Git prerequisite check (convert only) -----
if [ "$CMD" = "convert" ] && ! command -v git &>/dev/null; then
    echo "Error: git is required for 'convert' (clones the source repo)." >&2
    echo "Install git from: https://git-scm.com/downloads" >&2
    exit 1
fi

# ----- Run -----
exec "$py" "$CMD_PATH" "$@"
