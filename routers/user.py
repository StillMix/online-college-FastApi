from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserUpdate, UserOut, SendVerificationCode
from database import SessionLocal
import os
import shutil
from random import randint
from utils import send_email
from models.VerificationCode import VerificationCode
from typing import List

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/confirm_email/")
def confirm_email(
    email: str,
    verification_code: str,
    login: str,
    password: str,
    db: Session = Depends(get_db),
):
    # Проверяем, существует ли запись с этим email и кодом
    db_verification = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.email == email, VerificationCode.code == verification_code
        )
        .first()
    )

    if not db_verification:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Создаем пользователя
    db_user = User(email=email, login=login, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Удаляем код после успешной регистрации
    db.delete(db_verification)
    db.commit()

    return {"message": "User registered successfully", "user": db_user}


@router.post("/send_verification_code/")
def send_verification_code(data: SendVerificationCode, db: Session = Depends(get_db)):
    # Проверяем, не зарегистрирован ли уже пользователь с таким email
    db_user = db.query(User).filter(User.email == data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Генерация кода для подтверждения
    verification_code = str(randint(1000, 9999))

    # Сохраняем код в базе данных временно
    db_verification = VerificationCode(email=data.email, code=verification_code)
    db.add(db_verification)
    db.commit()

    # Отправка кода на email
    send_email(data.email, verification_code)

    return {"message": "Verification code sent to your email"}


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Обновление email и отправка кода на новый email, если он изменен
    if user.email and user.email != db_user.email:
        verification_code = str(randint(1000, 9999))
        send_email(user.email, verification_code)
        db_user.email = user.email

    if user.login:
        db_user.login = user.login
    if user.password:
        db_user.password = user.password
    if user.img:
        img_path = f"/userimgs/{db_user.id}/"
        os.makedirs(img_path, exist_ok=True)
        with open(os.path.join(img_path, "profile_img.jpg"), "wb") as img_file:
            img_file.write(user.img)
        db_user.img = f"{img_path}/profile_img.jpg"
    if user.name:
        db_user.name = user.name

    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/users/", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
