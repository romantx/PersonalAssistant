@echo off
echo ==============================================
echo 🚀 Starting the Personal Agent Team...
echo ==============================================

echo Starting Python Backend (Port 8000)...
start "Agent Backend" cmd /k "cd backend && venv\Scripts\uvicorn main:app --reload"

echo Starting React Frontend (Port 5173)...
start "Agent Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers have been launched in separate terminal windows!
echo Once they finish booting, open your browser to:
echo http://localhost:5173/
echo.
pause
