#!/bin/bash

# Скрипт для автоматического запуска приложения Резонанс
# Запускает БД, Redis, MinIO, настраивает бэкенд и запускает сервер

set -e

echo "🚀 Запуск приложения Резонанс..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для печати сообщений
print_step() {
    echo -e "${GREEN}[Шаг $1]${NC} $2"
}

print_warning() {
    echo -e "${YELLOW}[Внимание]${NC} $1"
}

print_error() {
    echo -e "${RED}[Ошибка]${NC} $1"
}

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker не найден. Пожалуйста, установите Docker."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не найден. Пожалуйста, установите Docker Compose."
        exit 1
    fi
    
    print_step "1" "Docker и Docker Compose найдены ✓"
}

# Проверка наличия Python
check_python() {
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python не найден. Пожалуйста, установите Python 3.10+."
        exit 1
    fi
    
    PYTHON_CMD=$(command -v python3 || command -v python)
    print_step "2" "Python найден: $PYTHON_CMD ✓"
}

# Запуск сервисов через Docker Compose
start_services() {
    print_step "3" "Запуск PostgreSQL, Redis и MinIO через Docker Compose..."
    
    docker-compose up -d
    
    print_step "3" "Ожидание готовности сервисов (30 секунд)..."
    sleep 30
    
    # Проверка статуса сервисов
    docker-compose ps
    
    print_step "3" "Сервисы запущены ✓"
}

# Настройка бэкенда
setup_backend() {
    print_step "4" "Настройка бэкенда..."
    
    cd backend
    
    # Создание виртуального окружения
    if [ ! -d "venv" ]; then
        print_step "4.1" "Создание виртуального окружения..."
        python3 -m venv venv || python -m venv venv
    else
        print_step "4.1" "Виртуальное окружение уже существует ✓"
    fi
    
    # Активация виртуального окружения
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        print_error "Не удалось активировать виртуальное окружение"
        exit 1
    fi
    
    print_step "4.2" "Установка зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Создание файла .env
    if [ ! -f ".env" ]; then
        print_step "4.3" "Создание файла .env..."
        cp .env.example .env
        
        # Генерация случайного SECRET_KEY
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
        
        print_step "4.3" "Файл .env создан с новым SECRET_KEY ✓"
    else
        print_step "4.3" "Файл .env уже существует ✓"
    fi
    
    cd ..
    print_step "4" "Бэкенд настроен ✓"
}

# Инициализация базы данных
init_database() {
    print_step "5" "Инициализация базы данных..."
    
    cd backend
    
    # Активация виртуального окружения
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    fi
    
    # Создание таблиц
    print_step "5.1" "Создание таблиц..."
    python init_db.py
    
    # Применение миграций
    print_step "5.2" "Применение миграций..."
    python apply_migration.py
    
    cd ..
    print_step "5" "База данных инициализирована ✓"
}

# Запуск сервера
start_server() {
    print_step "6" "Запуск сервера бэкенда..."
    
    cd backend
    
    # Активация виртуального окружения
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    fi
    
    print_step "6" "Сервер запущен на http://localhost:8000"
    print_step "6" "Документация API доступна на http://localhost:8000/docs"
    print_warning "Для остановки нажмите Ctrl+C"
    
    # Запуск сервера
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Основная функция
main() {
    echo ""
    echo "========================================="
    echo "   Резонанс - Автоматический запуск"
    echo "========================================="
    echo ""
    
    check_docker
    check_python
    start_services
    setup_backend
    init_database
    start_server
}

# Запуск основной функции
main
