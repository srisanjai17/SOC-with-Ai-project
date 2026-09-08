@echo off
REM ============================================================
REM SOC with AI — One-Click Development Setup (Windows)
REM Double-click this file to install everything:
REM   - Runtime dependencies (requirements.txt)
REM   - Dev dependencies (requirements-dev.txt)
REM   - Playwright Chromium (E2E tests)
REM   - Git hooks (pre-commit, commit-msg, post-merge, pre-push)
REM ============================================================

echo.
echo ========================================
echo   SOC with AI - Development Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH.
    echo.
    echo Install Python 3.10+ from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Run the setup script
python scripts\setup_dev.py %*

REM Keep window open on completion
echo.
echo ========================================
echo   Setup complete!
echo ========================================
echo.
pause
