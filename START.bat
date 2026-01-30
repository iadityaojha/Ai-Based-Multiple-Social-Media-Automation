@echo off
title AI Social Media Automation - Startup
color 0A

echo.
echo ========================================
echo   AI Social Media Automation Platform
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo [OK] Python found
echo [OK] Node.js found
echo.

:: Navigate to project root
cd /d "%~dp0"

:: ========================================
:: BACKEND SETUP
:: ========================================
echo [1/5] Setting up Backend...

cd backend

:: Create virtual environment if not exists
if not exist "venv" (
    echo      Creating virtual environment...
    python -m venv venv
)

:: Activate venv and install dependencies
call venv\Scripts\activate.bat

echo      Installing Python dependencies...
pip install -r requirements.txt -q

:: Create .env if not exists
if not exist ".env" (
    echo      Creating .env file from template...
    copy .env.example .env >nul
    echo.
    echo ========================================
    echo  IMPORTANT: Edit backend\.env file
    echo  Add your SECRET_KEY and ENCRYPTION_KEY
    echo ========================================
    echo.
)

:: Start backend in new window
echo [2/5] Starting Backend Server...
start "Backend - FastAPI" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --port 8000"

cd ..

:: ========================================
:: FRONTEND SETUP
:: ========================================
echo [3/5] Setting up Frontend...

cd frontend

:: Install npm dependencies if needed
if not exist "node_modules" (
    echo      Installing npm dependencies...
    call npm install
)

:: Start frontend in new window
echo [4/5] Starting Frontend Server...
start "Frontend - React" cmd /k "cd /d %~dp0frontend && npm run dev"

cd ..

:: Wait for servers to start
echo [5/5] Waiting for servers to start...
timeout /t 5 /nobreak >nul

:: Open browser
echo.
echo ========================================
echo   Opening browser at http://localhost:3000
echo ========================================
start http://localhost:3000

echo.
echo ========================================
echo   Application is running!
echo ========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   To stop: Close the Backend and Frontend windows
echo.
echo ========================================

pause
