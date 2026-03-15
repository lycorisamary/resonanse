# Настройка MinIO для хранения файлов

## Что такое MinIO?

MinIO - это S3-совместимое объектное хранилище с открытым исходным кодом. Используется для хранения файлов (аватаров, фотографий) в приложении.

## Быстрый старт

### 1. Запуск MinIO через Docker Compose

MinIO уже настроен в `docker-compose.yml`. Для запуска:

```bash
# Запуск всех сервисов (включая MinIO)
docker-compose up -d

# Или только MinIO
docker-compose up -d minio
```

### 2. Проверка работы MinIO

Проверьте, что MinIO запущен:

```bash
docker-compose ps
```

Должен быть запущен контейнер `resonans_minio`.

### 3. Доступ к MinIO Console

1. Откройте браузер: http://localhost:9001
2. Войдите с учетными данными по умолчанию:
   - **Username:** `minioadmin`
   - **Password:** `minioadmin`

**ВАЖНО:** В продакшене обязательно измените эти пароли!

### 4. Создание Bucket

Bucket `resonans-avatars` будет создан автоматически при первом использовании.

Или создайте вручную через Console:
1. Войдите в MinIO Console
2. Нажмите "Create Bucket"
3. Имя: `resonans-avatars`
4. Нажмите "Create Bucket"

### 5. Настройка доступа (опционально)

Для публичного доступа к файлам:

1. В MinIO Console выберите bucket `resonans-avatars`
2. Перейдите в "Access Policy"
3. Выберите "Public" (или настройте CORS для конкретных доменов)

## Настройка в .env

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

## Использование в коде

Сервис `StorageService` автоматически использует эти настройки:

```python
from app.services.storage import storage_service

# Загрузка файла
object_name = await storage_service.upload_file(
    file_content=file_bytes,
    file_extension="jpg",
    folder="avatars"
)

# Получение URL
url = storage_service.get_public_url(object_name)
```

## Тестирование подключения

### Через Python

```python
from app.services.storage import storage_service

# Проверка подключения
print(f"Bucket: {storage_service.bucket_name}")
print(f"Endpoint: {storage_service.client._base_url}")
```

### Через curl

```bash
# Проверка здоровья MinIO
curl http://localhost:9000/minio/health/live

# Должен вернуть: OK
```

## Миграция на AWS S3 (продакшен)

Для продакшена замените настройки в `.env`:

```env
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY=<your-aws-access-key>
S3_SECRET_KEY=<your-aws-secret-key>
S3_BUCKET_NAME=resonans-avatars-prod
S3_REGION=us-east-1
S3_USE_SSL=True
```

Код останется без изменений благодаря абстракции `StorageService`.

## Устранение неполадок

### MinIO не запускается

```bash
# Проверьте логи
docker-compose logs minio

# Пересоздайте контейнер
docker-compose down minio
docker-compose up -d minio
```

### Ошибка подключения из приложения

1. Проверьте, что MinIO запущен: `docker-compose ps`
2. Проверьте настройки в `.env`
3. Проверьте доступность: `curl http://localhost:9000/minio/health/live`

### Ошибка доступа к bucket

1. Убедитесь, что bucket существует в MinIO Console
2. Проверьте права доступа (Access Policy)
3. Проверьте правильность `S3_ACCESS_KEY` и `S3_SECRET_KEY`

## Безопасность

### Для разработки

- Используйте значения по умолчанию (minioadmin/minioadmin)
- Доступ только с localhost

### Для продакшена

1. **Измените пароли:**
   ```bash
   docker-compose down
   # Измените MINIO_ROOT_USER и MINIO_ROOT_PASSWORD в docker-compose.yml
   docker-compose up -d
   ```

2. **Используйте HTTPS:**
   - Настройте SSL сертификат
   - Установите `S3_USE_SSL=True`

3. **Ограничьте доступ:**
   - Настройте CORS в MinIO Console
   - Используйте IAM политики для bucket

4. **Резервное копирование:**
   - Настройте автоматическое копирование данных
   - Используйте версионирование объектов

## Дополнительные ресурсы

- [Документация MinIO](https://min.io/docs/)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/API.html)
- [S3 API совместимость](https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html)

