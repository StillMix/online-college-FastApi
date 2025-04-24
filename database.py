from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from config import settings

Base = declarative_base()

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=settings.DEBUG,
    future=True
)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    engine, 
    expire_on_commit=False,
    class_=AsyncSession
)

# Зависимость для получения сессии БД
async def get_db():
    """
    Генератор асинхронных сессий БД
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Функция для создания таблиц
async def create_tables():
    """
    Создает таблицы в базе данных
    """
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # Раскомментируйте для пересоздания всех таблиц
        await conn.run_sync(Base.metadata.create_all)