from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models.user import User
from schemas.user import UserCreate, UserUpdate, User as UserSchema
from services.users import (
    create_user,
    get_user_by_id,
    update_user,
    delete_user,
    authenticate_user,
)
from schemas.token import Token
from services.auth import create_access_token

router = APIRouter()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Регистрация нового пользователя
    """
    return await create_user(db, user)


@router.post("/login", response_model=Token)
async def login(username: str, password: str, db: AsyncSession = Depends(get_db)):
    """
    Вход пользователя и получение токена
    """
    user = await authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Получение данных текущего пользователя
    """
    return current_user


@router.get("/{user_id}", response_model=UserSchema)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Получение данных пользователя по ID
    """
    db_user = await get_user_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return db_user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user_details(
    user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Обновление данных пользователя
    """
    db_user = await get_user_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return await update_user(db, db_user, user_update)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Удаление пользователя
    """
    db_user = await get_user_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    await delete_user(db, db_user)
    return None
