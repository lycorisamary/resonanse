"""
Модель пользователя в базе данных.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Date, Float
from sqlalchemy.sql import func
from geoalchemy2 import Geography

from app.core.database import Base


class User(Base):
    """
    Модель пользователя.
    
    Хранит основную информацию о пользователе:
    - Учетные данные (email, пароль)
    - Профиль (имя, описание, фото)
    - Статус активации и даты создания/обновления
    """
    __tablename__ = "users"
    
    # Основные поля
    id = Column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор пользователя")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="Email пользователя")
    hashed_password = Column(String(255), nullable=False, comment="Хешированный пароль")
    
    # Профиль пользователя
    first_name = Column(String(100), nullable=True, comment="Имя пользователя")
    last_name = Column(String(100), nullable=True, comment="Фамилия пользователя")
    bio = Column(Text, nullable=True, comment="Описание профиля")
    avatar_url = Column(String(500), nullable=True, comment="URL аватара пользователя")
    birthdate = Column(Date, nullable=True, comment="Дата рождения пользователя")
    city = Column(String(100), nullable=True, comment="Город проживания")
    
    # Статус и даты
    is_active = Column(Boolean, default=True, nullable=False, comment="Активен ли пользователь")
    is_verified = Column(Boolean, default=False, nullable=False, comment="Верифицирован ли email")
    is_admin = Column(Boolean, default=False, nullable=False, comment="Является ли администратором")
    
    # Геолокация (Float для совместимости, в будущем можно заменить на PostGIS GEOGRAPHY)
    # Широта: -90 до 90, Долгота: -180 до 180
    latitude = Column(Float, nullable=True, comment="Широта местоположения (-90 до 90)")
    longitude = Column(Float, nullable=True, comment="Долгота местоположения (-180 до 180)")

    # Геолокация в формате GEOGRAPHY(POINT, 4326)
    # Хранит точку в виде POINT(lon lat)
    location = Column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
        comment="Геолокация пользователя (GEOGRAPHY POINT, SRID=4326)",
    )
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="Дата создания")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="Дата обновления")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

