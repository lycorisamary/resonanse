"""
Настройка подключения к базе данных PostgreSQL через SQLAlchemy.
Используется асинхронный режим работы.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Создание асинхронного движка для подключения к БД
engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,  # Логирование SQL запросов в режиме отладки
    future=True,
)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency для получения сессии базы данных.
    Используется в эндпоинтах FastAPI.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Инициализация базы данных - создание всех таблиц."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

