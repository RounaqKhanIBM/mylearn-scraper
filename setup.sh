#!/usr/bin/env bash
# One-time environment setup: virtualenv, Python dependencies, and the Chromium browser.
# Safe to re-run; it does nothing if everything is already installed.
#
#   ./setup.sh           (or: ./run.sh setup)
set -euo pipefail

cd "$(dirname "$0")"
VENV=".venv"
MARKER="$VENV/.deps_installed"

command -v python3 >/dev/null 2>&1 || { echo "python3 is required but was not found." >&2; exit 1; }

if [ ! -x "$VENV/bin/python" ]; then
    echo "Creating virtual environment in $VENV ..."
    python3 -m venv "$VENV"
fi

if [ -f "$MARKER" ] && [ ! requirements.txt -nt "$MARKER" ]; then
    echo "Environment is already set up."
    exit 0
fi

echo "Installing dependencies ..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r requirements.txt
echo "Installing browser (Chromium) ..."
"$VENV/bin/playwright" install chromium
touch "$MARKER"
echo "Setup complete."
