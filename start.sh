#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Forecast AI - Complete Deployment${NC}"
echo "=================================================="

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose detected${NC}"
echo ""

echo -e "${BLUE}Stopping existing containers...${NC}"
docker-compose down

echo ""
echo -e "${BLUE}Building and starting all services...${NC}"
echo "This may take 2-3 minutes on first run..."
echo ""

docker-compose up --build
