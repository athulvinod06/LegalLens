@echo off
echo =======================================================
echo          Starting LegalLens Contract Intelligence
echo =======================================================
echo.

set "NODE_PATH=C:\Users\Athul\AppData\Local\Programs\nodejs"
if exist "%NODE_PATH%" set "PATH=%NODE_PATH%;%PATH%"

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "LegalLens Backend" cmd /k ".\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting React Frontend on http://127.0.0.1:3000 ...
start "LegalLens Frontend" cmd /k "cd frontend && npm run preview -- --port 3000 --host 127.0.0.1"

timeout /t 2 /nobreak >nul

echo Opening browser at http://127.0.0.1:3000 ...
start http://127.0.0.1:3000

echo.
echo LegalLens is now running!
echo - Frontend UI:  http://127.0.0.1:3000
echo - Backend API:  http://127.0.0.1:8000
echo - Swagger Docs: http://127.0.0.1:8000/docs
echo.
pause
