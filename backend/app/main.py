"""
Главный файл приложения FastAPI.
Инициализирует приложение и подключает роутеры.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.dependencies import security
from app.api.v1.router import api_router

# Создание экземпляра приложения
app = FastAPI(
    title="Резонанс API",
    description="API для мобильного приложения знакомств Резонанс",
    version="1.0.0",
    # Настройка безопасности для Swagger UI
    swagger_ui_init_oauth={
        "clientId": "swagger-ui",
        "usePkceWithAuthorizationCodeGrant": False,
    },
)

# Настройка CORS для работы с Flutter приложением
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работы API."""
    return {"message": "Резонанс API работает", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения."""
    return {"status": "healthy"}

