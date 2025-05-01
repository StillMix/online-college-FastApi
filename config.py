import os
from pathlib import Path
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Базовые настройки приложения
    APP_NAME: str = "Онлайн-колледж API"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Настройки базы данных
    DATABASE_URL: str = "sqlite:///./db/college.db"

    # Пути к директориям
    BASE_DIR: Path = Path(__file__).resolve().parent
    COURSE_IMG_DIR: Path = BASE_DIR / "CourseImg"

    # Настройки для JWT
    SECRET_KEY: str = "your-secret-key-for-jwt"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS настройки
    CORS_ORIGINS: list = [
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
        "https://109.73.194.69",
        "http://109.73.194.69",
        "https://stillmix-online-college-fastapi-e9c2.twc1.net",
        "https://stillmix-online-college-7fcc.twc1.net",
        "http://stillmix-online-college-fastapi-e9c2.twc1.net",
        "http://stillmix-online-college-7fcc.twc1.net",
    ]

    # Настройки загрузки файлов
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_IMAGE_TYPES: list = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/svg+xml",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Создаем экземпляр настроек
settings = Settings()

# Создаем необходимые директории
settings.COURSE_IMG_DIR.mkdir(exist_ok=True)

# Директория для базы данных
DB_DIR = settings.BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)
