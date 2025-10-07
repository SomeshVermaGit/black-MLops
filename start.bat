@echo off
REM Quick start script for MLOps Collaborative Platform (Windows)

echo 🚀 Starting MLOps Collaborative Platform...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

echo ✓ Python found
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo ✅ Setup complete!
echo.
echo Starting API server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

REM Start the server
cd services\api-gateway
python main.py
