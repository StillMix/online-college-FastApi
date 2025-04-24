from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException

from models.course import Course, CourseInfo, Section, Lesson
from schemas.course import CourseCreate, CourseUpdate

# Директория для изображений
BASE_DIR = Path(__file__).resolve().parent.parent
COURSE_IMG_DIR = BASE_DIR / "CourseImg"

def get_courses(db: Session, skip: int = 0, limit: int = 100):
    """Получить список курсов с пагинацией"""
    return db.query(Course).offset(skip).limit(limit).all()

def get_course(db: Session, course_id: int):
    """Получить курс по ID"""
    return db.query(Course).filter(Course.id == course_id).first()

def create_course(db: Session, course: CourseCreate):
    """Создать новый курс"""
    # Создаем запись курса
    db_course = Course(
        title=course.title,
        subtitle=course.subtitle,
        type=course.type,
        timetoendL=course.timetoendL,
        color=course.color,
        icon=course.icon,
        icontype=course.icontype,
        titleForCourse=course.titleForCourse
    )
    db.add(db_course)
    db.flush()  # Получаем ID для курса перед добавлением связанных объектов
    
    # Создаем директорию для изображений курса
    course_img_dir = COURSE_IMG_DIR / str(db_course.id)
    course_img_dir.mkdir(exist_ok=True)
    
    # Добавляем информацию о курсе
    for info_item in course.info:
        db_info = CourseInfo(
            title=info_item.title,
            subtitle=info_item.subtitle,
            course_id=db_course.id
        )
        db.add(db_info)
    
    # Добавляем разделы и уроки курса
    for section_item in course.course:
        db_section = Section(
            name=section_item.name,
            course_id=db_course.id
        )
        db.add(db_section)
        db.flush()  # Получаем ID для раздела
        
        # Добавляем уроки к разделу
        for lesson_item in section_item.content:
            db_lesson = Lesson(
                name=lesson_item.name,
                passing=lesson_item.passing,
                description=lesson_item.description
            )
            db.add(db_lesson)
            db.flush()  # Получаем ID для урока
            
            # Связываем урок и раздел
            db_section.lessons.append(db_lesson)
    
    db.commit()
    db.refresh(db_course)
    return db_course

def update_course(db: Session, course_id: int, course: CourseUpdate):
    """Обновить существующий курс"""
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    # Обновляем основные поля курса
    db_course.title = course.title
    db_course.subtitle = course.subtitle
    db_course.type = course.type
    db_course.timetoendL = course.timetoendL
    db_course.color = course.color
    db_course.icon = course.icon
    db_course.icontype = course.icontype
    db_course.titleForCourse = course.titleForCourse
    
    # Удаляем старую информацию о курсе и добавляем новую
    db.query(CourseInfo).filter(CourseInfo.course_id == course_id).delete()
    for info_item in course.info:
        db_info = CourseInfo(
            title=info_item.title,
            subtitle=info_item.subtitle,
            course_id=db_course.id
        )
        db.add(db_info)
    
    # Удаляем старые разделы и уроки
    for section in db_course.sections:
        for lesson in section.lessons:
            db.delete(lesson)
        db.delete(section)
    
    # Добавляем новые разделы и уроки
    for section_item in course.course:
        db_section = Section(
            name=section_item.name,
            course_id=db_course.id
        )
        db.add(db_section)
        db.flush()
        
        for lesson_item in section_item.content:
            db_lesson = Lesson(
                name=lesson_item.name,
                passing=lesson_item.passing,
                description=lesson_item.description
            )
            db.add(db_lesson)
            db.flush()
            
            db_section.lessons.append(db_lesson)
    
    db.commit()
    db.refresh(db_course)
    return db_course

def delete_course(db: Session, course_id: int):
    """Удалить курс"""
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    # Удаляем директорию с изображениями курса
    course_img_dir = COURSE_IMG_DIR / str(course_id)
    if course_img_dir.exists():
        shutil.rmtree(course_img_dir)
    
    db.delete(db_course)
    db.commit()
    return {"detail": f"Курс с ID {course_id} успешно удален"}

async def save_course_image(course_id: int, file: UploadFile):
    """Сохранить изображение для курса"""
    # Создаем директорию для изображений конкретного курса
    course_img_dir = COURSE_IMG_DIR / str(course_id)
    course_img_dir.mkdir(exist_ok=True)
    
    # Путь для сохранения файла
    file_path = course_img_dir / file.filename
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Возвращаем относительный путь к файлу (для использования в веб-приложении)
    relative_path = f"CourseImg/{course_id}/{file.filename}"
    return {"filename": file.filename, "path": relative_path}