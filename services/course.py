from sqlalchemy.orm import Session
import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException

from models.course import Course, CourseInfo, Section, Lesson
from schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseInfoCreate,
    SectionCreate,
    LessonCreate,
)


def get_courses(db: Session):
    """Получить все курсы"""
    return db.query(Course).all()


def get_course(db: Session, course_id: str):
    """Получить конкретный курс по ID"""
    return db.query(Course).filter(Course.id == course_id).first()


def create_course(db: Session, course: CourseCreate):
    """Создать новый курс"""
    # Если ID не предоставлен, генерируем его
    if not course.id:
        course.id = str(uuid.uuid4())

    db_course = Course(
        id=course.id,
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
    db.flush()  # Необходимо для получения ID курса

    # Создаем информацию о курсе
    for info_item in course.info:
        db_info = CourseInfo(
            id=info_item.id,
            title=info_item.title,
            subtitle=info_item.subtitle,
            course_id=db_course.id,
        )
        db.add(db_info)

    # Создаем разделы курса
    for section_item in course.sections:
        db_section = Section(
            id=section_item.id,
            name=section_item.name,
            course_id=db_course.id,
        )
        db.add(db_section)

    db.commit()
    db.refresh(db_course)
    return db_course


def update_course(db: Session, course_id: str, course: CourseUpdate):
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

    db.commit()
    db.refresh(db_course)
    return db_course


def delete_course(db: Session, course_id: str):
    """Удалить курс"""
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db.delete(db_course)
    db.commit()
    return {"detail": f"Курс с ID {course_id} успешно удален"}


async def save_course_image(course_id: str, file: UploadFile):
    """Сохранить изображение курса"""
    # Создаем директорию для изображений курса
    COURSE_IMG_DIR = Path(__file__).resolve().parent.parent / "CourseImg"
    course_dir = COURSE_IMG_DIR / str(course_id)
    course_dir.mkdir(exist_ok=True, parents=True)

    # Получаем расширение файла
    file_extension = os.path.splitext(file.filename or "")[1]
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = course_dir / file_name

    # Сохраняем файл
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Возвращаем путь к файлу относительно корня приложения
    relative_path = f"CourseImg/{course_id}/{file_name}"
    return {"path": relative_path}


def create_course_info(db: Session, course_id: str, info: CourseInfoCreate):
    """Создать блок информации о курсе"""
    db_info = CourseInfo(
        id=info.id,
        title=info.title,
        subtitle=info.subtitle,
        course_id=course_id,
    )
    db.add(db_info)
    db.commit()
    db.refresh(db_info)
    return db_info


def create_course_section(db: Session, course_id: str, section: SectionCreate):
    """Создать раздел курса"""
    db_section = Section(
        id=section.id,
        name=section.name,
        course_id=course_id,
    )
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


def create_lesson(db: Session, section_id: str, lesson: LessonCreate):
    """Создать урок для раздела курса"""
    db_lesson = Lesson(
        id=lesson.id,
        name=lesson.name,
        passing=lesson.passing,
        description=lesson.description,
    )
    db.add(db_lesson)
    db.flush()

    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        db.rollback()
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db_section.lessons.append(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def update_lesson_description(db: Session, lesson_id: str, description: str):
    """Обновить описание урока"""
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")

    db_lesson.description = description
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def create_course_lesson(
    db: Session, course_id: str, section_id: str, lesson_data: dict
):
    """Создать урок для раздела курса"""
    db_lesson = Lesson(
        id=lesson_data.get("id", str(uuid.uuid4())),
        name=lesson_data.get("name", "Новый урок"),
        passing=lesson_data.get("passing", "no"),
        description=lesson_data.get("description", ""),
    )
    db.add(db_lesson)
    db.flush()

    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        db.rollback()
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db_section.content.append(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson
