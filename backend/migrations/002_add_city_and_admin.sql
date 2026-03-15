-- Миграция: Добавление поля city и is_admin
-- Дата: 2024
-- Описание: Добавляет поле города проживания и флаг администратора

-- Добавление поля city
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS city VARCHAR(100) NULL;

-- Добавление поля is_admin
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL;

-- Добавляем комментарии
COMMENT ON COLUMN users.city IS 'Город проживания';
COMMENT ON COLUMN users.is_admin IS 'Является ли администратором';

-- Создаем индекс для поиска по городу
CREATE INDEX IF NOT EXISTS idx_users_city ON users(city) 
WHERE city IS NOT NULL;

