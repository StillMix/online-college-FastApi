from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update, delete as sql_delete
from typing import Optional

from models.user import User
from schemas.user import UserCreate, UserUpdate
from services.security import get_password_hash, verify_password


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Создание нового пользователя
    """
    # Проверяем, что пользователь с таким логином и email не существует
    result = await db.execute(
        select(User).where((User.login == user.login) | (User.email == user.email))
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.login == user.login:
            raise ValueError("Пользователь с таким логином уже существует")
        else:
            raise ValueError("Пользователь с таким email уже существует")

    # Хешируем пароль и создаем пользователя
    hashed_password = get_password_hash(user.password)
    db_user = User(
        name=user.name,
        login=user.login,
        email=user.email,
        hashed_password=hashed_password,
        is_admin=False,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """
    Аутентификация пользователя
    """
    # Поиск пользователя по логину или email
    result = await db.execute(
        select(User).where((User.login == username) | (User.email == username))
    )
    user = result.scalar_one_or_none()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Получение пользователя по ID
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user: User, user_update: UserUpdate) -> User:
    """
    Обновление данных пользователя
    """
    # Обновляем только предоставленные поля
    update_data = user_update.dict(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    # Проверка уникальности login и email
    if "login" in update_data or "email" in update_data:
        query = select(User).where(
            (
                (User.login == update_data.get("login"))
                | (User.email == update_data.get("email"))
            )
            & (User.id != user.id)
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if "login" in update_data and existing_user.login == update_data["login"]:
                raise ValueError("Пользователь с таким логином уже существует")
            elif "email" in update_data and existing_user.email == update_data["email"]:
                raise ValueError("Пользователь с таким email уже существует")

    # Обновляем пользователя
    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    """
    Удаление пользователя
    """
    await db.delete(user)
    await db.commit()
