"""
Скрипт для применения миграций базы данных.

ВНИМАНИЕ: Для применения миграций рекомендуется использовать Alembic.
Этот скрипт - временное решение для ручного применения SQL миграций.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def apply_migration():
    """Применяет SQL миграцию к базе данных."""
    migration_file = Path(__file__).parent / "migrations" / "001_add_profile_fields.sql"
    
    if not migration_file.exists():
        print(f"Ошибка: файл миграции не найден: {migration_file}")
        sys.exit(1)
    
    # Чтение SQL из файла
    sql_content = migration_file.read_text(encoding='utf-8')
    
    # Создание подключения
    engine = create_async_engine(settings.database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Выполнение SQL команд
            # Примечание: asyncpg не поддерживает выполнение нескольких команд за раз
            # Разделяем по ';' и выполняем по очереди
            commands = [
                cmd.strip() 
                for cmd in sql_content.split(';') 
                if cmd.strip() and not cmd.strip().startswith('--')
            ]
            
            for command in commands:
                if command:
                    await conn.execute(text(command))
        
        print("Миграция успешно применена!")
        
    except Exception as e:
        print(f"Ошибка при применении миграции: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Применение миграции базы данных...")
    print("Убедитесь, что база данных запущена (docker-compose up -d postgres)")
    asyncio.run(apply_migration())

