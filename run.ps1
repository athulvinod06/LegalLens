Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "         Starting LegalLens Contract Intelligence      " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

$nodePath = "C:\Users\Athul\AppData\Local\Programs\nodejs"
if (Test-Path $nodePath) {
    $env:PATH = "$nodePath;" + $env:PATH
}

Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting React Frontend on http://127.0.0.1:3000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PATH = '$nodePath;' + `$env:PATH; cd frontend; npm run preview -- --port 3000 --host 127.0.0.1"

Start-Sleep -Seconds 2

Write-Host "Opening browser at http://127.0.0.1:3000 ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:3000"

Write-Host ""
Write-Host "LegalLens is running successfully!" -ForegroundColor Green
Write-Host "- Frontend UI:  http://127.0.0.1:3000"
Write-Host "- Backend API:  http://127.0.0.1:8000"
Write-Host "- Swagger Docs: http://127.0.0.1:8000/docs"
