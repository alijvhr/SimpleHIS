@echo off
REM Quick Start Script for Simple Hospital Information System (Windows)

echo ==========================================
echo Simple Hospital Information System
echo Quick Start Installation (Windows)
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version

if errorlevel 1 (
    echo X Python is not installed. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo OK Python is installed
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo X Failed to install dependencies
    pause
    exit /b 1
)

echo OK Dependencies installed
echo.

REM Check if database exists
if exist hospital.db (
    echo ! Database already exists. Skipping initialization.
) else (
    echo Creating initial admin user...
    echo admin> temp_input.txt
    echo مدیر سیستم>> temp_input.txt
    echo admin123>> temp_input.txt
    python initial_admin.py < temp_input.txt
    del temp_input.txt
    
    if errorlevel 1 (
        echo X Failed to create admin user
        pause
        exit /b 1
    )
    
    echo OK Admin user created
)

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Default Admin Credentials:
echo   Username: admin
echo   Password: admin123
echo.
echo To start the server, run:
echo   python main.py
echo.
echo Or:
echo   uvicorn main:app --reload
echo.
echo Then open your browser to:
echo   http://localhost:8000
echo.
echo ==========================================
echo For more information, see README.md
echo ==========================================
echo.
pause
