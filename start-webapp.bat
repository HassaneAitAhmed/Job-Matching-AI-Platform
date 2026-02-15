@echo off
REM Job Matching AI Platform - Startup Script for Windows

echo Starting Job Matching AI Platform...
echo.

REM Check if webapp directory exists
if not exist "webapp\" (
    echo Error: webapp directory not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed!
    echo Please install Python 3.9 or higher.
    pause
    exit /b 1
)

echo Checking dependencies...

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    cd webapp
    pip install -r requirements.txt --user
    cd ..
) else (
    echo Dependencies already installed
)

echo.
echo Starting web server...
echo Navigate to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

cd webapp
python app.py
