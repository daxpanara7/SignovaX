@echo off
echo 🚀 SMC Trading System - Demo Launcher (Windows)
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16 or higher.
    pause
    exit /b 1
)

echo ✅ Requirements check passed

REM Setup backend
echo.
echo 🔧 Setting up backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo 📚 Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating environment configuration...
    echo APP_ENV=development > .env
    echo SECRET_KEY=smc-trading-system-demo-key-2024 >> .env
    echo DATABASE_URL=sqlite:///./smc_trading.db >> .env
    echo ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 >> .env
    echo HOST=0.0.0.0 >> .env
    echo PORT=8000 >> .env
    echo LOG_LEVEL=INFO >> .env
    echo WORKERS=1 >> .env
)

cd ..

REM Setup frontend
echo.
echo 🎨 Setting up frontend...
cd frontend
echo 📦 Installing Node.js dependencies...
npm install
cd ..

echo.
echo 🚀 Starting SMC Trading System...
echo.

REM Start backend in background
echo 🔧 Starting backend server...
start "SMC Backend" cmd /c "cd backend && venv\Scripts\activate.bat && python run.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo 🎨 Starting frontend server...
start "SMC Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo 🎉 SMC Trading System is starting up!
echo ==================================================
echo 🌐 Frontend Dashboard: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo 📖 API Documentation: http://localhost:8000/docs
echo ==================================================
echo.
echo 💡 Demo Features:
echo    • Professional trading terminal interface
echo    • Real-time price simulation
echo    • SMC signal generation
echo    • Performance analytics
echo    • Risk management tools
echo    • Multi-timeframe analysis
echo.
echo 🔑 Demo Login (if needed):
echo    Username: admin
echo    Password: smc_admin_2024
echo.
echo ⏹️ Close the terminal windows to stop the servers
echo.
pause