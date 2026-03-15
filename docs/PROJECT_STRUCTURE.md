# Структура проекта Резонанс

## Общая структура

```
Resonans/
├── backend/                    # Бэкенд приложение (Python/FastAPI)
│   ├── app/                    # Основной пакет приложения
│   │   ├── __init__.py
│   │   ├── main.py             # Точка входа FastAPI приложения
│   │   ├── api/                # API слой
│   │   │   ├── __init__.py
│   │   │   └── v1/             # API версии 1
│   │   │       ├── __init__.py
│   │   │       ├── router.py   # Главный роутер, объединяет все эндпоинты
│   │   │       └── endpoints/  # Эндпоинты по функциональности
│   │   │           ├── __init__.py
│   │   │           ├── auth.py # Эндпоинты авторизации (register, login)
│   │   │           └── users.py # Эндпоинты пользователей (me)
│   │   ├── core/               # Ядро приложения
│   │   │   ├── __init__.py
│   │   │   ├── config.py       # Настройки из переменных окружения
│   │   │   ├── database.py     # Подключение к БД (SQLAlchemy async)
│   │   │   └── security.py     # JWT токены и хеширование паролей
│   │   ├── models/             # SQLAlchemy модели
│   │   │   ├── __init__.py
│   │   │   └── user.py         # Модель пользователя
│   │   └── schemas/            # Pydantic схемы для валидации
│   │       ├── __init__.py
│   │       └── user.py         # Схемы пользователя (UserCreate, UserLogin, UserResponse, Token)
│   ├── requirements.txt        # Зависимости Python
│   ├── .env.example           # Пример файла окружения
│   ├── .env                   # Файл окружения (создается вручную, не в git)
│   ├── .gitignore            # Игнорируемые файлы
│   └── init_db.py            # Скрипт инициализации базы данных
│
├── frontend/                  # Фронтенд приложение (Flutter/Dart)
│   ├── lib/
│   │   └── main.dart         # Точка входа Flutter приложения
│   ├── android/              # Настройки Android
│   ├── ios/                  # Настройки iOS (для будущего использования)
│   ├── pubspec.yaml          # Зависимости и настройки Flutter проекта
│   └── .gitignore           # Игнорируемые файлы Flutter
│
├── docs/                     # Документация проекта
│   ├── API.md                # Документация API
│   ├── ARCHITECTURE.md       # Архитектура проекта
│   ├── BACKEND_SETUP.md      # Инструкция по настройке бэкенда
│   ├── FRONTEND_SETUP.md     # Инструкция по настройке фронтенда
│   └── PROJECT_STRUCTURE.md  # Этот файл
│
├── docker-compose.yml        # Docker Compose для PostgreSQL и Redis
└── README.md                 # Главный README проекта
```

## Детальное описание компонентов

### Backend (`backend/`)

#### `app/main.py`
Главный файл приложения FastAPI. Инициализирует приложение, настраивает CORS, подключает роутеры.

#### `app/core/config.py`
Класс `Settings` для загрузки настроек из переменных окружения через Pydantic Settings.

**Основные настройки:**
- Подключение к PostgreSQL
- Подключение к Redis
- JWT настройки (SECRET_KEY, время жизни токена)
- CORS настройки

#### `app/core/database.py`
Настройка подключения к базе данных через SQLAlchemy в асинхронном режиме.

**Основные компоненты:**
- `engine` - асинхронный движок SQLAlchemy
- `AsyncSessionLocal` - фабрика сессий
- `Base` - базовый класс для всех моделей
- `get_db()` - dependency для получения сессии БД
- `init_db()` - функция инициализации таблиц

#### `app/core/security.py`
Модуль безопасности для работы с паролями и JWT токенами.

**Функции:**
- `verify_password()` - проверка пароля
- `get_password_hash()` - хеширование пароля (bcrypt)
- `create_access_token()` - создание JWT токена
- `decode_access_token()` - декодирование и проверка JWT токена

#### `app/models/user.py`
SQLAlchemy модель пользователя. Описывает структуру таблицы `users` в базе данных.

**Поля модели:**
- `id` - уникальный идентификатор
- `email` - email (уникальный, индексированный)
- `hashed_password` - хешированный пароль
- `first_name`, `last_name` - имя и фамилия
- `bio` - описание профиля
- `avatar_url` - URL аватара
- `is_active` - активен ли пользователь
- `is_verified` - верифицирован ли email
- `latitude`, `longitude` - координаты (для PostGIS)
- `created_at`, `updated_at` - временные метки

#### `app/schemas/user.py`
Pydantic схемы для валидации данных пользователя.

**Схемы:**
- `UserBase` - базовая схема
- `UserCreate` - для регистрации (email, password, first_name, last_name)
- `UserLogin` - для входа (email, password)
- `UserResponse` - для ответа API (все поля кроме пароля)
- `Token` - для JWT токена (access_token, token_type)

#### `app/api/v1/endpoints/auth.py`
Эндпоинты авторизации.

**Эндпоинты:**
- `POST /api/v1/auth/register` - регистрация нового пользователя
- `POST /api/v1/auth/login` - вход в систему, получение JWT токена

#### `app/api/v1/endpoints/users.py`
Эндпоинты для работы с пользователями.

**Эндпоинты:**
- `GET /api/v1/users/me` - получение информации о текущем пользователе (требует JWT токен)

**Dependencies:**
- `get_current_user()` - dependency для получения текущего пользователя из JWT токена

#### `app/api/v1/router.py`
Главный роутер API версии 1. Объединяет все эндпоинты.

#### `init_db.py`
Скрипт для инициализации базы данных. Создает все таблицы.

**Использование:**
```bash
python init_db.py
```

### Frontend (`frontend/`)

#### `lib/main.dart`
Точка входа Flutter приложения. Содержит базовую структуру приложения.

**Текущее состояние:**
- Базовый экран с приветствием
- Настройка MaterialApp

**Будущее развитие:**
- Навигация между экранами
- Интеграция с API
- Управление состоянием
- Локальное хранилище для токенов

#### `pubspec.yaml`
Файл конфигурации Flutter проекта. Содержит зависимости и настройки.

**Основные зависимости:**
- `http` - HTTP клиент для работы с API
- `json_annotation` - аннотации для сериализации JSON
- `shared_preferences` - локальное хранилище
- `cupertino_icons` - иконки

### Docker Compose (`docker-compose.yml`)

Конфигурация для запуска PostgreSQL и Redis в Docker контейнерах.

**Сервисы:**
- `postgres` - PostgreSQL 14 с расширением PostGIS
- `redis` - Redis 7

**Volumes:**
- `postgres_data` - данные PostgreSQL
- `redis_data` - данные Redis

### Документация (`docs/`)

#### `README.md`
Главный README проекта с общим описанием и быстрым стартом.

#### `BACKEND_SETUP.md`
Подробная инструкция по настройке и запуску бэкенда.

#### `FRONTEND_SETUP.md`
Подробная инструкция по настройке и запуску фронтенда.

#### `ARCHITECTURE.md`
Описание архитектуры проекта, принципов проектирования, структуры БД.

#### `API.md`
Документация API с описанием всех эндпоинтов, примерами запросов и ответов.

#### `PROJECT_STRUCTURE.md`
Этот файл - описание структуры проекта.

## Принципы организации кода

### Backend

1. **Разделение слоев:**
   - API слой (`api/`) - обработка HTTP запросов
   - Бизнес-логика - в эндпоинтах и сервисах (будущее)
   - Слой данных (`models/`) - SQLAlchemy модели
   - Валидация (`schemas/`) - Pydantic схемы

2. **Типизация:**
   - Все функции имеют type hints
   - Pydantic схемы для валидации данных

3. **Асинхронность:**
   - Использование async/await для работы с БД
   - Асинхронный драйвер asyncpg для PostgreSQL

4. **Безопасность:**
   - Пароли хешируются через bcrypt
   - JWT токены для аутентификации
   - Секреты в переменных окружения

### Frontend

1. **Структура (планируемая):**
   - `screens/` - экраны приложения
   - `widgets/` - переиспользуемые виджеты
   - `services/` - сервисы для работы с API
   - `models/` - модели данных
   - `utils/` - утилиты

2. **Типизация:**
   - Строгая типизация в Dart
   - Модели для всех данных

3. **Разделение ответственности:**
   - UI отделен от бизнес-логики
   - Сервисы для работы с API

## Расширение структуры

### Будущие компоненты Backend

```
backend/app/
├── services/          # Бизнес-логика
│   ├── auth_service.py
│   └── user_service.py
├── utils/            # Утилиты
│   └── logger.py
└── migrations/       # Миграции Alembic
    └── versions/
```

### Будущие компоненты Frontend

```
frontend/lib/
├── screens/
│   ├── auth/
│   │   ├── login_screen.dart
│   │   └── register_screen.dart
│   └── home_screen.dart
├── widgets/
│   └── common/
├── services/
│   ├── api_service.dart
│   └── auth_service.dart
├── models/
│   └── user.dart
└── utils/
    └── storage.dart
```

## Именование файлов и папок

- **Python файлы**: snake_case (например, `user_service.py`)
- **Dart файлы**: snake_case (например, `login_screen.dart`)
- **Классы**: PascalCase (например, `UserService`, `LoginScreen`)
- **Функции и переменные**: snake_case в Python, camelCase в Dart
- **Константы**: UPPER_SNAKE_CASE


