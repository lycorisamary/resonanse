"""
Скрипт для инициализации базы данных.
Создает все таблицы в базе данных.

ВАЖНО: Все модели SQLAlchemy должны быть импортированы ПЕРЕД вызовом init_db(),
чтобы они были зарегистрированы в Base.metadata.
"""
import asyncio

# Импорт всех моделей ПЕРЕД импортом init_db
# Это необходимо для регистрации моделей в Base.metadata
from app.models import User  # noqa: F401

# Импорт функции инициализации после импорта моделей
from app.core.database import init_db


async def main():
    """Основная функция для инициализации БД."""
    print("Инициализация базы данных...")
    print("Импортированные модели:")
    print(f"  - User (таблица: users)")
    await init_db()
    print("База данных успешно инициализирована!")


if __name__ == "__main__":
    asyncio.run(main())


