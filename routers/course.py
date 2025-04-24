from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import get_db
from models.course import Course
from schemas.course import Course as CourseSchema, CourseCreate, CourseUpdate
from services.course import get_courses, get_course, create_course, update_course, delete_course, save_course_image

router = APIRouter(
    prefix="/api/courses",
    tags=["courses"],
    responses={404: {"description": "Не найдено"}},
)

@router.get("/", response_model=List[CourseSchema])
def read_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Получить список всех курсов
    """
    courses = get_courses(db, skip=skip, limit=limit)
    return courses

@router.get("/{course_id}", response_model=CourseSchema)
def read_course(course_id: int, db: Session = Depends(get_db)):
    """
    Получить информацию о конкретном курсе по ID
    """
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return db_course

@router.post("/", response_model=CourseSchema)
def create_new_course(course: CourseCreate, db: Session = Depends(get_db)):
    """
    Создать новый курс
    """
    return create_course(db=db, course=course)

@router.put("/{course_id}", response_model=CourseSchema)
def update_existing_course(course_id: int, course: CourseUpdate, db: Session = Depends(get_db)):
    """
    Обновить существующий курс
    """
    return update_course(db=db, course_id=course_id, course=course)

@router.delete("/{course_id}")
def delete_existing_course(course_id: int, db: Session = Depends(get_db)):
    """
    Удалить курс
    """
    return delete_course(db=db, course_id=course_id)

@router.post("/{course_id}/upload-image")
async def upload_course_image(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загрузить изображение для курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    # Проверяем, что файл - изображение
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файл должен быть изображением")
    
    # Сохраняем изображение
    result = await save_course_image(course_id, file)
    
    # Обновляем путь к иконке в базе данных, если имя файла соответствует icon
    if "icon" in file.filename.lower():
        db_course.icon = result["path"]
        db.commit()
    
    return result

@router.post("/{course_id}/upload-with-data")
async def upload_course_with_data(
    course_id: int,
    file: UploadFile = File(...),
    course_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Загрузить изображение вместе с данными о курсе
    """
    # Парсим данные курса из JSON
    try:
        course_data_dict = json.loads(course_data)
        course_update = CourseUpdate(**course_data_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Некорректные данные курса: {str(e)}")
    
    # Обновляем курс
    db_course = update_course(db=db, course_id=course_id, course=course_update)
    
    # Сохраняем изображение
    result = await save_course_image(course_id, file)
    
    # Обновляем путь к иконке в базе данных
    if "icon" in file.filename.lower():
        db_course.icon = result["path"]
        db.commit()
        db.refresh(db_course)
    
    return {
        "course": db_course,
        "uploaded_file": result
    }