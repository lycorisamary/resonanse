# start.ps1 - Скрипт автоматического запуска приложения для Windows (PowerShell)

Write-Host "=== Запуск приложения Resonans ===" -ForegroundColor Cyan

# 1. Проверка наличия Docker
Write-Host "`n[1/6] Проверка Docker..." -ForegroundColor Yellow
try {
    docker compose version | Out-Null
    Write-Host "Docker Compose найден." -ForegroundColor Green
} catch {
    Write-Host "Ошибка: Docker Compose не найден. Установите Docker Desktop." -ForegroundColor Red
    exit 1
}

# 2. Запуск сервисов (PostgreSQL, Redis, MinIO)
Write-Host "`n[2/6] Запуск зависимостей (DB, Redis, MinIO)..." -ForegroundColor Yellow
docker compose up -d db redis minio
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка при запуске контейнеров." -ForegroundColor Red
    exit 1
}
Write-Host "Контейнеры запущены. Ожидание готовности БД (5 сек)..." -ForegroundColor Green
Start-Sleep -Seconds 5

# 3. Создание виртуального окружения
Write-Host "`n[3/6] Настройка виртуального окружения..." -ForegroundColor Yellow
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "Виртуальное окружение создано." -ForegroundColor Green
} else {
    Write-Host "Виртуальное окружение уже существует." -ForegroundColor Gray
}

# 4. Активация виртуального окружения и установка зависимостей
Write-Host "`n[4/6] Установка зависимостей..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --quiet
Write-Host "Зависимости установлены." -ForegroundColor Green

# 5. Настройка переменных окружения
if (-Not (Test-Path ".env")) {
    Write-Host "`n[5/6] Создание файла .env..." -ForegroundColor Yellow
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
    Write-Host "Файл .env создан." -ForegroundColor Green
} else {
    Write-Host "`n[5/6] Файл .env уже существует." -ForegroundColor Gray
}

# 6. Миграции базы данных
Write-Host "`n[6/6] Применение миграций БД..." -ForegroundColor Yellow
# Перезагружаем среду, чтобы подхватился .env, если он только что создан
Get-Content .env | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
# Выполняем миграции (замените manage.py на вашу команду миграции, например alembic или django migrate)
# Пример для Django:
python manage.py migrate
# Если используется Alembic, раскомментируйте строку ниже и закомментируйте строку выше:
# alembic upgrade head

Write-Host "`n=== ЗАПУСК СЕРВЕРА ===" -ForegroundColor Cyan
Write-Host "Сервер запускается... Откройте браузер по адресу http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "(Для остановки нажмите Ctrl+C)" -ForegroundColor Gray

# Запуск сервера
python manage.py runserver
