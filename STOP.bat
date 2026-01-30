@echo off
title Stop All Servers
echo.
echo Stopping all servers...
echo.

:: Kill Python (backend)
taskkill /f /im python.exe >nul 2>&1

:: Kill Node (frontend)  
taskkill /f /im node.exe >nul 2>&1

echo All servers stopped.
timeout /t 2 >nul
