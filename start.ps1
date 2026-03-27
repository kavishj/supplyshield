$BASE = "C:\Users\KAVISH\supplyshield_final"
$PYTHON = "$BASE\venv\Scripts\python.exe"

# Load .env file
Get-Content "$BASE\.env" | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
    }
}

Write-Host "Starting SupplyShield services..." -ForegroundColor Cyan
Write-Host ""

# Start all 5 services in separate windows
Start-Process powershell -ArgumentList "-NoExit", "-Command", 
    "cd '$BASE\services\geointel'; & '$PYTHON' -m uvicorn main:app --port 8001 --reload" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", 
    "cd '$BASE\services\riskcalc'; & '$PYTHON' -m uvicorn main:app --port 8002 --reload" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", 
    "cd '$BASE\services\gate'; & '$PYTHON' -m uvicorn main:app --port 8003 --reload" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$BASE\services\summarizer'; `$env:HUGGINGFACE_API_TOKEN='$env:HUGGINGFACE_API_TOKEN'; & '$PYTHON' -m uvicorn main:app --port 8004 --reload" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$BASE\services\recommender'; `$env:HUGGINGFACE_API_TOKEN='$env:HUGGINGFACE_API_TOKEN'; `$env:SERPER_API_KEY='$env:SERPER_API_KEY'; & '$PYTHON' -m uvicorn main:app --port 8005 --reload" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$BASE\orchestrator'; & '$PYTHON' -m uvicorn main:app --port 8000 --reload" `
    -WindowStyle Normal

Start-Sleep -Seconds 3

# Start BFF (port 8006)
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$BASE\bff'; & '$PYTHON' -m uvicorn main:app --port 8006 --reload" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

# Start React frontend (port 5173) — requires Node.js + npm install already done
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$BASE\frontend'; npm run dev" `
    -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "All services started." -ForegroundColor Green
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  GeoIntelAgent       -> http://127.0.0.1:8001/docs"
Write-Host "  RiskCalculatorAgent -> http://127.0.0.1:8002/docs"
Write-Host "  ProcurementGate     -> http://127.0.0.1:8003/docs"
Write-Host "  SummarizerAgent     -> http://127.0.0.1:8004/docs"
Write-Host "  RecommenderAgent    -> http://127.0.0.1:8005/docs"
Write-Host "  Orchestrator        -> http://127.0.0.1:8000/docs"
Write-Host "  BFF                 -> http://127.0.0.1:8006/docs"
Write-Host "  React UI            -> http://127.0.0.1:5173"
Write-Host ""