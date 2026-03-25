@echo off
REM Mouse Jiggler Detector - Windows Setup & Run Script
REM No pip install needed - uses built-in Python ctypes + Win32 API
REM
REM Usage:
REM   Double-click this file, or run from cmd/PowerShell:
REM     run_jiggler_detect.bat
REM     run_jiggler_detect.bat --hook          (detects software-injected events)
REM     run_jiggler_detect.bat --sensitivity high
REM     run_jiggler_detect.bat --log data.csv

echo === Mouse Jiggler Detector (Windows) ===
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python not found. Install Python 3 from python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Download the script if not present
if not exist detect_jiggler.py (
    echo Downloading detect_jiggler.py...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/chaceholland/kvm/claude/detect-mouse-jiggler-XaEl4/detect_jiggler.py' -OutFile 'detect_jiggler.py'"
    if %ERRORLEVEL% neq 0 (
        echo Failed to download. Copy detect_jiggler.py manually to this folder.
        pause
        exit /b 1
    )
    echo.
)

echo Starting jiggler detection (Ctrl+C to stop and see final report)...
echo.
python detect_jiggler.py %*
pause
