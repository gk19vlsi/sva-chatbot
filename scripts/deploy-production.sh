#!/bin/bash

# SVA-Chatbot Production Deployment Script
# This script deploys the application to production using Docker Compose

set -e

echo "🚀 SVA-Chatbot Production Deployment"
echo "====================================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script should be run with sudo for production deployment"
    echo "Usage: sudo ./scripts/deploy-production.sh"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    exit 1
fi

# Check if production .env files exist
if [ ! -f "backend/.env.production" ]; then
    echo "❌ Error: backend/.env.production not found"
    echo "Please create it from backend/.env.production.example"
    exit 1
fi

if [ ! -f "frontend/.env.production" ]; then
    echo "❌ Error: frontend/.env.production not found"
    echo "Please create it from frontend/.env.production.example"
    exit 1
fi

# Check if MongoDB credentials are set
if [ -z "$MONGO_ROOT_USERNAME" ] || [ -z "$MONGO_ROOT_PASSWORD" ]; then
    echo "❌ Error: MongoDB credentials not set"
    echo "Please set MONGO_ROOT_USERNAME and MONGO_ROOT_PASSWORD environment variables"
    exit 1
fi

# Backup current deployment
echo ""
echo "💾 Creating backup..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "Backing up current deployment..."
    docker-compose -f docker-compose.prod.yml logs > "$BACKUP_DIR/logs.txt"
    echo "✅ Backup created in $BACKUP_DIR"
fi

# Pull latest code
echo ""
echo "📥 Pulling latest code..."
git pull origin main

# Build images
echo ""
echo "🔨 Building production images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop current deployment
echo ""
echo "🛑 Stopping current deployment..."
docker-compose -f docker-compose.prod.yml down

# Start new deployment
echo ""
echo "🚀 Starting production deployment..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check health
echo ""
echo "🏥 Checking service health..."

MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health/ready &> /dev/null; then
        echo "✅ Backend is healthy"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "⏳ Waiting for backend... (attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 5
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Backend health check failed after $MAX_RETRIES attempts"
    echo "Rolling back..."
    docker-compose -f docker-compose.prod.yml down
    exit 1
fi

# Display status
echo ""
echo "✅ Production deployment complete!"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "📝 Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Check health: curl http://localhost:8000/health"
echo "  - Stop services: docker-compose -f docker-compose.prod.yml down"
echo ""
echo "⚠️  Remember to:"
echo "  - Configure your reverse proxy (Nginx)"
echo "  - Set up SSL certificates"
echo "  - Configure firewall rules"
echo "  - Set up monitoring and alerts"
echo ""
