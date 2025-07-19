@echo off
REM MistHelper Podman Build and Run Script for Windows
REM Follows NASA/JPL documentation standards with comprehensive logging
REM Usage: run-podman.bat [menu_number]
REM Example: run-podman.bat 11

REM Set default menu option
set MENU_OPTION=11
if not "%1"=="" set MENU_OPTION=%1

echo ============================================================
echo MistHelper Podman Setup and Execution Script
echo ============================================================
echo Created: 2025-07-16
echo Purpose: Build and run MistHelper in Podman container
echo Platform: Windows with Podman Desktop
echo Menu Option: %MENU_OPTION%
echo ============================================================

REM Check if Podman is running
echo [INFO] Checking Podman availability...
"C:\Program Files\RedHat\Podman\podman.exe" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Podman is not installed or not running.
    echo [ERROR] Please install Podman Desktop and ensure it is running.
    pause
    exit /b 1
)
echo [SUCCESS] Podman is available.

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found.
    echo [ERROR] Please create .env file with your Mist API credentials:
    echo [ERROR] MIST_HOST=api.mist.com
    echo [ERROR] MIST_APITOKEN=your_api_token_here
    echo [ERROR] MIST_ORG_ID=your_org_id_here
    pause
    exit /b 1
)
echo [SUCCESS] .env file found.

REM Create data directory if it doesn't exist
if not exist "data" (
    echo [INFO] Creating data directory for database persistence...
    mkdir data
    echo [SUCCESS] Data directory created.
) else (
    echo [INFO] Data directory already exists.
)

REM Build Podman image
echo [INFO] Building MistHelper Podman image...
"C:\Program Files\RedHat\Podman\podman.exe" build -t misthelper:latest .
if %errorlevel% neq 0 (
    echo [ERROR] Podman build failed.
    pause
    exit /b 1
)
echo [SUCCESS] Podman image built successfully.

REM Run container interactively
echo [INFO] Starting MistHelper container...
echo [INFO] Database will be stored in: %cd%\data\mist_data.db
echo [INFO] Press Ctrl+C to exit the container.
echo ============================================================

"C:\Program Files\RedHat\Podman\podman.exe" run -it --rm ^
    -v "%cd%\data:/app/data:Z" ^
    -v "%cd%\.env:/app/.env:ro,Z" ^
    --name misthelper-interactive ^
    misthelper:latest ^
    python MistHelper.py --output-format sqlite --menu %MENU_OPTION%

echo ============================================================
echo [INFO] Container has exited.
echo [INFO] Database file location: %cd%\data\mist_data.db
echo [INFO] To access the database directly:
echo [INFO] "C:\Program Files\RedHat\Podman\podman.exe" run --rm -it -v "%cd%\data:/app/data:Z" misthelper:latest sqlite3 /app/data/mist_data.db
echo ============================================================
pause
