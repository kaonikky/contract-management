"""
Модуль с настройками CORS для FastAPI приложения.
Позволяет настроить доступ к API из различных источников.
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем разрешенные источники из переменных окружения или используем значения по умолчанию
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000,http://217.198.5.205").split(",")
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
ALLOWED_HEADERS = ["Content-Type", "Authorization", "X-Requested-With"]

def setup_cors(app: FastAPI) -> None:
    """
    Настраивает CORS для FastAPI приложения
    
    Args:
        app: экземпляр FastAPI приложения
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
    )
    
    print(f"CORS настроен. Разрешенные источники: {ALLOWED_ORIGINS}")