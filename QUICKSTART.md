# Быстрый старт - Резонанс

## Минимальные требования

- Python 3.10+
- Docker и Docker Compose
- Flutter SDK 3.0+
- Git

## За 5 минут до первого запуска

### 1. Запуск базы данных (1 минута)

```bash
# Из корневой папки проекта
docker-compose up -d
```

Проверьте, что контейнеры запущены:
```bash
docker-compose ps
```

### 2. Настройка бэкенда (2 минуты)

```bash
cd backend

# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
copy .env.example .env  # Windows
# или
cp .env.example .env    # Linux/Mac

# Генерация SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Скопируйте сгенерированный ключ и вставьте в `.env` файл в строку `SECRET_KEY=...`

### 3. Инициализация базы данных (30 секунд)

```bash
python init_db.py
```

### 4. Запуск бэкенда (30 секунд)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Проверьте работу: откройте http://localhost:8000/docs

### 5. Настройка фронтенда (1 минута)

```bash
# В новом терминале, из корневой папки проекта
cd frontend

# Установка зависимостей
flutter pub get

# Запуск приложения
flutter run
```

## Проверка работы

### Тест API через Swagger

1. Откройте http://localhost:8000/docs
2. Попробуйте зарегистрировать пользователя:
   - POST `/api/v1/auth/register`
   - Email: `test@example.com`
   - Password: `test123456`
   - First name: `Тест`
3. Войдите в систему:
   - POST `/api/v1/auth/login`
   - Используйте те же email и password
   - Скопируйте `access_token` из ответа
4. Получите информацию о пользователе:
   - GET `/api/v1/users/me`
   - Нажмите "Authorize" и вставьте токен

### Тест через curl

```bash
# Регистрация
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456","first_name":"Тест"}'

# Вход
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'

# Получение информации (замените TOKEN на реальный токен)
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer TOKEN"
```

## Что дальше?

- Прочитайте [BACKEND_SETUP.md](docs/BACKEND_SETUP.md) для детальной настройки бэкенда
- Прочитайте [FRONTEND_SETUP.md](docs/FRONTEND_SETUP.md) для детальной настройки фронтенда
- Изучите [API.md](docs/API.md) для полной документации API
- Ознакомьтесь с [ARCHITECTURE.md](docs/ARCHITECTURE.md) для понимания архитектуры

## Частые проблемы

### Ошибка подключения к базе данных

**Решение:** Убедитесь, что Docker Compose запущен:
```bash
docker-compose ps
docker-compose up -d
```

### Ошибка "SECRET_KEY not set"

**Решение:** Создайте файл `.env` и укажите `SECRET_KEY`:
```bash
cd backend
copy .env.example .env
# Отредактируйте .env и укажите SECRET_KEY
```

### Ошибка импорта модулей

**Решение:** Убедитесь, что виртуальное окружение активировано и зависимости установлены:
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Flutter не находит устройства

**Решение:** Запустите эмулятор или подключите устройство:
```bash
flutter devices
flutter emulators --launch <emulator_id>
```

## Остановка сервисов

```bash
# Остановка бэкенда: Ctrl+C в терминале

# Остановка Docker контейнеров
docker-compose down

# Остановка с удалением данных (осторожно!)
docker-compose down -v
```

