from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from database import engine, Base
from routers import course, user, auth
from models.course import Base as CourseBase

# Создаем таблицы в базе данных
CourseBase.metadata.create_all(bind=engine)

app = FastAPI(
    title="Онлайн-колледж API",
    description="API для платформы онлайн-обучения",
    version="0.1.0",
)

# Настройка CORS
origins = [
    "http://localhost:8080",
    "http://localhost:8000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8000",
    "https://stillmix-online-college-fastapi-e9c2.twc1.net",
    "https://stillmix-online-college-7fcc.twc1.net",
    "http://stillmix-online-college-fastapi-e9c2.twc1.net",
    "http://stillmix-online-college-7fcc.twc1.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация маршрутов
app.include_router(auth.router)
app.include_router(course.router)
app.include_router(user.router)

# Настройка статических файлов
BASE_DIR = Path(__file__).resolve().parent
COURSE_IMG_DIR = BASE_DIR / "CourseImg"
COURSE_IMG_DIR.mkdir(exist_ok=True)

# Монтирование директории с изображениями
app.mount(
    "/CourseImg", StaticFiles(directory=str(COURSE_IMG_DIR)), name="course_images"
)

# Монтирование директории с аватарами пользователей
USERS_AVATAR_DIR = BASE_DIR / "UsersAvatar"
USERS_AVATAR_DIR.mkdir(exist_ok=True)
app.mount(
    "/UsersAvatar", StaticFiles(directory=str(USERS_AVATAR_DIR)), name="user_avatars"
)


@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в API онлайн-колледжа!"}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API работает корректно"}


# Обработчик исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"message": f"Произошла ошибка: {str(exc)}"}
    )


# Для запуска приложения используйте:
# uvicorn main:app --reload --port 8000

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
