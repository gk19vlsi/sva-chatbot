#!/bin/bash

# Start backend development server with error handling
echo "Starting SVA-Chatbot Backend..."
echo "================================"
echo ""
echo "Note: Database connection issues are expected in development."
echo "The server will start but some features may not work without MongoDB."
echo ""

# Activate virtual environment and start server
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
