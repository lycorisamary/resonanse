# start.ps1 - Auto-start script for Windows (PowerShell)

Write-Host "=== Starting Resonans Application ===" -ForegroundColor Cyan

# 1. Check Docker
Write-Host "`n[1/6] Checking Docker..." -ForegroundColor Yellow
try {
    docker compose version | Out-Null
    Write-Host "Docker Compose found." -ForegroundColor Green
} catch {
    Write-Host "Error: Docker Compose not found. Install Docker Desktop." -ForegroundColor Red
    exit 1
}

# 2. Start services (PostgreSQL, Redis, MinIO)
Write-Host "`n[2/6] Starting dependencies (DB, Redis, MinIO)..." -ForegroundColor Yellow
docker compose up -d db redis minio
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error starting containers." -ForegroundColor Red
    exit 1
}
Write-Host "Containers started. Waiting for DB readiness (5 sec)..." -ForegroundColor Green
Start-Sleep -Seconds 5

# 3. Create virtual environment
Write-Host "`n[3/6] Setting up virtual environment..." -ForegroundColor Yellow
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Gray
}

# 4. Activate venv and install dependencies
Write-Host "`n[4/6] Installing dependencies..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --quiet
Write-Host "Dependencies installed." -ForegroundColor Green

# 5. Setup environment variables
if (-Not (Test-Path ".env")) {
    Write-Host "`n[5/6] Creating .env file..." -ForegroundColor Yellow
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    @"
SECRET_KEY=$secretKey
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/resonans_db
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
"@ | Out-File -Encoding ASCII .env
    Write-Host ".env file created." -ForegroundColor Green
} else {
    Write-Host "`n[5/6] .env file already exists." -ForegroundColor Gray
}

# 6. Database migrations
Write-Host "`n[6/6] Applying database migrations..." -ForegroundColor Yellow
Get-Content .env | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
python manage.py migrate

Write-Host "`n=== SERVER STARTING ===" -ForegroundColor Cyan
Write-Host "Server starting... Open browser at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "(Press Ctrl+C to stop)" -ForegroundColor Gray

# Start server
python manage.py runserver
