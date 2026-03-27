$BASE = "C:\Users\KAVISH\supplyshield_final"

# ── GeoIntel ──────────────────────────────────────────────────
@"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY sdn.csv /app/data/sdn.csv
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
"@ | Set-Content "$BASE\services\geointel\Dockerfile"

# ── RiskCalc ──────────────────────────────────────────────────
@"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
"@ | Set-Content "$BASE\services\riskcalc\Dockerfile"

# ── Gate ──────────────────────────────────────────────────────
@"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 8003
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
"@ | Set-Content "$BASE\services\gate\Dockerfile"

# ── Summarizer ────────────────────────────────────────────────
@"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 8004
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
"@ | Set-Content "$BASE\services\summarizer\Dockerfile"

# ── Orchestrator ──────────────────────────────────────────────
@"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"@ | Set-Content "$BASE\orchestrator\Dockerfile"

# ── Frontend (root) ───────────────────────────────────────────
@"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true"]
"@ | Set-Content "$BASE\Dockerfile"

# ── .dockerignore at root ─────────────────────────────────────
@"
venv/
__pycache__/
*.pyc
.env
.git/
*.ipynb
data/auth.json
"@ | Set-Content "$BASE\.dockerignore"

Write-Host "All Dockerfiles created successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Files created:" -ForegroundColor Cyan
Write-Host "  $BASE\services\geointel\Dockerfile"
Write-Host "  $BASE\services\riskcalc\Dockerfile"
Write-Host "  $BASE\services\gate\Dockerfile"
Write-Host "  $BASE\services\summarizer\Dockerfile"
Write-Host "  $BASE\orchestrator\Dockerfile"
Write-Host "  $BASE\Dockerfile"
Write-Host "  $BASE\.dockerignore"