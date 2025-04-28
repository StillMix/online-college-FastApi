from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.user import UserOut

# Настройки безопасности
SECRET_KEY = (
    "вашсекретныйключдляjwt"  # В реальном проекте должен быть безопасно сохранен
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 день

# Инструменты для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def verify_password(plain_password, hashed_password):
    """Проверяет соответствие пароля хешу"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Создает хеш пароля"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    """Аутентифицирует пользователя по логину и паролю"""
    # Ищем пользователя по логину или email
    user = (
        db.query(User)
        .filter((User.login == username) | (User.email == username))
        .first()
    )

    if not user:
        return False

    if not verify_password(password, user.password):
        return False

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT токен с данными пользователя"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    """Получает текущего пользователя по токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    """Проверяет, что пользователь активен"""
    return current_user
