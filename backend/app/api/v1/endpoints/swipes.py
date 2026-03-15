"""
Эндпоинты для логики свайпов, матчей и ленты (feed).
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.swipe import Match, Swipe
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.redis_client import get_redis

router = APIRouter()


class SwipeCreate(BaseModel):
    """Схема для создания свайпа."""

    target_user_id: int = Field(..., gt=0, description="ID пользователя, которого свайпаем")
    decision: bool = Field(..., description="True = like, False = dislike")


class SwipeResponse(BaseModel):
    """Ответ на операцию свайпа."""

    is_match: bool = Field(..., description="True, если получился взаимный лайк")


@router.post("/swipes", response_model=SwipeResponse)
async def swipe(
    payload: SwipeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SwipeResponse:
    """
    Совершение свайпа (like/dislike) с атомарной логикой UPSERT.

    - Одна строка в `swipes` на пару пользователей (user_id_1 < user_id_2)
    - `decision_1` / `decision_2` обновляются в зависимости от того, чей ID меньше
    - При взаимном лайке создаётся запись в `matches` и возвращается `is_match = True`
    """
    if payload.target_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя свайпнуть самого себя",
        )

    # Проверяем, что целевой пользователь существует
    result = await db.execute(select(User).where(User.id == payload.target_user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Целевой пользователь не найден",
        )

    user_id_1 = min(current_user.id, payload.target_user_id)
    user_id_2 = max(current_user.id, payload.target_user_id)
    is_current_1 = current_user.id == user_id_1

    stmt = (
        insert(Swipe)
        .values(
            user_id_1=user_id_1,
            user_id_2=user_id_2,
            decision_1=payload.decision if is_current_1 else None,
            decision_2=payload.decision if not is_current_1 else None,
        )
        .on_conflict_do_update(
            index_elements=[Swipe.user_id_1, Swipe.user_id_2],
            set_={
                "decision_1": payload.decision if is_current_1 else Swipe.decision_1,
                "decision_2": payload.decision if not is_current_1 else Swipe.decision_2,
            },
        )
        .returning(Swipe.user_id_1, Swipe.user_id_2, Swipe.decision_1, Swipe.decision_2)
    )

    row = (await db.execute(stmt)).first()
    if row is None:
        is_match = False
    else:
        decision_1 = row.decision_1
        decision_2 = row.decision_2
        is_match = bool(decision_1 and decision_2)

        if is_match:
            # Проверяем, нет ли уже матча
            result_match = await db.execute(
                select(Match).where(
                    (Match.user_id_1 == user_id_1) & (Match.user_id_2 == user_id_2)
                )
            )
            existing = result_match.scalar_one_or_none()
            if existing is None:
                db.add(Match(user_id_1=user_id_1, user_id_2=user_id_2))

    # Фиксируем изменения
    await db.commit()

    # Инвалидация кэша фида
    redis = await get_redis()
    await redis.delete(f"feed:{current_user.id}")

    return SwipeResponse(is_match=is_match)


@router.get("/feed", response_model=List[UserResponse])
async def get_feed(
    radius_km: int = 50,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str | None = None,
    has_common_interests: bool = False,
    sort_by: str = "distance",  # distance | random | compatibility
    global_search: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    """
    Лента кандидатов для свайпа с гибкой фильтрацией и подготовкой к AI-рекомендациям.

    - Проверяет Redis по ключу `feed:{user_id}:{fingerprint_фильтров}`
    - Если кэша нет — генерирует до 20–50 кандидатов через PostGIS/SQL и сохраняет в Redis на 5 минут
    - Исключает пользователей, по которым уже есть записи в `swipes`
    - Поддерживает фильтры по радиусу, возрасту, полу и общим интересам
    """
    if not global_search and radius_km != -1 and current_user.location is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала нужно установить свою геолокацию через /users/location",
        )

    # Формируем "отпечаток" фильтров для ключа кэша
    filter_fingerprint = f"r={radius_km}|amin={age_min}|amax={age_max}|g={gender}|ci={int(has_common_interests)}|sb={sort_by}|glob={int(global_search)}"

    redis = await get_redis()
    cache_key = f"feed:{current_user.id}:{filter_fingerprint}"

    cached_ids = await redis.get(cache_key)
    if cached_ids:
        import json

        ids = json.loads(cached_ids)
        if not ids:
            return []
        result = await db.execute(select(User).where(User.id.in_(ids)))
        return [UserResponse.model_validate(u) for u in result.scalars().all()]

    # Нормализуем sort_by
    sort_by_normalized = sort_by.lower()
    if sort_by_normalized not in {"distance", "random", "compatibility"}:
        sort_by_normalized = "distance"

    is_global = global_search or radius_km == -1
    radius_m = radius_km * 1000 if not is_global else -1

    params: dict[str, object] = {
        "uid": current_user.id,
        "radius": radius_m,
        "age_min": age_min,
        "age_max": age_max,
        "gender": gender,
        "has_common_interests": has_common_interests,
        "is_global": is_global,
        "limit": 20,
    }

    # Генерируем кусок условия по полу только если фильтр задан,
    # чтобы избежать проблем с типом NULL-параметра в PostgreSQL.
    gender_condition = "AND u.gender = :gender" if gender is not None else ""

    # Аналогично собираем условия по возрасту.
    age_min_condition = (
        "AND u.birthdate IS NOT NULL "
        "AND DATE_PART('year', age(u.birthdate)) >= :age_min"
        if age_min is not None
        else ""
    )
    age_max_condition = (
        "AND u.birthdate IS NOT NULL "
        "AND DATE_PART('year', age(u.birthdate)) <= :age_max"
        if age_max is not None
        else ""
    )

    if is_global:
        base_sql = """
            WITH swiped AS (
                SELECT CASE
                         WHEN user_id_1 = :uid THEN user_id_2
                         ELSE user_id_1
                       END AS other_id
                FROM swipes
                WHERE user_id_1 = :uid OR user_id_2 = :uid
            ),
            current_interests AS (
                SELECT tag
                FROM user_interests
                WHERE user_id = :uid
            ),
            base_candidates AS (
                SELECT
                    u.id,
                    -- TODO: Здесь будет интеграция с AI-сервисом для расчета веса совместимости
                    COALESCE(
                        (
                            SELECT COUNT(*)::float
                            FROM user_interests ui
                            JOIN current_interests ci ON ci.tag = ui.tag
                            WHERE ui.user_id = u.id
                        ),
                        0.0
                    ) AS ai_score
                FROM users u
                WHERE u.id != :uid
                  AND u.id NOT IN (SELECT other_id FROM swiped)
                  {gender_condition}
                  {age_min_condition}
                  {age_max_condition}
                  AND (
                        NOT :has_common_interests
                        OR EXISTS (
                            SELECT 1
                            FROM user_interests ui
                            JOIN current_interests ci ON ci.tag = ui.tag
                            WHERE ui.user_id = u.id
                        )
                  )
            )
            SELECT id, ai_score
            FROM base_candidates
            """
    else:
        base_sql = """
            WITH user_point AS (
                SELECT location AS loc
                FROM users
                WHERE id = :uid AND location IS NOT NULL
            ),
            swiped AS (
                SELECT CASE
                         WHEN user_id_1 = :uid THEN user_id_2
                         ELSE user_id_1
                       END AS other_id
                FROM swipes
                WHERE user_id_1 = :uid OR user_id_2 = :uid
            ),
            current_interests AS (
                SELECT tag
                FROM user_interests
                WHERE user_id = :uid
            ),
            base_candidates AS (
                SELECT
                    u.id,
                    ST_Distance(u.location, p.loc) AS distance,
                    -- TODO: Здесь будет интеграция с AI-сервисом для расчета веса совместимости
                    COALESCE(
                        (
                            SELECT COUNT(*)::float
                            FROM user_interests ui
                            JOIN current_interests ci ON ci.tag = ui.tag
                            WHERE ui.user_id = u.id
                        ),
                        0.0
                    ) AS ai_score
                FROM users u,
                     user_point p
                WHERE u.id != :uid
                  AND u.location IS NOT NULL
                  AND u.id NOT IN (SELECT other_id FROM swiped)
                  AND ST_DWithin(u.location, p.loc, :radius)
                  {gender_condition}
                  {age_min_condition}
                  {age_max_condition}
                  AND (
                        NOT :has_common_interests
                        OR EXISTS (
                            SELECT 1
                            FROM user_interests ui
                            JOIN current_interests ci ON ci.tag = ui.tag
                            WHERE ui.user_id = u.id
                        )
                  )
            )
            SELECT id, distance, ai_score
            FROM base_candidates
            """

    if sort_by_normalized == "random":
        order_sql = "\n ORDER BY random() \n LIMIT :limit"
    elif sort_by_normalized == "compatibility":
        if is_global:
            order_sql = "\n ORDER BY ai_score DESC NULLS LAST, id \n LIMIT :limit"
        else:
            order_sql = (
                "\n ORDER BY ai_score DESC NULLS LAST, distance ASC NULLS LAST, id \n LIMIT :limit"
            )
    else:
        if is_global:
            order_sql = "\n ORDER BY ai_score DESC NULLS LAST, id \n LIMIT :limit"
        else:
            order_sql = (
                "\n ORDER BY distance ASC NULLS LAST, ai_score DESC NULLS LAST, id \n LIMIT :limit"
            )

    # Подставляем условие по полу (строка либо пустая, либо с "AND u.gender = :gender")
    sql_text = (base_sql + order_sql).format(
        gender_condition=gender_condition,
        age_min_condition=f" {age_min_condition}" if age_min_condition else "",
        age_max_condition=f" {age_max_condition}" if age_max_condition else "",
    )
    query = text(sql_text)

    result_ids = await db.execute(query, params)
    rows = result_ids.fetchall()
    ids = [row[0] for row in rows]

    import json

    await redis.set(cache_key, json.dumps(ids), ex=300)  # 5 минут

    if not ids:
        return []

    result_users = await db.execute(select(User).where(User.id.in_(ids)))
    return [UserResponse.model_validate(u) for u in result_users.scalars().all()]


