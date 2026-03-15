# Управление профилем пользователя

## Обзор

Реализован функционал управления профилем пользователя:
- Загрузка аватара
- Обновление данных профиля
- Подготовка к гео-поиску

## Изменения в модели User

### Добавленные/обновленные поля:

1. **birthdate** (Date, nullable) - Дата рождения пользователя
2. **city** (String, nullable) - Город проживания
3. **latitude** (Float, nullable) - Широта (-90 до 90)
4. **longitude** (Float, nullable) - Долгота (-180 до 180)
5. **is_admin** (Boolean) - Флаг администратора

**Примечание:** Поля `avatar_url` и `bio` уже существовали в модели.

## Миграция базы данных

### Применение миграции

```bash
# Подключение к PostgreSQL
docker exec -it resonans_postgres psql -U resonans_user -d resonans_db

# Выполнение миграции
\i /path/to/migrations/001_add_profile_fields.sql
```

Или через файл:

```bash
type migrations\001_add_profile_fields.sql | docker exec -i resonans_postgres psql -U resonans_user -d resonans_db

type migrations\004_swipes_matches.sql | docker exec -i resonans_postgres psql -U resonans_user -d resonans_db


//
docker exec -i resonans_postgres psql -U resonans_user -d resonans_db < backend/migrations/001_add_profile_fields.sql
```


### Миграция 001 (уже применена):

1. Добавляет колонку `birthdate` типа DATE
2. Удаляет старые колонки `latitude` и `longitude` (String)
3. Создает новые колонки `latitude` и `longitude` типа FLOAT
4. Создает индекс для геолокации

### Миграция 002 (новая):

```bash
type migrations\002_add_city_and_admin.sql | docker exec -i resonans_postgres psql -U resonans_user -d resonans_db
```

**Что делает:**
1. Добавляет колонку `city` типа VARCHAR(100)
2. Добавляет колонку `is_admin` типа BOOLEAN (по умолчанию FALSE)
3. Создает индекс для поиска по городу

## Настройка MinIO

### Запуск MinIO

MinIO уже добавлен в `docker-compose.yml`. Для запуска:

```bash
docker-compose up -d minio
```

### Доступ к MinIO Console

1. Откройте браузер: http://localhost:9001
2. Войдите с учетными данными:
   - Username: `minioadmin`
   - Password: `minioadmin`

### Настройка bucket

1. В MinIO Console создайте bucket `resonans-avatars`
2. Или bucket будет создан автоматически при первом использовании

### Настройка .env

Добавьте в `backend/.env`:

```env
# Настройки S3/MinIO для хранения файлов
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=resonans-avatars
S3_REGION=us-east-1
S3_USE_SSL=False

# Настройки загрузки файлов
MAX_FILE_SIZE_MB=5
ALLOWED_IMAGE_EXTENSIONS=["jpg","jpeg","png","webp"]
```

## API Эндпоинты

### 1. Получение профиля

**GET** `/api/v1/users/me`

**Заголовки:**
```
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "bio": "О себе...",
  "avatar_url": "http://localhost:9000/resonans-avatars/avatars/uuid.jpg",
  "birthdate": "1990-01-01",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### 2. Обновление профиля

**PATCH** `/api/v1/users/me`

**Заголовки:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "first_name": "Иван",
  "last_name": "Иванов",
  "bio": "Новое описание",
  "birthdate": "1990-01-01",
  "city": "Москва",
  "latitude": 55.7558,
  "longitude": 37.6173
}
```

**Валидация:**
- `latitude`: от -90 до 90
- `longitude`: от -180 до 180
- `birthdate`: не может быть в будущем
- `city`: строка до 100 символов

### 3. Смена пароля

**POST** `/api/v1/users/change-password`

**Заголовки:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "old_password": "текущий_пароль",
  "new_password": "новый_пароль"
}
```

**Валидация:**
- `old_password` - обязательное поле
- `new_password` - обязательное поле, минимум 8 символов
- Новый пароль должен отличаться от старого

### 4. Загрузка аватара

### 5. Получение списка городов

**GET** `/api/v1/cities/cities`

Возвращает список доступных городов для выбора в профиле.

**Ответ:**
```json
[
  "Москва",
  "Санкт-Петербург",
  "Новосибирск",
  ...
]
```

**POST** `/api/v1/users/upload-avatar`

**Заголовки:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Тело запроса:**
- `file`: файл изображения (JPG, JPEG, PNG, WEBP)
- Максимальный размер: 5 МБ

**Ограничения:**
- Форматы: JPG, JPEG, PNG, WEBP
- Максимальный размер: 5 МБ (настраивается в `MAX_FILE_SIZE_MB`)

**Ответ:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "avatar_url": "http://localhost:9000/resonans-avatars/avatars/uuid.jpg",
  ...
}
```

## Flutter приложение

### Установка зависимостей

```bash
cd frontend
flutter pub get
```

### Структура файлов

```
frontend/lib/
├── config/
│   └── api_config.dart      # Конфигурация API
├── models/
│   └── user.dart            # Модели User и UserUpdate
├── services/
│   └── api_service.dart     # Сервис для работы с API
└── screens/
    └── profile_screen.dart  # Экран профиля
```

### Использование

```dart
import 'package:resonans/screens/profile_screen.dart';

// В навигации
Navigator.push(
  context,
  MaterialPageRoute(builder: (context) => const ProfileScreen()),
);
```

### Настройка API URL

В `lib/config/api_config.dart` измените `baseUrl`:

- Для Android эмулятора: `http://10.0.2.2:8000`
- Для физического устройства: `http://<IP_вашего_компьютера>:8000`

## Тестирование

### Тест загрузки аватара (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/users/upload-avatar" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/image.jpg"
```

### Тест обновления профиля (curl)

```bash
curl -X PATCH "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Иван",
    "bio": "Новое описание",
    "birthdate": "1990-01-01"
  }'
```

### Тест геолокации и поиска рядом (curl)

Установка геолокации пользователя:

```bash
curl -X POST "http://localhost:8000/api/v1/users/location" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 55.7558,
    "longitude": 37.6173
  }'
```

Поиск пользователей рядом:

```bash
curl -X GET "http://localhost:8000/api/v1/users/nearby?radius_km=10" \
  -H "Authorization: Bearer <token>"
```

## Устранение неполадок

### Ошибка подключения к MinIO

1. Проверьте, что MinIO запущен: `docker-compose ps`
2. Проверьте настройки в `.env`
3. Проверьте доступность: `curl http://localhost:9000/minio/health/live`

### Ошибка загрузки файла

1. Проверьте размер файла (максимум 5 МБ)
2. Проверьте формат файла (JPG, PNG, WEBP)
3. Проверьте права доступа к bucket в MinIO

### Ошибка валидации координат

- Широта должна быть от -90 до 90
- Долгота должна быть от -180 до 180

## Исправления

### Отображение аватарок

- ✅ Добавлен пакет `cached_network_image` для кэширования изображений
- ✅ Используется `CachedNetworkImage` вместо `NetworkImage`
- ✅ Добавлена обработка ошибок загрузки
- ✅ Добавлен placeholder во время загрузки

### Выбор города

- ✅ Добавлено поле `city` в модель User
- ✅ Создан API эндпоинт для получения списка городов
- ✅ Добавлен DropdownButton для выбора города в профиле
- ✅ Список из 50 крупных городов России

## Следующие шаги

- [ ] Добавить возможность удаления аватара
- [ ] Реализовать гео-поиск на основе координат
- [ ] Добавить валидацию возраста (18+)
- [ ] Добавить больше городов или интеграцию с API геокодирования

