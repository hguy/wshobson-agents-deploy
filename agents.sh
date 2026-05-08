#!/usr/bin/env bash
# Launches the WsHobson Agents Anywhere migration tool.
# Checks prerequisites (Python 3.12+, git), prints install commands
# for missing tools, and exits. Retry after installing prerequisites.
# Usage: ./agents.sh <convert|install|remove|swap> [args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD="${1:-}"
CMD_PATH="$SCRIPT_DIR/$CMD.py"

if [ -z "$CMD" ]; then
    echo "Error: No command specified. Usage: agents.sh <convert|install|remove|swap> [args...]" >&2
    exit 1
fi

if [ ! -f "$CMD_PATH" ]; then
    echo "Error: Unknown command '$CMD'. Valid: convert, install, remove, swap" >&2
    exit 1
fi
shift

MISSING=0

# ----- Python 3.12+ -----
PYTHON_BIN=""
for candidate in python3 python python3.12; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [ -z "$ver" ]; then continue; fi
        major="${ver%.*}"
        minor="${ver#*.}"
        if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; }; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

# Also check uv-managed Python
if [ -z "$PYTHON_BIN" ] && command -v uv &>/dev/null; then
    uv_ver=$(uv python list 2>/dev/null | grep -oE '3\.(1[2-9]|[2-9]\d)' | head -1)
    if [ -n "$uv_ver" ]; then
        PYTHON_BIN="uv"
    fi
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "Missing: Python 3.12+" >&2
    case "$(uname)" in
        Darwin)
            echo "  Install: brew install python@3.12" >&2 ;;
        Linux)
            if command -v apt &>/dev/null; then
                echo "  Install: apt install python3.12 python3.12-venv" >&2
            elif command -v dnf &>/dev/null; then
                echo "  Install: dnf install python3.12" >&2
            elif command -v yum &>/dev/null; then
                echo "  Install: yum install python3.12" >&2
            elif command -v apk &>/dev/null; then
                echo "  Install: apk add python3.12" >&2
            else
                echo "  Download: https://www.python.org/downloads/" >&2
            fi ;;
        *)
            echo "  Download: https://www.python.org/downloads/" >&2 ;;
    esac
    MISSING=1
fi

# ----- Git (required for convert) -----
if [ "$CMD" = "convert" ] && ! command -v git &>/dev/null; then
    echo "Missing: git" >&2
    case "$(uname)" in
        Darwin)
            echo "  Install: brew install git" >&2
            echo "  Or: xcode-select --install" >&2 ;;
        Linux)
            if command -v apt &>/dev/null; then
                echo "  Install: apt install git" >&2
            elif command -v dnf &>/dev/null; then
                echo "  Install: dnf install git" >&2
            elif command -v yum &>/dev/null; then
                echo "  Install: yum install git" >&2
            elif command -v apk &>/dev/null; then
                echo "  Install: apk add git" >&2
            else
                echo "  Download: https://git-scm.com/downloads" >&2
            fi ;;
        *)
            echo "  Download: https://git-scm.com/downloads" >&2 ;;
    esac
    MISSING=1
fi

# ----- uv (recommended) -----
if ! command -v uv &>/dev/null; then
    echo "Warning: uv (Python package manager) not found. Recommended for faster dependency management." >&2
    echo "  Install: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    echo >&2
fi

# ----- Report and exit -----
if [ "$MISSING" -eq 1 ]; then
    echo >&2
    echo "Install the missing tools above, open a new terminal, and retry." >&2
    exit 1
fi

# ----- Run -----
if command -v uv &>/dev/null; then
    exec uv run python "$CMD_PATH" "$@"
else
    exec "$PYTHON_BIN" "$CMD_PATH" "$@"
fi
