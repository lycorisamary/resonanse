"""
Настройки приложения.
Все секреты и конфигурация загружаются из переменных окружения.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Класс настроек приложения."""
    
    # Настройки приложения
    APP_NAME: str = "Резонанс"
    DEBUG: bool = False
    
    # Настройки базы данных PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Настройки Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Настройки JWT
    SECRET_KEY: str  # Секретный ключ для подписи JWT токенов
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
    
    # CORS настройки
    CORS_ORIGINS: List[str] = ["*"]
    
    # Настройки S3/MinIO для хранения файлов
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "resonans-avatars"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False  # Для локального MinIO
    
    # Настройки загрузки файлов
    MAX_FILE_SIZE_MB: int = 5  # Максимальный размер файла в МБ
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]
    
    # Настройки админ-панели
    ADMIN_EMAIL: str = "admin@resonans.ru"  # Email администратора (только этот пользователь может войти в админ-панель)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    @property
    def database_url(self) -> str:
        """Формирует URL для подключения к PostgreSQL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def redis_url(self) -> str:
        """Формирует URL для подключения к Redis."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Создание экземпляра настроек
settings = Settings()

