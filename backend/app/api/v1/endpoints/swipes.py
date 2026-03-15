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
    radius_km: float = 10.0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    """
    Лента кандидатов для свайпа.

    - Проверяет Redis по ключу `feed:{user_id}`
    - Если кэша нет — генерирует до 20 кандидатов через PostGIS и сохраняет в Redis на 5 минут
    - Исключает пользователей, по которым уже есть записи в `swipes`
    """
    if current_user.location is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала нужно установить свою геолокацию через /users/location",
        )

    redis = await get_redis()
    cache_key = f"feed:{current_user.id}"

    cached_ids = await redis.get(cache_key)
    if cached_ids:
        import json

        ids = json.loads(cached_ids)
        if not ids:
            return []
        result = await db.execute(select(User).where(User.id.in_(ids)))
        return [UserResponse.model_validate(u) for u in result.scalars().all()]

    radius_m = radius_km * 1000

    # Генерация кандидатов через PostGIS
    query = text(
        """
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
        )
        SELECT u.id
        FROM users u, user_point p
        WHERE u.id != :uid
          AND u.location IS NOT NULL
          AND u.id NOT IN (SELECT other_id FROM swiped)
          AND ST_DWithin(u.location, p.loc, :radius)
        ORDER BY ST_Distance(u.location, p.loc)
        LIMIT 20
        """
    )

    result_ids = await db.execute(query, {"uid": current_user.id, "radius": radius_m})
    rows = result_ids.fetchall()
    ids = [row[0] for row in rows]

    import json

    await redis.set(cache_key, json.dumps(ids), ex=300)  # 5 минут

    if not ids:
        return []

    result_users = await db.execute(select(User).where(User.id.in_(ids)))
    return [UserResponse.model_validate(u) for u in result_users.scalars().all()]


