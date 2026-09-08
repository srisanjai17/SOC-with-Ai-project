@echo off
title SOC with AI — Real-Time Network Defense
echo.
echo ================================================
echo   SOC with AI — Real-Time Network Defense System
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Install dependencies
echo [SETUP] Checking dependencies...
python -m pip install -q fastapi "uvicorn[standard]" pydantic python-dateutil jinja2 scikit-learn numpy scipy brotli-asgi scapy 2>nul

REM Start server
echo [START] Launching SOC with AI...
echo [START] Dashboard: http://127.0.0.1:8002/
echo [START] Login: admin / admin123
echo.
python start.py --port 8002

pause
