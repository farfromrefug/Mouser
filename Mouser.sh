#!/bin/bash
# Mouser startup script for Linux
# This script activates the virtual environment and runs Mouser

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run the following commands first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Check if dependencies are installed
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "Error: Dependencies not installed!"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Run Mouser
cd "$SCRIPT_DIR"
python3 main_qml.py "$@"
