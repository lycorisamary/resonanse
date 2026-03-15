"""
Эндпоинты для работы с пользователями.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
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

