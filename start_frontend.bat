@echo off
REM Script to start both backend and frontend servers on Windows

echo Starting Australian Visa Scraper Frontend...
echo.

REM Start backend in background
echo Starting backend API server on port 8000...
start "Backend API" cmd /c "python -m api.server 8000"

REM Wait a bit for backend to start
timeout /t 2 /nobreak >nul

REM Start frontend
echo Starting frontend development server...
cd frontend
call npm run dev

