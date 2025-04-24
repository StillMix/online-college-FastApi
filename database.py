from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Создаем директорию для базы данных, если она не существует
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)

# Создаем директорию для изображений курсов
COURSE_IMG_DIR = BASE_DIR / "CourseImg"
COURSE_IMG_DIR.mkdir(exist_ok=True)

# URL для подключения к SQLite DB
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_DIR}/college.db"

# Создание движка SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создание сессии для соединения с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
