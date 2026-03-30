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


-- Миграция 003: добавление колонки location (GEOGRAPHY POINT, SRID 4326)

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS location GEOGRAPHY(POINT, 4326);

-- Пример проверки PostGIS:
-- SELECT id,
--        ST_AsText(location)                            AS wkt,
--        ST_Distance(
--          location,
--          ST_GeogFromText('SRID=4326;POINT(37.6173 55.7558)')
--        ) AS dist_m
-- FROM users
-- WHERE location IS NOT NULL
-- ORDER BY dist_m
-- LIMIT 10;


-- Миграция 004: таблицы swipes и matches для логики свайпов и матчей

CREATE TABLE IF NOT EXISTS swipes (
    user_id_1 INT NOT NULL,
    user_id_2 INT NOT NULL,
    decision_1 BOOLEAN NULL,
    decision_2 BOOLEAN NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_swipes PRIMARY KEY (user_id_1, user_id_2)
);

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    user_id_1 INT NOT NULL,
    user_id_2 INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_swipes_user1 ON swipes(user_id_1);
CREATE INDEX IF NOT EXISTS idx_swipes_user2 ON swipes(user_id_2);
CREATE INDEX IF NOT EXISTS idx_matches_user1 ON matches(user_id_1);
CREATE INDEX IF NOT EXISTS idx_matches_user2 ON matches(user_id_2);


-- Добавление поля gender в таблицу users и таблицы user_interests.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS gender VARCHAR(20);

CREATE TABLE IF NOT EXISTS user_interests (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_interests_user_id ON user_interests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interests_tag ON user_interests(tag);

-- TODO: при необходимости можно добавить справочник интересов и связи многие-ко-многим.


