#!/bin/sh
# ============================================================
# SOC with AI — One-Click Development Setup (Unix/macOS)
# Run this script to install everything:
#   - Runtime dependencies (requirements.txt)
#   - Dev dependencies (requirements-dev.txt)
#   - Playwright Chromium (E2E tests)
#   - Git hooks (pre-commit, commit-msg, post-merge, pre-push)
# ============================================================

set -e

echo ""
echo "========================================"
echo "  SOC with AI - Development Setup"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    echo "ERROR: Python not found in PATH."
    echo ""
    echo "Install Python 3.10+:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS:         brew install python"
    echo "  Fedora:        sudo dnf install python3"
    echo ""
    exit 1
fi

# Find python command
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
else
    PYTHON=python
fi

# Make the script executable if needed
chmod +x scripts/setup_dev.py 2>/dev/null || true

# Run the setup script
$PYTHON scripts/setup_dev.py "$@"

echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
