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


