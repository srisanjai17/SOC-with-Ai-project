#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# SOC with AI — Docker Entrypoint
# Handles graceful startup, config validation, and signal handling
# ═══════════════════════════════════════════════════════════════════
set -e

echo "======================================"
echo "  SOC with AI — Starting Up"
echo "======================================"

# ── Validate config ────────────────────────────────────────────────
if [ -f /app/config.yaml ]; then
    echo "[1/4] Config file found ✓"
else
    echo "[1/4] No config file, using defaults"
fi

# ── Create data directories ────────────────────────────────────────
mkdir -p /app/data /app/logs
echo "[2/4] Data directories ready ✓"

# ── Set environment defaults ───────────────────────────────────────
export SOC_HOST="${SOC_HOST:-0.0.0.0}"
export SOC_PORT="${SOC_PORT:-8000}"
export SOC_WORKERS="${SOC_WORKERS:-4}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"

echo "[3/4] Environment configured:"
echo "  Host:     $SOC_HOST"
echo "  Port:     $SOC_PORT"
echo "  Workers:  $SOC_WORKERS"

# ── Handle SIGTERM/SIGINT for graceful shutdown ────────────────────
cleanup() {
    echo ""
    echo "Shutting down SOC with AI gracefully..."
    kill -TERM "$PID" 2>/dev/null
    wait "$PID" 2>/dev/null
    echo "Shutdown complete."
}

trap cleanup SIGTERM SIGINT

# ── Start server ──────────────────────────────────────────────────
echo "[4/4] Starting SOC with AI server..."
echo "  Dashboard: http://${SOC_HOST}:${SOC_PORT}/"
echo "  API docs:  http://${SOC_HOST}:${SOC_PORT}/docs"
echo "======================================"

exec python server.py --host "$SOC_HOST" --port "$SOC_PORT" &
PID=$!
wait "$PID"
