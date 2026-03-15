"""
Эндпоинты для админ-панели.
Доступ только для администратора (проверка по email из настроек).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


async def check_admin_access(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency для проверки прав администратора.
    
    Пользователь считается администратором, если его email совпадает с ADMIN_EMAIL.
    При первом успешном доступе такого пользователя флаг `is_admin` автоматически
    выставляется в True и сохраняется в базе, чтобы фронтенд мог отобразить админку.
    """
    if current_user.email != settings.ADMIN_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права администратора."
        )
    
    # Если email совпадает, но флаг is_admin ещё не выставлен — выставляем его
    if not current_user.is_admin:
        current_user.is_admin = True
        await db.commit()
        await db.refresh(current_user)
    
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(check_admin_access),
    db: AsyncSession = Depends(get_db)
) -> List[UserResponse]:
    """
    Получение списка всех пользователей.
    
    Доступно только администратору.
    """
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    admin: User = Depends(check_admin_access),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Получение информации о пользователе по ID.
    
    Доступно только администратору.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin: User = Depends(check_admin_access),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Обновление данных пользователя администратором.
    
    Доступно только администратору.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Обновление полей
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    admin: User = Depends(check_admin_access),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Активация пользователя.
    
    Доступно только администратору.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    admin: User = Depends(check_admin_access),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Деактивация пользователя.
    
    Доступно только администратору.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(check_admin_access),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Удаление пользователя.
    
    Доступно только администратору.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Не позволяем удалить самого себя
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя"
        )
    
    # Удаление пользователя
    await db.delete(user)
    await db.commit()
    
    return {"message": "Пользователь успешно удален"}

