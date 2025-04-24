from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import create_tables
from routers import users, courses

@asynccontextmanager
async def lifespan(app: FastAPI):
    # При запуске приложения выполняем создание таблиц
    await create_tables()
    yield
    # При завершении работы приложения можно выполнить дополнительные действия

app = FastAPI(
    title="Online College API",
    description="API для онлайн-колледжа на FastAPI",
    version="0.1.0",
    lifespan=lifespan
)

# Настройка CORS для возможности обращения к API из фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])

@app.get("/api/health", tags=["health"])
async def health_check():
    """
    Проверка работоспособности API
    """
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)