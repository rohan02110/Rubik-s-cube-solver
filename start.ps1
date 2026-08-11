Write-Host "Starting Rubik's Cube Solver Services..." -ForegroundColor Cyan

# 1. Start Flask API in a new window
Write-Host "1. Launching Flask API Server (Port 5000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Activating virtual environment...'; .\venv\Scripts\Activate.ps1; Write-Host 'Installing backend dependencies...'; pip install -r api/requirements.txt; Write-Host 'Starting Flask...'; python api/app.py"

# 2. Start Node.js Express Frontend in a new window
Write-Host "2. Launching Node.js Express Frontend (Port 3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Starting Frontend...'; cd frontend; npm start"

Write-Host ""
Write-Host "Both services are starting up in separate PowerShell windows." -ForegroundColor Cyan
Write-Host "Once initialized, visit: http://localhost:3000" -ForegroundColor Yellow