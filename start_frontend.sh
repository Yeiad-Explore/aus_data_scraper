#!/bin/bash
# Script to start both backend and frontend servers

echo "Starting Australian Visa Scraper Frontend..."
echo ""

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "Backend API already running on port 8000"
else
    echo "Starting backend API server on port 8000..."
    python -m api.server 8000 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    sleep 2
fi

# Start frontend
echo "Starting frontend development server..."
cd frontend
npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT

