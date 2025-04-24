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
    # Создаем запись курса с явным ID
    new_id = str(len(get_courses(db)) + 1)  # Генерируем новый ID как строку

    db_course = Course(
        id=new_id,  # Явно устанавливаем ID
        title=course.title,
        subtitle=course.subtitle,
        type=course.type,
        timetoendL=course.timetoendL,
        color=course.color,
        icon=course.icon if course.icon else None,
        icontype=course.icontype,
        titleForCourse=course.titleForCourse,
    )
    db.add(db_course)
    db.flush()

    # Используем ID напрямую, так как мы его уже установили
    course_id_str = new_id

    # Создаем директорию для изображений курса
    course_img_dir = COURSE_IMG_DIR / course_id_str
    course_img_dir.mkdir(exist_ok=True)

    # Добавляем информацию о курсе
    for index, info_item in enumerate(course.info):
        unique_info_id = f"{course_id_str}_{index + 1}"

        db_info = CourseInfo(
            id=unique_info_id,
            title=info_item.title,
            subtitle=info_item.subtitle,
            course_id=course_id_str,
        )
        db.add(db_info)

    # Добавляем разделы и уроки курса
    sections = []
    for section_index, section_item in enumerate(course.course):
        section_id = f"{course_id_str}_section_{section_index + 1}"

        db_section = Section(
            id=section_id, name=section_item.name, course_id=course_id_str
        )
        db.add(db_section)
        db.flush()

        # Добавляем уроки к разделу
        for lesson_index, lesson_item in enumerate(section_item.content):
            lesson_id = f"{course_id_str}_lesson_{section_index + 1}_{lesson_index + 1}"

            db_lesson = Lesson(
                id=lesson_id,
                name=lesson_item.name,
                passing=lesson_item.passing,
                description=lesson_item.description,
            )
            db.add(db_lesson)
            db.flush()

            # Связываем урок и раздел
            db_section.lessons.append(db_lesson)

        # Сохраняем содержимое уроков для каждого раздела
        db_section.content = section_item.content

        sections.append(db_section)

    db_course.sections = sections

    db.commit()
    db.refresh(db_course)

    # Преобразуем объект course для соответствия схеме
    result = {
        "id": db_course.id,
        "title": db_course.title,
        "subtitle": db_course.subtitle,
        "type": db_course.type,
        "timetoendL": db_course.timetoendL,
        "color": db_course.color,
        "icon": db_course.icon or "",  # Гарантируем, что icon не None
        "icontype": db_course.icontype,
        "titleForCourse": db_course.titleForCourse,
        "info": [
            {"id": info.id, "title": info.title, "subtitle": info.subtitle}
            for info in db_course.info
        ],
        "course": [],  # Вместо sections, используем course
    }

    # Преобразуем разделы и уроки
    for section in db_course.sections:
        section_data = {"id": section.id, "name": section.name, "content": []}

        for lesson in section.lessons:
            lesson_data = {
                "id": lesson.id,
                "name": lesson.name,
                "passing": lesson.passing,
                "description": lesson.description or "",
            }
            section_data["content"].append(lesson_data)

        result["course"].append(section_data)

    return result


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
    db_course.icontype = course.icontype
    db_course.titleForCourse = course.titleForCourse

    # Удаляем старую информацию о курсе и добавляем новую
    db.query(CourseInfo).filter(CourseInfo.course_id == course_id).delete()
    for info_item in course.info:
        db_info = CourseInfo(
            title=info_item.title, subtitle=info_item.subtitle, course_id=db_course.id
        )
        db.add(db_info)

    # Удаляем старые разделы и уроки
    for section in db_course.sections:
        for lesson in section.lessons:
            db.delete(lesson)
        db.delete(section)

    # Добавляем новые разделы и уроки
    for section_item in course.course:
        db_section = Section(name=section_item.name, course_id=db_course.id)
        db.add(db_section)
        db.flush()

        for lesson_item in section_item.content:
            db_lesson = Lesson(
                name=lesson_item.name,
                passing=lesson_item.passing,
                description=lesson_item.description,
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

    # Получаем расширение файла
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""

    # Формируем новое имя файла: icon-{course_id}.{extension}
    new_filename = f"icon-{course_id}.{file_extension}"

    # Путь для сохранения файла
    file_path = course_img_dir / new_filename

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Возвращаем относительный путь к файлу (для использования в веб-приложении)
    relative_path = f"CourseImg/{course_id}/{new_filename}"
    return {"filename": new_filename, "path": relative_path}