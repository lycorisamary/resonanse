# Резонанс - Мобильное приложение для знакомств

Платформа для поиска друзей и единомышленников на основе глубинных интересов.

## Технический стек

- **Бэкенд**: Python 3.10+, FastAPI (асинхронный режим)
- **База данных**: PostgreSQL 14 с расширением PostGIS
- **Кэш**: Redis
- **Фронтенд**: Flutter (Dart), приоритет Android для MVP
- **Инфраструктура**: Docker Compose (только для БД и Redis)

## Структура проекта

```
Resonans/
├── backend/                 # Бэкенд приложение
│   ├── app/
│   │   ├── api/            # API эндпоинты
│   │   │   └── v1/
│   │   │       ├── endpoints/  # Эндпоинты (auth, users)
│   │   │       └── router.py   # Главный роутер
│   │   ├── core/           # Основные настройки
│   │   │   ├── config.py   # Конфигурация приложения
│   │   │   ├── database.py # Подключение к БД
│   │   │   └── security.py # Безопасность (JWT, пароли)
│   │   ├── models/         # SQLAlchemy модели
│   │   │   └── user.py     # Модель пользователя
│   │   ├── schemas/        # Pydantic схемы
│   │   │   └── user.py     # Схемы пользователя
│   │   └── main.py         # Точка входа приложения
│   ├── requirements.txt    # Зависимости Python
│   └── .env.example        # Пример файла окружения
├── frontend/               # Flutter приложение
│   ├── lib/
│   │   └── main.dart       # Точка входа Flutter
│   └── pubspec.yaml        # Зависимости Flutter
├── docker-compose.yml      # Docker Compose для БД и Redis
└── README.md               # Этот файл
```

## Быстрый старт

### 1. Настройка базы данных и Redis

Запустите PostgreSQL и Redis через Docker Compose:

```bash
docker-compose up -d
```

### 2. Настройка бэкенда

1. Перейдите в папку бэкенда:
```bash
cd backend
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Создайте файл `.env` на основе `.env.example`:
```bash
copy .env.example .env  # Windows
# или
cp .env.example .env    # Linux/Mac
```

6. Отредактируйте `.env` и укажите свои настройки:
   - `SECRET_KEY` - обязательно сгенерируйте свой ключ
   - `ADMIN_EMAIL` - email администратора (для доступа к админ-панели)
   - Настройки MinIO (если используете)

7. Инициализируйте базу данных:
```bash
# Создание таблиц
python init_db.py

# Применение миграций
# Миграция 001 (добавление полей профиля)
type migrations\001_add_profile_fields.sql | docker exec -i resonans_postgres psql -U resonans_user -d resonans_db

# Миграция 002 (добавление города и админа)
type migrations\002_add_city_and_admin.sql | docker exec -i resonans_postgres psql -U resonans_user -d resonans_db
```

8. Запустите сервер:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: http://localhost:8000
Документация API: http://localhost:8000/docs

### 3. Настройка фронтенда

1. Убедитесь, что у вас установлен Flutter SDK
2. Перейдите в папку фронтенда:
```bash
cd frontend
```

3. Установите зависимости:
```bash
flutter pub get
```

4. Запустите приложение:
```bash
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

### Города

- `GET /api/v1/cities/cities` - Получение списка доступных городов

### Админ-панель

- `GET /api/v1/admin/users` - Получение списка всех пользователей
- `GET /api/v1/admin/users/{user_id}` - Получение пользователя по ID
- `PATCH /api/v1/admin/users/{user_id}` - Обновление пользователя
- `POST /api/v1/admin/users/{user_id}/activate` - Активация пользователя
- `POST /api/v1/admin/users/{user_id}/deactivate` - Деактивация пользователя
- `DELETE /api/v1/admin/users/{user_id}` - Удаление пользователя

## Flutter приложение

Приложение имеет полноценный UI для:
- ✅ Регистрации и входа
- ✅ Просмотра и редактирования профиля
- ✅ Загрузки аватара
- ✅ Админ-панели
- ✅ Ленты кандидатов и свайпов (Feed)

Подробнее: [Документация Flutter UI](docs/FLUTTER_UI.md)

## Текущий этап разработки

**Неделя 3**: Геолокация, лента кандидатов и свайпы.

### Реализованный функционал

✅ **Авторизация и регистрация**
- Регистрация новых пользователей
- Вход в систему с JWT токенами
- Автоматическое сохранение токена

✅ **Управление профилем**
- Просмотр и редактирование профиля
- Загрузка аватара (галерея/камера)
- Выбор города проживания
- Смена пароля
- Обновление данных (имя, фамилия, био, дата рождения)

✅ **Админ-панель**
- Просмотр всех пользователей
- Управление пользователями (активация/деактивация, удаление)
- Поиск пользователей
- Доступ только для администратора (настраивается через ADMIN_EMAIL)

✅ **Геолокация и свайпы**
- Хранение геопозиции пользователя в PostGIS (`GEOGRAPHY(POINT, 4326)`)
- Поиск пользователей поблизости через `/users/nearby`
- Лента кандидатов `/feed` с кэшем в Redis
- Свайпы `/swipes` с атомарным UPSERT и таблицей `swipes`
- Создание матчей в таблице `matches` при взаимном лайке

## Дополнительная документация

- [Инструкция по запуску бэкенда](docs/BACKEND_SETUP.md) - настройка и запуск FastAPI
- [Инструкция по запуску фронтенда](docs/FRONTEND_SETUP.md) - настройка и запуск Flutter
- [Документация API](docs/API.md) - описание всех эндпоинтов
- [Архитектура проекта](docs/ARCHITECTURE.md) - структура и принципы разработки
- [Управление профилем](docs/PROFILE_MANAGEMENT.md) - работа с профилем и файлами
- [Настройка MinIO](docs/SETUP_MINIO.md) - настройка хранилища файлов
- [Flutter UI руководство](docs/FLUTTER_UI.md) - описание экранов приложения

