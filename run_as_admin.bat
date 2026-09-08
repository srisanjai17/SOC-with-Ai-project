@echo off
echo =============================================
echo   SOC with AI — Admin Mode
echo   Starting on port 8005 with admin privileges
echo =============================================
cd /d "C:\Users\SRISANJAI\Downloads\SOC project"
set SOC_ADMIN_MODE=1
"C:\Python314\python.exe" -m uvicorn src.api.routes:app --host 0.0.0.0 --port 8005
pause
