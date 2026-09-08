#!/bin/bash
# SOC with AI — Real-Time Network Defense System
# Run: chmod +x run.sh && ./run.sh

set -e

echo ""
echo "==============================================="
echo "  SOC with AI — Real-Time Network Defense System"
echo "==============================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Install Python 3.10+"
    exit 1
fi

PYTHON=$(command -v python3)
echo "[OK] Python: $($PYTHON --version)"

# Install dependencies
echo "[SETUP] Checking dependencies..."
$PYTHON -m pip install -q fastapi "uvicorn[standard]" pydantic python-dateutil jinja2 scikit-learn numpy scipy brotli-asgi 2>/dev/null || true

# Try scapy (needs root for live capture)
if [ "$EUID" -eq 0 ]; then
    $PYTHON -m pip install -q scapy 2>/dev/null || true
    echo "[OK] Scapy installed (root mode — live capture enabled)"
else
    echo "[INFO] Run with sudo for live packet capture"
    echo "[INFO] Without sudo, demo mode will be used"
fi

# Check if Docker mode requested
if [ "$1" = "--docker" ] || [ "$1" = "-d" ]; then
    echo ""
    echo "[DOCKER] Starting with Docker Compose..."
    if ! command -v docker &> /dev/null; then
        echo "[ERROR] Docker not found. Install Docker first."
        exit 1
    fi
    docker compose up -d --build
    echo ""
    echo "[DOCKER] SOC with AI running at http://localhost:8000"
echo "[DOCKER] Login: admin / admin123"
echo "[DOCKER] Logs: docker compose logs -f soc"
    exit 0
fi

# Start server (default: local mode)
echo ""
echo "[START] Launching SOC with AI..."
echo "[START] Dashboard: http://127.0.0.1:8002/"
echo "[START] Login: admin / admin123"
echo "[START] Docker: ./run.sh --docker"
echo ""
$PYTHON start.py --port 8002
