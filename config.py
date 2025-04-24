from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

# Определяем базовый путь проекта
BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    # Настройки приложения
    APP_NAME: str = "Online College API"
    DEBUG: bool = True
    
    # Настройки базы данных
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/online_college.db"
    
    # Настройки безопасности
    SECRET_KEY: str = "your-secret-key-for-jwt-generation"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Настройки CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создаем экземпляр настроек
settings = Settings()