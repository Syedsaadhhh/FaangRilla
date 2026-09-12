# OpenDoor Relay - Run Local Environment (PowerShell)
# Starts backend (port 8000) and frontend (port 5173) concurrently

$pythonExe = Join-Path $PSScriptRoot "..\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "Virtual environment not found. Initializing..." -ForegroundColor Yellow
    uv venv (Join-Path $PSScriptRoot "..\backend\.venv") --python 3.12
    uv pip install -e (Join-Path $PSScriptRoot "..\backend") --python $pythonExe
}

Write-Host "Starting OpenDoor Relay Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
$backendProc = Start-Process -FilePath $pythonExe -ArgumentList "-m", "uvicorn", "opendoor_relay.api.app:app", "--host", "127.0.0.1", "--port", "8000", "--reload" -PassThru

Write-Host "Starting OpenDoor Relay Frontend on http://127.0.0.1:5173..." -ForegroundColor Cyan
$frontendDir = Join-Path $PSScriptRoot "..\frontend"
$frontendProc = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory $frontendDir -PassThru

Write-Host ""
Write-Host "OpenDoor Relay is running!" -ForegroundColor Green
Write-Host "  - Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  - Backend API: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "  - Health check: http://127.0.0.1:8000/health" -ForegroundColor Green
Write-Host "  - API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to stop all services..." -ForegroundColor Yellow

Read-Host
Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue
Write-Host "Services stopped." -ForegroundColor Gray
