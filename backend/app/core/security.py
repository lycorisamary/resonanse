"""
Модуль для работы с безопасностью: хеширование паролей и JWT токены.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Контекст для хеширования паролей (используется bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие обычного пароля хешированному.
    
    Args:
        plain_password: Обычный пароль
        hashed_password: Хешированный пароль
        
    Returns:
        True если пароли совпадают, иначе False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль с помощью bcrypt.
    
    Args:
        password: Пароль для хеширования
        
    Returns:
        Хешированный пароль
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен доступа.
    
    Args:
        data: Данные для включения в токен (обычно user_id)
        expires_delta: Время жизни токена (по умолчанию из настроек)
        
    Returns:
        JWT токен в виде строки
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Декодирует и проверяет JWT токен.
    
    Args:
        token: JWT токен для декодирования
        
    Returns:
        Словарь с данными из токена или None если токен невалидный
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

