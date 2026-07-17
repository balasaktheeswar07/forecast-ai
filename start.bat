@echo off
REM Forecast AI - Complete Deployment
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
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed!
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose detected
echo.

echo Stopping existing containers...
docker-compose down

echo.
echo Building and starting all services...
echo This may take 2-3 minutes on first run...
echo.

docker-compose up --build
