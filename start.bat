@echo off
REM Colors for Windows Command Prompt
cls
echo.
echo ==========================================
echo  🚀 Forecast AI - Complete Deployment
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed!
    echo Download Docker from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed!
    echo Install Docker Compose or upgrade Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose detected
echo.

REM Stop any existing containers
echo Stopping existing containers...
docker-compose down

echo.
echo Building and starting all services...
echo This may take 2-3 minutes on first run...
echo.

REM Start all services
docker-compose up --build

echo.
echo ==========================================
echo ✅ All services started!
echo ==========================================
echo.
echo Access your application:
echo.
echo   📱 Dashboard:  http://localhost:3000
echo   🔌 Backend:    http://127.0.0.1:8000
echo   🤖 Ollama:     http://localhost:11434
echo.
echo   API Docs:      http://127.0.0.1:8000/docs
echo.
echo ==========================================
echo.
echo What to do next:
echo 1. Open http://localhost:3000 in your browser
echo 2. Upload sample CSV data (or generate one)
echo 3. Click 'Generate Forecast'
echo 4. Click 'Get Insights' to see Ollama AI in action!
echo.
echo 💡 Tip: Ctrl+C to stop all services.
echo.
pause
