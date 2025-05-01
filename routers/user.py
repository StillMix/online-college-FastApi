from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from models.user import User
from models.course import Lesson
from schemas.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    SendVerificationCode,
    UserCourse,
    LessonCompletion,
)
from database import SessionLocal, get_db
import os
import shutil
from random import randint
from utils import send_email
from models.VerificationCode import VerificationCode
from typing import List
from pathlib import Path
from services.auth import get_password_hash

router = APIRouter(prefix="/api/users", tags=["users"])

# Создаем директорию для аватарок, если не существует
BASE_DIR = Path(__file__).resolve().parent.parent
USERS_AVATAR_DIR = BASE_DIR / "UsersAvatar"
USERS_AVATAR_DIR.mkdir(exist_ok=True)


@router.post("/confirm_email/")
def confirm_email(
    user_data: dict,
    db: Session = Depends(get_db),
):
    # Извлекаем данные из JSON
    email = user_data.get("email")
    verification_code = user_data.get("verification_code")
    login = user_data.get("login")
    password = user_data.get("password")

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

    # Хешируем пароль
    hashed_password = get_password_hash(password)

    # Создаем пользователя
    db_user = User(email=email, login=login, password=hashed_password, role="student")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Удаляем код после успешной регистрации
    db.delete(db_verification)
    db.commit()

    return {"message": "User registered successfully", "user": db_user}


@router.post("/confirm_email/")
def confirm_email(
    user_data: dict,
    db: Session = Depends(get_db),
):
    # Извлекаем данные из JSON
    email = user_data.get("email")
    verification_code = user_data.get("verification_code")
    login = user_data.get("login")
    password = user_data.get("password")

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
    db_user = User(email=email, login=login, password=password, role="student")
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

    # Вместо отправки email, просто возвращаем код в ответе
    # Это только для разработки, в продакшене так делать не следует!
    try:
        # Попытка отправить email (для совместимости)
        send_email(data.email, verification_code)
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        print(f"Error sending email: {str(e)}")

    # Возвращаем код напрямую для разработки
    return {
        "message": "Verification code sent to your email",
        "code": verification_code,  # Только для разработки!
    }


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Обновляем только переданные поля
    user_data_dict = user_data.dict(exclude_unset=True)

    # Особая обработка для email, если он был передан
    if "email" in user_data_dict and user_data_dict["email"] != db_user.email:
        verification_code = str(randint(1000, 9999))
        send_email(user_data_dict["email"], verification_code)

    # Обновляем все переданные поля
    for key, value in user_data_dict.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Удаляем пользователя из БД
    db.delete(db_user)
    db.commit()

    # Удаляем директорию с аватаром пользователя при наличии
    user_avatar_dir = USERS_AVATAR_DIR / str(user_id)
    if user_avatar_dir.exists():
        shutil.rmtree(user_avatar_dir)

    return {"message": f"User with ID {user_id} successfully deleted"}


# Роут для добавления курса пользователю
@router.post("/course")
def add_user_course(user_course: UserCourse, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    db_user = db.query(User).filter(User.id == user_course.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Здесь можно добавить логику для проверки существования курса
    # и добавления в таблицу связей пользователь-курс

    # Создаем запись в БД (здесь нужно создать модель связи)
    # db_user_course = UserCourseModel(user_id=user_course.user_id, course_id=user_course.course_id)
    # db.add(db_user_course)
    # db.commit()

    # Пока просто возвращаем успешный ответ
    return {
        "message": f"Course {user_course.course_id} added to user {user_course.user_id}"
    }


# Роут для отметки урока как пройденного
@router.post("/lesson/complete")
def complete_lesson(completion: LessonCompletion, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    db_user = db.query(User).filter(User.id == completion.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем существование урока
    db_lesson = db.query(Lesson).filter(Lesson.id == completion.lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Обновляем статус прохождения
    db_lesson.passing = "yes"
    db.commit()

    return {
        "message": f"Lesson {completion.lesson_id} marked as completed for user {completion.user_id}"
    }


@router.post("/{user_id}/avatar")
async def upload_avatar(
    user_id: int, avatar: UploadFile = File(...), db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Создаем директорию для аватара пользователя
    user_avatar_dir = USERS_AVATAR_DIR / str(user_id)
    user_avatar_dir.mkdir(exist_ok=True, parents=True)

    # Получаем расширение файла
    file_extension = os.path.splitext(avatar.filename)[1]
    avatar_path = user_avatar_dir / f"avatar{file_extension}"

    # Сохраняем файл
    with avatar_path.open("wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)

    # Обновляем путь к аватару в БД
    db_user.img = f"UsersAvatar/{user_id}/avatar{file_extension}"
    db.commit()
    db.refresh(db_user)

    return {"message": "Avatar uploaded successfully", "img_path": db_user.img}
