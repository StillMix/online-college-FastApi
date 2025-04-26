from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException
import uuid

from models.course import Course, CourseInfo, Section, Lesson
from schemas.course import CourseCreate, CourseUpdate, Course as CourseSchema

# Директория для изображений
BASE_DIR = Path(__file__).resolve().parent.parent
COURSE_IMG_DIR = BASE_DIR / "CourseImg"


def get_courses(db: Session, skip: int = 0, limit: int = 100) -> List[Course]:
    """Получить список курсов с пагинацией"""
    return db.query(Course).offset(skip).limit(limit).all()


def get_course(db: Session, course_id: str) -> Optional[Course]:
    """Получить курс по ID"""
    return db.query(Course).filter(Course.id == course_id).first()


def create_course(db: Session, course: CourseCreate) -> Dict[str, Any]:
    """Создать новый курс"""
    # Генерация нового ID, если не предоставлен
    if not course.id:
        # Генерируем ID на основе количества курсов или используем UUID
        existing_courses = db.query(Course).count()
        course_id = str(existing_courses + 1)
    else:
        course_id = course.id

    # Создаем запись курса
    db_course = Course(
        id=course_id,
        title=course.title,
        subtitle=course.subtitle,
        type=course.type,
        timetoendL=course.timetoendL,
        color=course.color,
        icon=course.icon,
        icontype=course.icontype,
        titleForCourse=course.titleForCourse,
    )
    db.add(db_course)
    db.flush()

    # Создаем директорию для изображений курса
    course_img_dir = COURSE_IMG_DIR / course_id
    course_img_dir.mkdir(exist_ok=True)

    # Добавляем информацию о курсе
    for info_item in course.info:
        db_info = CourseInfo(
            id=info_item.id,
            title=info_item.title,
            subtitle=info_item.subtitle,
            course_id=course_id,
        )
        db.add(db_info)

    # Добавляем разделы и уроки курса
    for section_item in course.course:
        db_section = Section(
            id=section_item.id,
            name=section_item.name,
            course_id=course_id,
        )
        db.add(db_section)
        db.flush()

        # Добавляем уроки к разделу
        for lesson_item in section_item.content:
            db_lesson = Lesson(
                id=lesson_item.id,
                name=lesson_item.name,
                passing=lesson_item.passing,
                description=lesson_item.description,
            )
            db.add(db_lesson)
            db.flush()

            # Связываем урок и раздел
            db_section.lessons.append(db_lesson)

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
        "icon": db_course.icon or "",
        "icontype": db_course.icontype,
        "titleForCourse": db_course.titleForCourse,
        "info": [
            {"id": info.id, "title": info.title, "subtitle": info.subtitle}
            for info in db_course.info
        ],
        "course": [],  # Используем "course" вместо "sections" для совместимости с фронтендом
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


def update_course(db: Session, course_id: str, course: CourseUpdate) -> Dict[str, Any]:
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

    if course.icon:
        db_course.icon = course.icon

    # Удаляем старую информацию о курсе
    db.query(CourseInfo).filter(CourseInfo.course_id == course_id).delete()

    # Добавляем новую информацию
    for info_item in course.info:
        db_info = CourseInfo(
            id=info_item.id,
            title=info_item.title,
            subtitle=info_item.subtitle,
            course_id=course_id,
        )
        db.add(db_info)

    # Получаем все существующие разделы для курса
    existing_sections = db.query(Section).filter(Section.course_id == course_id).all()

    # Собираем ID всех уроков из этих разделов
    lessons_to_delete = []
    for section in existing_sections:
        lessons_to_delete.extend([lesson.id for lesson in section.lessons])

    # Удаляем старые разделы
    for section in existing_sections:
        db.delete(section)

    # Удаляем старые уроки
    if lessons_to_delete:
        db.query(Lesson).filter(Lesson.id.in_(lessons_to_delete)).delete(
            synchronize_session="fetch"
        )

    # Добавляем новые разделы и уроки
    for section_item in course.course:
        db_section = Section(
            id=section_item.id,
            name=section_item.name,
            course_id=course_id,
        )
        db.add(db_section)
        db.flush()

        # Добавляем уроки к разделу
        for lesson_item in section_item.content:
            db_lesson = Lesson(
                id=lesson_item.id,
                name=lesson_item.name,
                passing=lesson_item.passing,
                description=lesson_item.description,
            )
            db.add(db_lesson)
            db.flush()

            # Связываем урок и раздел
            db_section.lessons.append(db_lesson)

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
        "icon": db_course.icon or "",
        "icontype": db_course.icontype,
        "titleForCourse": db_course.titleForCourse,
        "info": [
            {"id": info.id, "title": info.title, "subtitle": info.subtitle}
            for info in db_course.info
        ],
        "course": [],  # Используем "course" вместо "sections"
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


def delete_course(db: Session, course_id: str) -> Dict[str, str]:
    """Удалить курс"""
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Удаляем директорию с изображениями курса
    course_img_dir = COURSE_IMG_DIR / course_id
    if course_img_dir.exists():
        shutil.rmtree(course_img_dir)

    db.delete(db_course)
    db.commit()
    return {"detail": f"Курс с ID {course_id} успешно удален"}


async def save_course_image(course_id: str, file: UploadFile) -> Dict[str, str]:
    """Сохранить изображение для курса"""
    # Создаем директорию для изображений конкретного курса
    course_img_dir = COURSE_IMG_DIR / course_id
    course_img_dir.mkdir(exist_ok=True)

    # Получаем расширение файла
    file_extension = ""
    if file.filename and "." in file.filename:
        file_extension = file.filename.split(".")[-1]

    # Формируем новое имя файла: icon-{course_id}.{extension}
    new_filename = f"icon-{course_id}.{file_extension}"

    # Путь для сохранения файла
    file_path = course_img_dir / new_filename

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Возвращаем относительный путь к файлу (для использования в веб-приложении)
    relative_path = f"CourseImg/{course_id}/{new_filename}"
    return {"filename": new_filename, "path": relative_path}


def update_lesson_passing(db: Session, lesson_id: str, passing: str) -> Dict[str, Any]:
    """Обновить статус прохождения урока"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")

    lesson.passing = passing
    db.commit()
    db.refresh(lesson)

    return {
        "id": lesson.id,
        "name": lesson.name,
        "passing": lesson.passing,
        "description": lesson.description or "",
    }


def update_lesson_description(
    db: Session, lesson_id: str, description: str
) -> Dict[str, Any]:
    """Обновить описание урока"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")

    lesson.description = description
    db.commit()
    db.refresh(lesson)

    return {
        "id": lesson.id,
        "name": lesson.name,
        "passing": lesson.passing,
        "description": lesson.description or "",
    }
