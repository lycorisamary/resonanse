# Инструкция по настройке и запуску бэкенда

## Требования

- Python 3.10 или выше
- PostgreSQL 14 (запускается через Docker Compose)
- Redis (запускается через Docker Compose)
- pip (менеджер пакетов Python)

## Пошаговая настройка

### 1. Подготовка окружения

#### 1.1. Создание виртуального окружения

Рекомендуется использовать виртуальное окружение для изоляции зависимостей:

```bash
# Перейдите в папку backend
cd backend

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

#### 1.2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

#### 2.1. Создание файла .env

Скопируйте пример файла окружения:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

#### 2.2. Редактирование .env

Откройте файл `.env` и настройте следующие параметры:

**Обязательные параметры:**

- `POSTGRES_USER` - пользователь PostgreSQL (по умолчанию: `resonans_user`)
- `POSTGRES_PASSWORD` - пароль PostgreSQL (по умолчанию: `resonans_password`)
- `POSTGRES_DB` - название базы данных (по умолчанию: `resonans_db`)
- `SECRET_KEY` - секретный ключ для JWT токенов (**обязательно измените!**)

**Генерация SECRET_KEY:**

Для генерации безопасного секретного ключа выполните:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Скопируйте сгенерированный ключ в файл `.env`.

**Опциональные параметры:**

- `DEBUG` - режим отладки (True/False)
- `POSTGRES_HOST` - хост PostgreSQL (по умолчанию: `localhost`)
- `POSTGRES_PORT` - порт PostgreSQL (по умолчанию: `5432`)
- `REDIS_HOST` - хост Redis (по умолчанию: `localhost`)
- `REDIS_PORT` - порт Redis (по умолчанию: `6379`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - время жизни JWT токена в минутах (по умолчанию: 10080 = 7 дней)

### 3. Запуск базы данных и Redis

Убедитесь, что Docker Compose запущен из корневой папки проекта:

```bash
# Из корневой папки проекта
docker-compose up -d
```

Проверьте, что контейнеры запущены:

```bash
docker-compose ps
```

Должны быть запущены:
- `resonans_postgres` (PostgreSQL)
- `resonans_redis` (Redis)

### 4. Инициализация базы данных

Создайте таблицы в базе данных:

```bash
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

Или создайте скрипт `init_db.py`:

```python
import asyncio
from app.core.database import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
    print("База данных инициализирована!")
```

Затем запустите:

```bash
python init_db.py
```

### 5. Запуск сервера

#### 5.1. Запуск через uvicorn (рекомендуется для разработки)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Параметры:
- `--reload` - автоматическая перезагрузка при изменении кода
- `--host 0.0.0.0` - доступ со всех интерфейсов
- `--port 8000` - порт сервера

#### 5.2. Проверка работы

После запуска сервера откройте в браузере:

- **API документация (Swagger)**: http://localhost:8000/docs
- **Альтернативная документация (ReDoc)**: http://localhost:8000/redoc
- **Проверка здоровья**: http://localhost:8000/health
- **Корневой эндпоинт**: http://localhost:8000/

## Структура бэкенда

```
backend/
├── app/
│   ├── api/                 # API эндпоинты
│   │   └── v1/
│   │       ├── endpoints/   # Эндпоинты
│   │       │   ├── auth.py  # Регистрация и вход
│   │       │   └── users.py # Работа с пользователями
│   │       └── router.py    # Главный роутер
│   ├── core/                # Основные настройки
│   │   ├── config.py        # Конфигурация из .env
│   │   ├── database.py      # Подключение к БД (SQLAlchemy)
│   │   └── security.py      # JWT и хеширование паролей
│   ├── models/              # SQLAlchemy модели
│   │   └── user.py          # Модель пользователя
│   ├── schemas/             # Pydantic схемы для валидации
│   │   └── user.py          # Схемы пользователя
│   └── main.py              # Точка входа FastAPI
├── requirements.txt         # Зависимости Python
├── .env.example            # Пример файла окружения
└── .env                    # Файл окружения (создается вручную)
```

## Основные компоненты

### Модели данных (SQLAlchemy)

Модели находятся в `app/models/`. Они описывают структуру таблиц базы данных.

**User** (`app/models/user.py`):
- `id` - уникальный идентификатор
- `email` - email пользователя (уникальный)
- `hashed_password` - хешированный пароль
- `first_name`, `last_name` - имя и фамилия
- `bio` - описание профиля
- `avatar_url` - URL аватара
- `is_active` - активен ли пользователь
- `is_verified` - верифицирован ли email
- `latitude`, `longitude` - координаты (для PostGIS)
- `created_at`, `updated_at` - временные метки

### Схемы (Pydantic)

Схемы находятся в `app/schemas/`. Они используются для валидации входящих данных и сериализации ответов.

**Основные схемы:**
- `UserCreate` - данные для регистрации
- `UserLogin` - данные для входа
- `UserResponse` - данные пользователя в ответе
- `Token` - JWT токен

### Эндпоинты

**Авторизация** (`/api/v1/auth/`):
- `POST /register` - регистрация нового пользователя
- `POST /login` - вход в систему, получение JWT токена

**Пользователи** (`/api/v1/users/`):
- `GET /me` - информация о текущем пользователе (в разработке)

## Тестирование API

### Через Swagger UI (рекомендуется)

1. Откройте http://localhost:8000/docs
2. Используйте эндпоинты для регистрации и входа
3. После входа скопируйте `access_token` из ответа
4. Нажмите кнопку **"Authorize"** (🔒) в правом верхнем углу
5. Вставьте токен в поле "Value" (без слова "Bearer")
6. Нажмите "Authorize", затем "Close"
7. Теперь все защищенные эндпоинты будут работать

### Через curl

#### Регистрация пользователя

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "first_name": "Иван",
    "last_name": "Иванов"
  }'
```

#### Вход в систему

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Ответ будет содержать JWT токен:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Использование токена

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer <ваш_токен>"
```

## Устранение неполадок

### Ошибка подключения к базе данных

1. Убедитесь, что Docker Compose запущен: `docker-compose ps`
2. Проверьте настройки в `.env` (POSTGRES_HOST, POSTGRES_PORT)
3. Проверьте логи контейнера: `docker-compose logs postgres`

### Ошибка импорта модулей

1. Убедитесь, что виртуальное окружение активировано
2. Проверьте, что все зависимости установлены: `pip list`
3. Переустановите зависимости: `pip install -r requirements.txt`

### Ошибка "SECRET_KEY not set"

1. Убедитесь, что файл `.env` создан
2. Проверьте, что в `.env` указан `SECRET_KEY`
3. Перезапустите сервер

## Следующие шаги

- [ ] Добавить миграции базы данных через Alembic
- [ ] Реализовать получение JWT токена из заголовка Authorization
- [ ] Добавить эндпоинт для обновления профиля пользователя
- [ ] Реализовать загрузку и хранение фотографий
- [ ] Добавить логирование ошибок


