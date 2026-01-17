#!/bin/bash

# SVA-Chatbot Railway Deployment Script
# This script helps deploy the application to Railway

set -e

echo "🚂 SVA-Chatbot Railway Deployment"
echo "=================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI is not installed"
    echo "Install it with: npm install -g @railway/cli"
    echo "Or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
fi

# Check if project exists
if ! railway status &> /dev/null; then
    echo "📦 Creating new Railway project..."
    railway init
else
    echo "✅ Using existing Railway project"
fi

# Deploy backend
echo ""
echo "🚀 Deploying backend..."
cd backend

# Set environment variables
echo "Setting backend environment variables..."
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set WORKERS=4

echo "⚠️  Please set the following variables manually in Railway dashboard:"
echo "  - GROQ_API_KEY"
echo "  - JWT_SECRET_KEY"
echo "  - MONGODB_URL (from Railway MongoDB service)"
echo ""
read -p "Press Enter when you've set the variables..."

# Deploy
railway up

cd ..

# Deploy frontend
echo ""
echo "🚀 Deploying frontend..."
cd frontend

# Set environment variables
echo "Setting frontend environment variables..."
echo "⚠️  Please set VITE_API_URL to your backend Railway URL"
read -p "Enter backend URL (e.g., https://your-backend.railway.app): " BACKEND_URL
railway variables set VITE_API_URL="$BACKEND_URL"
railway variables set VITE_WS_URL="${BACKEND_URL/https/wss}"

# Deploy
railway up

cd ..

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Get your service URLs: railway status"
echo "  2. Update CORS_ORIGINS in backend with frontend URL"
echo "  3. Test your deployment"
echo ""
