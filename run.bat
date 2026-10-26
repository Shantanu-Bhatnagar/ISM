@echo off
title OmniStore ISM - Enterprise Information Storage Management
color 0b
echo ======================================================================
echo    OMNISTORE ISM - ENTERPRISE INFORMATION STORAGE MANAGEMENT PLATFORM
echo ======================================================================
echo.
echo [*] Checking Python installation...
python --version
if errorlevel 1 (
    echo [!] Python is not found in PATH. Please install Python 3.8+ and try again.
    pause
    exit /b
)

echo.
echo [*] Checking and installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo [*] Launching OmniStore ISM Console...
python run.py
pause
