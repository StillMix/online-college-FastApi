from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from services.auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    get_current_active_user,
)
from models.user import User
from schemas.user import UserOut, Token, UserCreate

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={401: {"description": "Ошибка авторизации"}},
)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Эндпоинт для получения JWT токена"""
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserOut)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверяем, что пользователь с таким логином или email не существует
    existing_user = (
        db.query(User)
        .filter((User.login == user_data.login) | (User.email == user_data.email))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином или email уже существует",
        )

    # Создаем нового пользователя
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        login=user_data.login,
        email=user_data.email,
        password=hashed_password,
        role="student",  # По умолчанию обычный пользователь
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user=Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return current_user
