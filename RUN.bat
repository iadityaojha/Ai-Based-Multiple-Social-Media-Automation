@echo off
title AI Social Media Automation - Quick Start
color 0A

echo.
echo ========================================
echo   AI Social Media Automation Platform
echo        Quick Start (already setup)
echo ========================================
echo.

cd /d "%~dp0"

:: Start Backend
echo Starting Backend...
start "Backend - FastAPI" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --port 8000"

:: Start Frontend
echo Starting Frontend...
start "Frontend - React" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait and open browser
timeout /t 4 /nobreak >nul
start http://localhost:3000

echo.
echo ========================================
echo   Application is running!
echo ========================================
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo.
echo   Close this window to continue working.
echo   To stop servers, close their windows.
echo ========================================
echo.

timeout /t 3 >nul
