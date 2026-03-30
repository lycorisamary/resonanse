# Резонанс - Мобильное приложение для знакомств

Платформа для поиска друзей и единомышленников на основе глубинных интересов.

## Технический стек

- **Бэкенд**: Python 3.11+, FastAPI (асинхронный режим)
- **База данных**: PostgreSQL 14 с расширением PostGIS
- **Кэш**: Redis
- **Фронтенд**: Flutter (Dart), приоритет Android для MVP
- **Инфраструктура**: Docker Compose (PostgreSQL, Redis, MinIO)

## Требования

- Python 3.11 или 3.12 (не используйте Python 3.13 из-за проблем совместимости)
- Docker и Docker Compose
- Flutter SDK (для фронтенда)

## Быстрый старт

### 1. Запуск зависимостей (БД, Redis, MinIO)

```bash
docker-compose up -d
```

Проверьте статус контейнеров:
```bash
docker-compose ps
```

### 2. Настройка бэкенда

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

# Создание файла .env
cp .env.example .env  # Linux/Mac
# или
copy .env.example .env  # Windows

# Редактирование .env (обязательно измените SECRET_KEY!)
# Можно сгенерировать ключ: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Инициализация БД
python init_db.py
python apply_migration.py

# Запуск сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API доступно по адресу: http://localhost:8000  
Документация Swagger: http://localhost:8000/docs

### 3. Настройка фронтенда

```bash
cd frontend

# Установка зависимостей
flutter pub get

# Запуск приложения
flutter run
```

## API Эндпоинты

### Авторизация
- `POST /api/v1/auth/register` - Регистрация нового пользователя
- `POST /api/v1/auth/login` - Вход в систему, получение JWT токена

### Пользователи
- `GET /api/v1/users/me` - Получение информации о текущем пользователе
- `PATCH /api/v1/users/me` - Обновление профиля пользователя
- `POST /api/v1/users/upload-avatar` - Загрузка аватара
- `POST /api/v1/users/change-password` - Смена пароля
- `GET /api/v1/users/nearby` - Поиск пользователей поблизости

### Свайпы и матчи
- `POST /api/v1/swipes` - Отправка свайпа (like/dislike)
- `GET /api/v1/feed` - Лента кандидатов

### Админ-панель
- `GET /api/v1/admin/users` - Список всех пользователей
- `GET /api/v1/admin/users/{user_id}` - Информация о пользователе
- `PATCH /api/v1/admin/users/{user_id}` - Обновление пользователя
- `POST /api/v1/admin/users/{user_id}/activate` - Активация
- `POST /api/v1/admin/users/{user_id}/deactivate` - Деактивация
- `DELETE /api/v1/admin/users/{user_id}` - Удаление

Полная документация доступна по адресу: http://localhost:8000/docs

## Структура проекта

```
Resonans/
├── backend/                 # Бэкенд (FastAPI)
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Конфигурация, БД, безопасность
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── schemas/        # Pydantic схемы
│   │   └── main.py         # Точка входа
│   ├── migrations/         # SQL миграции
│   ├── requirements.txt    # Python зависимости
│   ├── init_db.py          # Инициализация БД
│   └── apply_migration.py  # Применение миграций
├── frontend/               # Flutter приложение
│   └── lib/                # Dart код
├── docker-compose.yml      # Docker сервисы
└── docs/                   # Документация
```

## Дополнительная документация

- [API Documentation](docs/API.md)
- [Backend Setup](docs/BACKEND_SETUP.md)
- [Frontend Setup](docs/FRONTEND_SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [MinIO Setup](docs/SETUP_MINIO.md)

