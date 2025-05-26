"""
Главный модуль FastAPI приложения
"""
from fastapi import FastAPI
import os
import logging
from typing import List
import uvicorn

from app.routers import auth, users, contracts, dadata
from app.models.models import User
from app.database.base import get_db
from app.core.auth import get_password_hash
from app.cors_config import setup_cors
from sqlalchemy.orm import Session

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Система управления контрактами - API",
    description="API для управления юридическими контрактами",
    version="1.0.0",
)

# Настройка CORS
setup_cors(app)

# Регистрация маршрутов
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(contracts.router)
app.include_router(dadata.router)  # Добавляем маршруты для DaData API


def create_initial_admin():
    """Создает администратора по умолчанию, если такого пользователя нет в базе"""
    db = next(get_db())
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    
    admin = db.query(User).filter(User.username == admin_username).first()
    if not admin:
        logger.info(f"Создание администратора по умолчанию: {admin_username}")
        hashed_password = get_password_hash(admin_password)
        admin = User(
            username=admin_username,
            password=hashed_password,
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info(f"Администратор по умолчанию создан: {admin_username}")
    else:
        logger.info(f"Администратор уже существует: {admin_username}")


@app.on_event("startup")
async def startup_event():
    """Выполняется при запуске приложения"""
    logger.info("Запуск приложения...")
    create_initial_admin()
    logger.info("Приложение готово к работе")


@app.get("/api")
async def root():
    """Корневой маршрут для проверки работоспособности API"""
    return {"message": "API системы управления контрактами работает"}


if __name__ == "__main__":
    # Запуск сервера, если файл выполняется напрямую
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Запуск сервера на {host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)