# Документация: Система чата и уведомлений Resonans

## 1. Исследование и архитектура

### 1.1. Общие требования
- Чат создается автоматически при взаимном свайпе (матче)
- Поддержка текстовых сообщений в реальном времени через WebSocket
- Системные сообщения для будущих AI-агентов и уведомлений
- Уведомления о новых матчах и сообщениях
- Статус прочтения сообщений
- Мягкое удаление сообщений (soft delete)

### 1.2. Структура базы данных

#### Таблица `conversations`
Хранит информацию о чатах между пользователями:
- `id`: уникальный идентификатор
- `user_id_1`, `user_id_2`: участники чата (уникальная пара)
- `created_at`: дата создания
- `updated_at`: дата последнего обновления
- `last_message_at`: время последнего сообщения (для сортировки)
- `is_active`: статус чата (активен/заблокирован)

**Ограничения:**
- Уникальность пары пользователей (независимо от порядка)
- Проверка: `user_id_1 != user_id_2`

#### Таблица `messages`
Хранит сообщения внутри чатов:
- `id`: уникальный идентификатор
- `conversation_id`: ссылка на чат
- `sender_id`: отправитель сообщения
- `content`: текст сообщения (до 5000 символов)
- `message_type`: тип сообщения (`text`, `image`, `system`)
- `is_read`: статус прочтения
- `created_at`, `updated_at`: временные метки
- `deleted_at`: дата удаления (NULL = не удалено)

**Типы сообщений:**
- `text`: обычные пользовательские сообщения
- `image`: изображения (будущая функциональность)
- `system`: системные сообщения (AI-агент, уведомления о матче)

#### Триггеры
1. **update_conversation_updated_at**: обновляет `updated_at` при изменении чата
2. **update_conversation_last_message**: обновляет `last_message_at` при новом сообщении

### 1.3. API Endpoints

#### REST API

| Метод | Endpoint | Описание | Доступ |
|-------|----------|----------|--------|
| GET | `/api/v1/conversations` | Список чатов пользователя | Auth |
| GET | `/api/v1/conversations/{id}` | Детали конкретного чата | Auth |
| GET | `/api/v1/conversations/{id}/messages` | История сообщений | Auth |
| POST | `/api/v1/conversations/{id}/messages` | Отправить сообщение | Auth |
| POST | `/api/v1/conversations/{id}/system-messages` | Системное сообщение | Admin only |
| DELETE | `/api/v1/messages/{id}` | Удалить сообщение | Sender/Admin |
| WebSocket | `/ws/conversations/{id}` | Real-time обмен сообщениями | Auth |

#### WebSocket Protocol

**Подключение:**
```
GET /ws/conversations/{conversation_id}
Headers: Authorization: Bearer {token}
```

**Формат сообщений (Client → Server):**
```json
{
  "content": "Привет!"
}
```

**Формат сообщений (Server → Client):**
```json
{
  "id": 123,
  "sender_id": 456,
  "content": "Привет!",
  "message_type": "text",
  "created_at": "2026-03-30T23:00:00Z"
}
```

### 1.4. Автоматическое создание чата при матче

При взаимном лайке в endpoint `/api/v1/swipes`:
1. Создается запись в таблице `matches`
2. В фоновой задаче (`BackgroundTasks`) создается `conversation`
3. Отправляется системное сообщение о матче (будущая функция)

---

## 2. Локальное тестирование

### 2.1. Подготовка окружения

```powershell
# 1. Применить миграцию
cd backend
.\venv\Scripts\Activate.ps1
python init_db.py  # или alembic upgrade head

# 2. Запустить сервер
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2.2. Сценарий тестирования чата

#### Шаг 1: Регистрация двух пользователей

**Пользователь 1 (Браузер/Postman):**
```bash
POST http://127.0.0.1:8000/api/v1/auth/register
Content-Type: application/json

{
  "email": "user1@test.com",
  "password": "password123",
  "first_name": "User",
  "last_name": "One"
}
```

**Пользователь 2 (Инкогнито/другой клиент):**
```bash
POST http://127.0.0.1:8000/api/v1/auth/register
Content-Type: application/json

{
  "email": "user2@test.com",
  "password": "password123",
  "first_name": "User",
  "last_name": "Two"
}
```

#### Шаг 2: Логин и получение токенов

**Пользователь 1:**
```bash
POST http://127.0.0.1:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "user1@test.com",
  "password": "password123"
}
```
Сохраните `access_token` как `TOKEN1`.

**Пользователь 2:**
```bash
POST http://127.0.0.1:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "user2@test.com",
  "password": "password123"
}
```
Сохраните `access_token` как `TOKEN2`.

#### Шаг 3: Установка геолокации (опционально, для фида)

```bash
POST http://127.0.0.1:8000/api/v1/users/location
Authorization: Bearer {TOKEN1}
Content-Type: application/json

{
  "latitude": 55.7558,
  "longitude": 37.6173
}
```

#### Шаг 4: Взаимный свайп (создание матча)

**Пользователь 1 свайпает Пользователя 2:**
```bash
POST http://127.0.0.1:8000/api/v1/swipes
Authorization: Bearer {TOKEN1}
Content-Type: application/json

{
  "target_user_id": 2,
  "decision": true
}
```

**Пользователь 2 свайпает Пользователя 1:**
```bash
POST http://127.0.0.1:8000/api/v1/swipes
Authorization: Bearer {TOKEN2}
Content-Type: application/json

{
  "target_user_id": 1,
  "decision": true
}
```

В ответе должно быть: `{"is_match": true}`

#### Шаг 5: Проверка создания чата

**Пользователь 1 проверяет список чатов:**
```bash
GET http://127.0.0.1:8000/api/v1/conversations
Authorization: Bearer {TOKEN1}
```

Должен вернуться список с одним чатом:
```json
[
  {
    "id": 1,
    "user_id_1": 1,
    "user_id_2": 2,
    "created_at": "2026-03-30T23:00:00Z",
    "last_message_at": null,
    "is_active": true
  }
]
```

#### Шаг 6: Отправка сообщений (REST)

**Пользователь 1 отправляет сообщение:**
```bash
POST http://127.0.0.1:8000/api/v1/conversations/1/messages
Authorization: Bearer {TOKEN1}
Content-Type: application/json

{
  "content": "Привет! Как дела?"
}
```

**Пользователь 2 получает историю сообщений:**
```bash
GET http://127.0.0.1:8000/api/v1/conversations/1/messages
Authorization: Bearer {TOKEN2}
```

#### Шаг 7: Тестирование WebSocket (real-time)

**Подключение через Python:**
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/conversations/1"
    headers = {"Authorization": "Bearer TOKEN1"}
    
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # Отправка сообщения
        await websocket.send(json.dumps({"content": "Привет из WebSocket!"}))
        
        # Получение подтверждения
        response = await websocket.recv()
        print(f"Получено: {response}")

asyncio.run(test_websocket())
```

**Или через JavaScript (браузер):**
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws/conversations/1');

ws.onopen = () => {
  console.log('Connected to chat');
  ws.send(JSON.stringify({ content: 'Привет!' }));
};

ws.onmessage = (event) => {
  console.log('Message received:', event.data);
};
```

#### Шаг 8: Системные сообщения (только админ)

**Назначение пользователя администратором (через БД):**
```sql
UPDATE users SET is_admin = TRUE WHERE email = 'user1@test.com';
```

**Отправка системного сообщения:**
```bash
POST http://127.0.0.1:8000/api/v1/conversations/1/system-messages
Authorization: Bearer {TOKEN1}
Content-Type: application/json

{
  "content": "🎉 Поздравляем с матчем! Это системное сообщение от AI-агента."
}
```

#### Шаг 9: Удаление сообщения

```bash
DELETE http://127.0.0.1:8000/api/v1/messages/1
Authorization: Bearer {TOKEN1}
```

---

## 3. Уведомления

### 3.1. Типы уведомлений

1. **Уведомление о матче** (`match`):
   - Отправляется обоим пользователям при взаимном лайке
   - Содержит информацию о созданном чате
   - Может включать краткую информацию о пользователе

2. **Уведомление о новом сообщении** (`new_message`):
   - Отправляется получателю сообщения в реальном времени
   - Через WebSocket или Push-уведомления (в будущем)

3. **Системные уведомления** (`system`):
   - Вопросы от AI-агента
   - Напоминания
   - Важные обновления

### 3.2. Формат уведомления (WebSocket)

```json
{
  "type": "new_message",
  "conversation_id": 1,
  "message": {
    "id": 123,
    "sender_id": 456,
    "content": "Привет!",
    "message_type": "text",
    "created_at": "2026-03-30T23:00:00Z"
  },
  "timestamp": "2026-03-30T23:00:00Z"
}
```

### 3.3. Будущие улучшения

- **Push-уведомления**: Интеграция с Firebase Cloud Messaging (FCM) для мобильных устройств
- **Email-уведомления**: Для неактивных пользователей
- **AI-агент**: Автоматические вопросы для улучшения匹配 качества
- **Голосовые сообщения**: Расширение типа `message_type`
- **Реакции на сообщения**: Эмодзи-реакции

---

## 4. Безопасность

### 4.1. Авторизация
- Все endpoints требуют JWT-токен
- WebSocket проверяет токен при подключении
- Пользователь может получить доступ только к своим чатам

### 4.2. Ограничения
- Только отправитель или админ может удалять сообщения
- Системные сообщения доступны только администраторам
- Мягкое удаление позволяет восстановить сообщения (при необходимости)

### 4.3. Валидация
- Длина сообщения: 1-5000 символов
- Проверка существования чата и прав доступа
- rate limiting (рекомендуется добавить в production)

---

## 5. Производительность

### 5.1. Индексы базы данных
- `idx_conversations_user_id_1`, `idx_conversations_user_id_2`: быстрый поиск чатов
- `idx_conversations_last_message`: сортировка по последнему сообщению
- `idx_messages_conversation_id`: быстрый доступ к сообщениям чата
- `idx_messages_unread`: фильтр непрочитанных сообщений

### 5.2. Кэширование
- Redis для хранения активных WebSocket-соединений (будущая функция)
- Connection manager для групповой рассылки в чате

### 5.3. Масштабирование
- Фоновые задачи для создания чатов (не блокируют основной поток)
- Асинхронная обработка WebSocket сообщений
- Возможность шардирования по `conversation_id`

---

## 6. Примеры кода

### 6.1. Python клиент для тестирования

```python
import requests
import websockets
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000"

def login(email: str, password: str) -> str:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    return response.json()["access_token"]

def send_message(token: str, conversation_id: int, content: str):
    response = requests.post(
        f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": content}
    )
    return response.json()

async def websocket_chat(token: str, conversation_id: int):
    uri = f"ws://{BASE_URL}/ws/conversations/{conversation_id}"
    async with websockets.connect(uri, extra_headers={"Authorization": f"Bearer {token}"}) as ws:
        await ws.send(json.dumps({"content": "Hello from WebSocket!"}))
        response = await ws.recv()
        print(f"Received: {response}")

# Использование
token1 = login("user1@test.com", "password123")
message = send_message(token1, 1, "Привет!")
print(message)

asyncio.run(websocket_chat(token1, 1))
```

---

## 7. Чек-лист перед запуском в production

- [ ] Применены все миграции
- [ ] Настроен rate limiting для API
- [ ] Включен HTTPS для WebSocket (wss://)
- [ ] Настроено логирование ошибок
- [ ] Добавлен monitoring для активных соединений
- [ ] Протестирована нагрузка (например, через locust)
- [ ] Настроены backup для базы данных
- [ ] Реализована обработка отключений WebSocket
- [ ] Добавлены unit-тесты для chat endpoints
- [ ] Проведен security audit

---

## 8. Заключение

Система чата и уведомлений готова к использованию. Основные функции:
- ✅ Автоматическое создание чата при матче
- ✅ Текстовые сообщения (REST + WebSocket)
- ✅ Системные сообщения для AI-агента
- ✅ Статус прочтения
- ✅ Мягкое удаление
- ✅ Уведомления о событиях

Следующие шаги:
1. Интеграция AI-агента для автоматических вопросов
2. Push-уведомления для мобильных устройств
3. Поддержка изображений и голосовых сообщений
4. Расширенная аналитика чатов
