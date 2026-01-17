#!/bin/bash

# SVA-Chatbot Local Deployment Script
# This script sets up and runs the application locally using Docker Compose

set -e

echo "🚀 SVA-Chatbot Local Deployment"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Backend .env file not found. Creating from example..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env - Please edit it with your configuration"
fi

if [ ! -f "frontend/.env" ]; then
    echo "⚠️  Frontend .env file not found. Creating from example..."
    cp frontend/.env.example frontend/.env
    echo "✅ Created frontend/.env"
fi

# Stop any running containers
echo ""
echo "🛑 Stopping any running containers..."
docker-compose down

# Pull latest images
echo ""
echo "📥 Pulling latest images..."
docker-compose pull

# Build images
echo ""
echo "🔨 Building images..."
docker-compose build

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "🏥 Checking service health..."

if curl -f http://localhost:8000/health/live &> /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs backend
    exit 1
fi

if curl -f http://localhost:3000 &> /dev/null; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️  Frontend may still be starting..."
fi

# Display status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo "  - MongoDB: mongodb://localhost:27017"
echo ""
echo "📝 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart: docker-compose restart"
echo ""
