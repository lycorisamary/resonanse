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


