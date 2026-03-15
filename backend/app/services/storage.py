"""
Сервис для работы с хранилищем файлов (S3/MinIO).
Абстракция для работы с S3-совместимыми хранилищами.
"""
import uuid
from datetime import timedelta
from io import BytesIO
from minio import Minio
from minio.error import S3Error

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """
    Сервис для работы с S3/MinIO хранилищем.
    
    Поддерживает:
    - Загрузку файлов
    - Генерацию публичных URL
    - Удаление файлов
    """
    
    def __init__(self):
        """Инициализация клиента MinIO/S3."""
        self.client = Minio(
            endpoint=settings.S3_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_USE_SSL,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Создает bucket, если он не существует."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket {self.bucket_name} создан")
        except S3Error as e:
            logger.error(f"Ошибка при создании bucket: {e}")
            raise
    
    async def upload_file(
        self,
        file_content: bytes,
        file_extension: str,
        folder: str = "avatars"
    ) -> str:
        """
        Загружает файл в хранилище.
        
        Args:
            file_content: Содержимое файла в байтах
            file_extension: Расширение файла (без точки)
            folder: Папка для загрузки
            
        Returns:
            Путь к файлу в хранилище (object_key)
            
        Raises:
            ValueError: Если размер файла превышает лимит
            S3Error: При ошибке загрузки
        """
        # Проверка размера файла
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"Размер файла ({file_size_mb:.2f} МБ) превышает максимальный "
                f"лимит ({settings.MAX_FILE_SIZE_MB} МБ)"
            )
        
        # Проверка расширения
        if file_extension.lower() not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Расширение .{file_extension} не разрешено. "
                f"Разрешенные: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
            )
        
        # Генерация уникального имени файла
        file_id = str(uuid.uuid4())
        object_name = f"{folder}/{file_id}.{file_extension.lower()}"
        
        # Загрузка файла
        try:
            file_obj = BytesIO(file_content)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_obj,
                length=len(file_content),
                content_type=f"image/{file_extension.lower()}"
            )
            
            logger.info(f"Файл {object_name} успешно загружен")
            return object_name
            
        except S3Error as e:
            logger.error(f"Ошибка при загрузке файла: {e}")
            raise
    
    def get_file_url(self, object_name: str, expires_in_days: int = 7) -> str:
        """
        Генерирует публичный URL для файла.
        
        Args:
            object_name: Путь к файлу в хранилище
            expires_in_days: Количество дней, на которое действителен URL
            
        Returns:
            Публичный URL файла
        """
        try:
            # Для MinIO используем presigned URL
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(days=expires_in_days)
            )
            return url
        except S3Error as e:
            logger.error(f"Ошибка при генерации URL: {e}")
            raise
    
    def get_public_url(self, object_name: str) -> str:
        """
        Генерирует публичный URL без срока действия (если bucket публичный).
        
        Args:
            object_name: Путь к файлу в хранилище
            
        Returns:
            Публичный URL файла
        """
        protocol = "https" if settings.S3_USE_SSL else "http"
        return f"{protocol}://{settings.S3_ENDPOINT.replace('http://', '').replace('https://', '')}/{self.bucket_name}/{object_name}"
    
    async def delete_file(self, object_name: str) -> None:
        """
        Удаляет файл из хранилища.
        
        Args:
            object_name: Путь к файлу в хранилище
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"Файл {object_name} удален")
        except S3Error as e:
            logger.error(f"Ошибка при удалении файла: {e}")
            # Не поднимаем исключение, так как файл может уже не существовать


# Создание глобального экземпляра сервиса
storage_service = StorageService()

