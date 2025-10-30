$ErrorActionPreference = "Stop"

Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
python -m pip install -r backend/requirements.txt

Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
if (Test-Path "frontend/requirement.txt") {
  python -m pip install -r frontend/requirement.txt
} else {
  python -m pip install streamlit requests pandas
}

Write-Host "Starting backend (FastAPI on :8000)..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
  python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
}

# Wait for backend readiness (max ~20s)
$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline) {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) { break }
  } catch { Start-Sleep -Milliseconds 800 }
}

if ((Get-Job -Id $backendJob.Id).State -eq 'Failed') {
  Write-Host "Backend job failed. Showing logs:" -ForegroundColor Red
  Receive-Job $backendJob -Keep
  throw "Backend failed to start"
}

Write-Host "Backend is up (or timed out). Latest logs:" -ForegroundColor Green
Receive-Job $backendJob -Keep | Select-Object -Last 10 | ForEach-Object { $_ }

Write-Host "Starting frontend (Streamlit on :8501)..." -ForegroundColor Cyan
python -m streamlit run frontend/app.py --server.port 8501 --server.address 127.0.0.1


