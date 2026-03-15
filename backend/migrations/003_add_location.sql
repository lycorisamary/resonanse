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


