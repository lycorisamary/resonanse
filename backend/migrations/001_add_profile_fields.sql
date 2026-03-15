-- Миграция: Добавление полей для профиля пользователя
-- Дата: 2024
-- Описание: Добавляет поля birthdate, обновляет latitude и longitude на Float

-- Добавление поля birthdate (дата рождения)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS birthdate DATE NULL;

-- Изменение типа данных для latitude и longitude с String на Float
-- Сначала удаляем старые колонки (если они существуют)
ALTER TABLE users 
DROP COLUMN IF EXISTS latitude,
DROP COLUMN IF EXISTS longitude;

-- Добавляем новые колонки с типом Float
ALTER TABLE users 
ADD COLUMN latitude FLOAT NULL,
ADD COLUMN longitude FLOAT NULL;

-- Добавляем комментарии к колонкам
COMMENT ON COLUMN users.birthdate IS 'Дата рождения пользователя';
COMMENT ON COLUMN users.latitude IS 'Широта местоположения (-90 до 90)';
COMMENT ON COLUMN users.longitude IS 'Долгота местоположения (-180 до 180)';

-- Создаем индексы для геолокации (для будущего использования в поиске)
CREATE INDEX IF NOT EXISTS idx_users_location ON users(latitude, longitude) 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

