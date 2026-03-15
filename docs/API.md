# API Документация

## Базовый URL

```
http://localhost:8000/api/v1
```

## Аутентификация

Большинство эндпоинтов требуют аутентификации через JWT токен. Токен должен передаваться в заголовке `Authorization`:

```
Authorization: Bearer <your_jwt_token>
```

### Использование в Swagger UI

1. Откройте http://localhost:8000/docs
2. Нажмите кнопку **"Authorize"** (🔒) в правом верхнем углу
3. В поле "Value" введите ваш JWT токен (без слова "Bearer")
4. Нажмите **"Authorize"**, затем **"Close"**
5. Теперь все защищенные эндпоинты будут использовать этот токен автоматически

**Примечание:** Если вы получаете ошибку 422 в Swagger, убедитесь, что:
- Токен введен без префикса "Bearer"
- Токен не истек
- Токен получен через эндпоинт `/auth/login`

## Эндпоинты

### Авторизация

#### Регистрация пользователя

**POST** `/auth/register`

Создает нового пользователя в системе.

**Тело запроса:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "Иван",
  "last_name": "Иванов"
}
```

**Параметры:**
- `email` (string, required) - Email пользователя (должен быть уникальным)
- `password` (string, required) - Пароль (минимум 8 символов)
- `first_name` (string, optional) - Имя пользователя
- `last_name` (string, optional) - Фамилия пользователя

**Успешный ответ (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "bio": null,
  "avatar_url": null,
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Ошибки:**
- `400 Bad Request` - Пользователь с таким email уже существует
- `422 Unprocessable Entity` - Ошибка валидации данных

**Пример запроса (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "Иван",
    "last_name": "Иванов"
  }'
```

---

#### Вход в систему

**POST** `/auth/login`

Аутентифицирует пользователя и возвращает JWT токен.

**Тело запроса:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Параметры:**
- `email` (string, required) - Email пользователя
- `password` (string, required) - Пароль пользователя

**Успешный ответ (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Ошибки:**
- `401 Unauthorized` - Неверный email или пароль
- `403 Forbidden` - Пользователь деактивирован
- `422 Unprocessable Entity` - Ошибка валидации данных

**Пример запроса (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

---

### Пользователи

#### Получение информации о текущем пользователе

**GET** `/users/me`

Возвращает информацию о текущем аутентифицированном пользователе.

**Заголовки:**
- `Authorization: Bearer <token>` (required)

**Успешный ответ (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "bio": null,
  "avatar_url": null,
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Ошибки:**
- `401 Unauthorized` - Токен отсутствует или невалидный
- `403 Forbidden` - Пользователь деактивирован
- `404 Not Found` - Пользователь не найден

**Пример запроса (curl):**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Коды статусов HTTP

- `200 OK` - Успешный запрос
- `201 Created` - Ресурс успешно создан
- `400 Bad Request` - Неверный запрос
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Доступ запрещен
- `404 Not Found` - Ресурс не найден
- `422 Unprocessable Entity` - Ошибка валидации данных
- `500 Internal Server Error` - Внутренняя ошибка сервера

## Формат ошибок

При возникновении ошибки API возвращает JSON объект с описанием:

```json
{
  "detail": "Описание ошибки"
}
```

## JWT Токены

JWT токены содержат следующую информацию:
- `sub` - ID пользователя
- `exp` - Время истечения токена (Unix timestamp)

Токены действительны в течение времени, указанного в `ACCESS_TOKEN_EXPIRE_MINUTES` (по умолчанию 7 дней).

## Эндпоинты городов

### Получение списка городов

**GET** `/cities/cities`

Возвращает список крупных городов России для выбора в профиле.

**Ответ (200):**
```json
[
  "Москва",
  "Санкт-Петербург",
  "Новосибирск",
  ...
]
```

## Эндпоинты админ-панели

Все эндпоинты админ-панели требуют прав администратора (email должен совпадать с `ADMIN_EMAIL` из настроек).

### Получение списка пользователей

**GET** `/admin/users`

**Параметры:**
- `skip` (int, optional) - для пагинации
- `limit` (int, optional) - максимальное количество (по умолчанию 100)

### Получение пользователя по ID

**GET** `/admin/users/{user_id}`

### Обновление пользователя

**PATCH** `/admin/users/{user_id}`

### Активация пользователя

**POST** `/admin/users/{user_id}/activate`

### Деактивация пользователя

**POST** `/admin/users/{user_id}/deactivate`

### Удаление пользователя

**DELETE** `/admin/users/{user_id}`

Подробнее: [Документация админ-панели](ADMIN_PANEL.md)

## Интерактивная документация

API предоставляет интерактивную документацию через Swagger UI:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

В документации можно:
- Просмотреть все эндпоинты
- Увидеть схемы запросов и ответов
- Протестировать API прямо в браузере
- Использовать кнопку "Authorize" для работы с защищенными эндпоинтами


