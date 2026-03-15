"""
Эндпоинты для работы с пользователями.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pathlib import Path

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.models.user_interest import UserInterest
from app.schemas.user import UserResponse, UserUpdate, PasswordChange, LocationUpdate
from pydantic import BaseModel, Field
from app.services.storage import storage_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Получение информации о текущем пользователе.
    
    Требует валидный JWT токен. Используйте кнопку "Authorize" в Swagger UI.
    """
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Обновление данных текущего пользователя.
    
    Требует валидный JWT токен в заголовке Authorization.
    Позволяет обновить: имя, фамилию, био, дату рождения, геолокацию.
    """
    # Обновление только переданных полей
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.post("/upload-avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(..., description="Файл изображения (JPG, PNG, WEBP)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Загрузка аватара пользователя.
    
    Требует валидный JWT токен в заголовке Authorization.
    Принимает файл изображения, загружает его в хранилище и обновляет avatar_url.
    
    Ограничения:
    - Максимальный размер: 5 МБ
    - Разрешенные форматы: JPG, JPEG, PNG, WEBP
    """
    # Проверка типа файла
    file_extension = Path(file.filename).suffix.lstrip(".").lower()
    if file_extension not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый формат файла. Разрешенные: JPG, JPEG, PNG, WEBP"
        )
    
    try:
        # Чтение содержимого файла
        file_content = await file.read()
        
        # Удаление старого аватара, если он существует
        if current_user.avatar_url:
            try:
                # Извлекаем object_name из URL (если это presigned URL, нужно парсить)
                # Для упрощения просто загружаем новый файл
                pass
            except Exception as e:
                # Игнорируем ошибки при удалении старого файла
                pass
        
        # Загрузка нового файла
        object_name = await storage_service.upload_file(
            file_content=file_content,
            file_extension=file_extension,
            folder="avatars"
        )
        
        # Генерация URL для доступа к файлу.
        # Используем presigned URL, чтобы не настраивать публичный bucket в MinIO.
        avatar_url = storage_service.get_file_url(object_name)
        
        # Обновление пользователя
        current_user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(current_user)
        
        return UserResponse.model_validate(current_user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )


@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Смена пароля пользователя.
    
    Требует валидный JWT токен в заголовке Authorization.
    Необходимо указать текущий пароль для подтверждения.
    """
    # Проверка текущего пароля
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )
    
    # Проверка, что новый пароль отличается от старого
    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль должен отличаться от текущего"
        )
    
    # Хеширование нового пароля
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Пароль успешно изменен"}


@router.post("/location", response_model=UserResponse)
async def set_location(
    payload: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Обновление геолокации пользователя.

    Сохраняет координаты в колонку `location` (GEOGRAPHY POINT, SRID 4326).
    Формат: POINT(lon lat).
    """
    point_wkt = f"SRID=4326;POINT({payload.longitude} {payload.latitude})"

    await db.execute(
        text("UPDATE users SET location = ST_GeogFromText(:wkt) WHERE id = :uid"),
        {"wkt": point_wkt, "uid": current_user.id},
    )
    await db.commit()

    # Обновляем объект текущего пользователя
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


class UserInterestsUpdate(BaseModel):
    """Обновление списка интересов пользователя (простые текстовые теги)."""

    tags: list[str] = Field(default_factory=list, description="Список интересов пользователя")


@router.post("/interests", response_model=UserResponse)
async def set_interests(
    payload: UserInterestsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Установка/обновление интересов текущего пользователя.

    Полностью заменяет список интересов пользователя на переданный.
    """
    # Удаляем старые интересы
    await db.execute(
        text("DELETE FROM user_interests WHERE user_id = :uid"),
        {"uid": current_user.id},
    )

    # Вставляем новые, если есть
    for tag in payload.tags:
        cleaned = tag.strip()
        if not cleaned:
            continue
        db.add(UserInterest(user_id=current_user.id, tag=cleaned))

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/nearby", response_model=list[UserResponse])
async def get_nearby_users(
    radius_km: int = 50,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str | None = None,
    has_common_interests: bool = False,
    sort_by: str = "distance",  # distance | random | compatibility
    global_search: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    """
    Получение списка пользователей поблизости.

    Гибкий поиск пользователей поблизости (или глобально).

    - Исключает текущего пользователя и тех, с кем уже есть запись в `swipes`
    - Поддерживает фильтры: возраст, пол, наличие общих интересов
    - Поддерживает режим глобального поиска (без геофильтра)
    """
    if not global_search and radius_km != -1 and current_user.location is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала нужно установить свою геолокацию через /users/location",
        )

    # Нормализуем sort_by
    sort_by_normalized = sort_by.lower()
    if sort_by_normalized not in {"distance", "random", "compatibility"}:
        sort_by_normalized = "distance"

    is_global = global_search or radius_km == -1
    radius_m = radius_km * 1000 if not is_global else -1

    params: dict[str, object] = {
        "uid": current_user.id,
        "radius": radius_m,
    }

    # Генерируем условие по полу только если фильтр задан.
    gender_condition = ""
    if gender is not None:
        gender_condition = "AND u.gender = :gender"
        params["gender"] = gender

    # Условия по возрасту: добавляем и параметр только при наличии фильтра.
    age_min_condition = ""
    if age_min is not None:
        age_min_condition = (
            "AND u.birthdate IS NOT NULL "
            "AND DATE_PART('year', age(u.birthdate)) >= CAST(:age_min AS INTEGER)"
        )
        params["age_min"] = age_min

    age_max_condition = ""
    if age_max is not None:
        age_max_condition = (
            "AND u.birthdate IS NOT NULL "
            "AND DATE_PART('year', age(u.birthdate)) <= CAST(:age_max AS INTEGER)"
        )
        params["age_max"] = age_max

    # Фильтр по общим интересам включаем только если он явно включён.
    common_interests_condition = ""
    if has_common_interests:
        common_interests_condition = """
                  AND EXISTS (
                        SELECT 1
                        FROM user_interests ui
                        JOIN current_interests ci ON ci.tag = ui.tag
                        WHERE ui.user_id = u.id
                  )
        """

    if is_global:
        # Глобальный поиск без геофильтра, но с подготовкой к AI-скорингу.
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
                  {common_interests_condition}
            )
            SELECT id, ai_score
            FROM base_candidates
            """
    else:
        # Поиск рядом с использованием PostGIS
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
                  {common_interests_condition}
            )
            SELECT id, distance, ai_score
            FROM base_candidates
            """

    # Добавляем сортировку
    if sort_by_normalized == "random":
        order_sql = "\n ORDER BY random() \n LIMIT 50"
    elif sort_by_normalized == "compatibility":
        # Пока сортируем по ai_score, а distance учитываем только если он есть
        if is_global:
            order_sql = "\n ORDER BY ai_score DESC NULLS LAST, id \n LIMIT 50"
        else:
            order_sql = (
                "\n ORDER BY ai_score DESC NULLS LAST, distance ASC NULLS LAST, id \n LIMIT 50"
            )
    else:
        # distance по умолчанию
        if is_global:
            # В глобальном режиме distance нет, сортируем только по ai_score
            order_sql = "\n ORDER BY ai_score DESC NULLS LAST, id \n LIMIT 50"
        else:
            order_sql = (
                "\n ORDER BY distance ASC NULLS LAST, ai_score DESC NULLS LAST, id \n LIMIT 50"
            )

    sql_text = (base_sql + order_sql).format(
        gender_condition=gender_condition,
        age_min_condition=f" {age_min_condition}" if age_min_condition else "",
        age_max_condition=f" {age_max_condition}" if age_max_condition else "",
        common_interests_condition=common_interests_condition,
    )
    query = text(sql_text)

    result = await db.execute(query, params)
    rows = result.fetchall()
    ids = [row[0] for row in rows]

    if not ids:
        return []

    result_users = await db.execute(select(User).where(User.id.in_(ids)))
    return [UserResponse.model_validate(u) for u in result_users.scalars().all()]

