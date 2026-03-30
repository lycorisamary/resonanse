"""
Главный роутер API версии 1.
Объединяет все эндпоинты приложения.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, admin, cities, swipes, chat

api_router = APIRouter()

# Подключение роутеров эндпоинтов
api_router.include_router(auth.router, prefix="/auth", tags=["Авторизация"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
api_router.include_router(admin.router, prefix="/admin", tags=["Админ-панель"])
api_router.include_router(cities.router, prefix="/cities", tags=["Города"])
api_router.include_router(swipes.router, prefix="", tags=["Свайпы и лента"])
api_router.include_router(chat.router, prefix="", tags=["Чат и сообщения"])

