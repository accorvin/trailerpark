@echo off
setlocal enabledelayedexpansion

:: TrailerPark startup script for Windows
cd /d "%~dp0\.."

:: Load port from .env or use default
set PORT=8000
if exist backend\.env (
    for /f "tokens=1,2 delims==" %%a in ('findstr /b "PORT=" backend\.env') do set PORT=%%b
)

:: Check if port is in use
netstat -ano | findstr ":%PORT% " >nul 2>&1
if %errorlevel%==0 (
    echo WARNING: Port %PORT% is already in use. Another instance may be running.
    echo Press Ctrl+C to cancel or any key to continue anyway...
    pause >nul
)

echo Starting TrailerPark on port %PORT%...

set RESTART_COUNT=0
set MAX_RESTARTS=5

:start_loop
if !RESTART_COUNT! geq %MAX_RESTARTS% (
    echo TrailerPark has crashed %MAX_RESTARTS% times. Giving up.
    echo Check data\logs\trailerpark.log for details.
    pause
    exit /b 1
)

:: Start uvicorn
cd backend
uv run uvicorn src.main:app --host 0.0.0.0 --port %PORT%
set EXIT_CODE=%errorlevel%
cd ..

if %EXIT_CODE% neq 0 (
    set /a RESTART_COUNT+=1
    echo TrailerPark crashed (exit code %EXIT_CODE%). Restart !RESTART_COUNT!/%MAX_RESTARTS%...
    timeout /t 5 /nobreak >nul
    goto start_loop
)

:: Open browser on first start (only if not restarting)
if !RESTART_COUNT! equ 0 (
    timeout /t 2 /nobreak >nul
    start http://localhost:%PORT%
)
