@echo off
setlocal

:: TrailerPark first-time setup script for Windows
cd /d "%~dp0\.."

echo ================================
echo  TrailerPark Setup
echo ================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not on PATH.
    echo Please install Python 3.12+ from https://www.python.org/downloads/
    exit /b 1
)
echo [OK] Python found

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not on PATH.
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)
echo [OK] Node.js found

:: Check uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: uv is not installed.
    echo Install with: pip install uv
    exit /b 1
)
echo [OK] uv found

:: Check .env
if not exist backend\.env (
    echo ERROR: backend\.env file not found.
    echo Please copy backend\.env.example to backend\.env and fill in the values.
    exit /b 1
)
echo [OK] .env file found

:: Verify required env vars
for /f "tokens=1,2 delims==" %%a in ('findstr /b "EMAIL_DIR=" backend\.env') do (
    if "%%b"=="" (
        echo ERROR: EMAIL_DIR is not set in backend\.env
        exit /b 1
    )
)
for /f "tokens=1,2 delims==" %%a in ('findstr /b "OPENAI_API_KEY=" backend\.env') do (
    if "%%b"=="" (
        echo ERROR: OPENAI_API_KEY is not set in backend\.env
        exit /b 1
    )
)
echo [OK] Required config values present

:: Install Python dependencies
echo.
echo Installing Python dependencies...
cd backend
uv sync
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies.
    exit /b 1
)
echo [OK] Python dependencies installed

:: Install dev dependencies
uv sync --extra dev
cd ..

:: Install Node dependencies
echo.
echo Installing Node dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Node dependencies.
    exit /b 1
)
echo [OK] Node dependencies installed

:: Build frontend
echo.
echo Building frontend...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Failed to build frontend.
    exit /b 1
)
echo [OK] Frontend built
cd ..

:: Run database migrations
echo.
echo Running database migrations...

:: Backup existing DB if it exists
if exist backend\data\trailerpark.db (
    echo Backing up existing database...
    copy backend\data\trailerpark.db backend\data\trailerpark-pre-migration.db >nul
)

cd backend
uv run alembic -c alembic/alembic.ini upgrade head
if %errorlevel% neq 0 (
    echo ERROR: Database migration failed!
    if exist data\trailerpark-pre-migration.db (
        echo Restoring database backup...
        copy data\trailerpark-pre-migration.db data\trailerpark.db >nul
    )
    exit /b 1
)
echo [OK] Database migrated
cd ..

echo.
echo ================================
echo  Setup complete!
echo  Run scripts\start.bat to start the app.
echo ================================
