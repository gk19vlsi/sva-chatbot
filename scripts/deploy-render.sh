#!/bin/bash

# SVA-Chatbot Render Deployment Script
# This script provides instructions for deploying to Render

set -e

echo "🎨 SVA-Chatbot Render Deployment Guide"
echo "======================================="
echo ""
echo "Render deployment is done through their web interface."
echo "Follow these steps:"
echo ""
echo "1️⃣  Create Render Account"
echo "   Visit: https://render.com"
echo ""
echo "2️⃣  Create MongoDB Database"
echo "   - Go to Dashboard → New → MongoDB"
echo "   - Or use MongoDB Atlas"
echo "   - Copy the connection string"
echo ""
echo "3️⃣  Create Backend Web Service"
echo "   - Dashboard → New → Web Service"
echo "   - Connect your GitHub repository"
echo "   - Settings:"
echo "     * Name: sva-chatbot-backend"
echo "     * Root Directory: backend"
echo "     * Build Command: pip install -r requirements.txt"
echo "     * Start Command: uvicorn app.main:app --host 0.0.0.0 --port \$PORT --workers 4"
echo ""
echo "   - Environment Variables:"
echo "     * MONGODB_URL=<your-mongodb-connection-string>"
echo "     * MONGODB_DB_NAME=sva_chatbot"
echo "     * GROQ_API_KEY=<your-groq-api-key>"
echo "     * JWT_SECRET_KEY=<generate-strong-secret>"
echo "     * ENVIRONMENT=production"
echo "     * DEBUG=false"
echo "     * CORS_ORIGINS=<your-frontend-url>"
echo ""
echo "4️⃣  Create Frontend Web Service"
echo "   - Dashboard → New → Web Service"
echo "   - Connect your GitHub repository"
echo "   - Settings:"
echo "     * Name: sva-chatbot-frontend"
echo "     * Root Directory: frontend"
echo "     * Build Command: npm install && npm run build"
echo "     * Start Command: npm install -g serve && serve -s dist -l \$PORT"
echo ""
echo "   - Environment Variables:"
echo "     * VITE_API_URL=<your-backend-url>"
echo "     * VITE_WS_URL=<your-backend-ws-url>"
echo ""
echo "5️⃣  Deploy"
echo "   - Render will automatically build and deploy"
echo "   - Monitor deployment logs"
echo "   - Get public URLs for both services"
echo ""
echo "6️⃣  Update Configuration"
echo "   - Update backend CORS_ORIGINS with frontend URL"
echo "   - Update frontend VITE_API_URL with backend URL"
echo "   - Redeploy if needed"
echo ""
echo "7️⃣  Verify Deployment"
echo "   - Visit frontend URL"
echo "   - Check backend health: <backend-url>/health"
echo "   - Test functionality"
echo ""
echo "📝 Render Configuration Files"
echo ""
echo "You can also use render.yaml for infrastructure as code."
echo "See: https://render.com/docs/infrastructure-as-code"
echo ""

# Offer to create render.yaml
read -p "Would you like to create a render.yaml file? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > render.yaml << 'EOF'
services:
  - type: web
    name: sva-chatbot-backend
    env: python
    region: oregon
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
    envVars:
      - key: MONGODB_URL
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
    healthCheckPath: /health/live

  - type: web
    name: sva-chatbot-frontend
    env: node
    region: oregon
    plan: starter
    buildCommand: npm install && npm run build
    startCommand: npm install -g serve && serve -s dist -l $PORT
    envVars:
      - key: VITE_API_URL
        sync: false
      - key: VITE_WS_URL
        sync: false
EOF
    echo "✅ Created render.yaml"
    echo "Edit it with your configuration and commit to your repository"
fi

echo ""
echo "✅ Render deployment guide complete!"
echo ""
