"""
Pydantic схемы для валидации данных пользователя.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Базовая схема пользователя."""
    email: EmailStr = Field(..., description="Email пользователя")
    first_name: Optional[str] = Field(None, max_length=100, description="Имя пользователя")
    last_name: Optional[str] = Field(None, max_length=100, description="Фамилия пользователя")


class UserCreate(UserBase):
    """Схема для создания нового пользователя."""
    password: str = Field(..., min_length=8, description="Пароль (минимум 8 символов)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "first_name": "Иван",
                "last_name": "Иванов"
            }
        }


class UserLogin(BaseModel):
    """Схема для входа пользователя."""
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class UserUpdate(BaseModel):
    """Схема для обновления данных пользователя."""
    first_name: Optional[str] = Field(None, max_length=100, description="Имя пользователя")
    last_name: Optional[str] = Field(None, max_length=100, description="Фамилия пользователя")
    bio: Optional[str] = Field(None, max_length=1000, description="Описание профиля")
    birthdate: Optional[date] = Field(None, description="Дата рождения")
    city: Optional[str] = Field(None, max_length=100, description="Город проживания")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Широта (-90 до 90)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Долгота (-180 до 180)")
    
    @field_validator('birthdate')
    @classmethod
    def validate_birthdate(cls, v: Optional[date]) -> Optional[date]:
        """Проверка, что дата рождения не в будущем."""
        if v and v > date.today():
            raise ValueError("Дата рождения не может быть в будущем")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Иван",
                "last_name": "Иванов",
                "bio": "Люблю путешествовать и встречать новых людей",
                "birthdate": "1990-01-01",
                "latitude": 55.7558,
                "longitude": 37.6173
            }
        }


class UserResponse(UserBase):
    """Схема для ответа с данными пользователя."""
    id: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    birthdate: Optional[date] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool
    is_verified: bool
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Для работы с SQLAlchemy моделями


class PasswordChange(BaseModel):
    """Схема для смены пароля."""
    old_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=8, description="Новый пароль (минимум 8 символов)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "oldpassword123",
                "new_password": "newpassword123"
            }
        }


class LocationUpdate(BaseModel):
    """Схема для обновления геолокации пользователя."""

    latitude: float = Field(..., ge=-90, le=90, description="Широта (-90 до 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Долгота (-180 до 180)")



class Token(BaseModel):
    """Схема для JWT токена."""
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field(default="bearer", description="Тип токена")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

