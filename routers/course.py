from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Body,
)
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json

from database import get_db
from models.course import Course, CourseInfo, Section, Lesson
from schemas.course import (
    Course as CourseSchema,
    CourseCreate,
    CourseUpdate,
    CourseInfo as CourseInfoSchema,
    CourseInfoCreate,
    Section as SectionSchema,
    SectionCreate,
    Lesson as LessonSchema,
    LessonCreate,
)
from services.course import (
    get_courses,
    get_course,
    create_course,
    update_course,
    delete_course,
    save_course_image,
    update_lesson_description,
    create_course_info,
    create_course_section,
    create_lesson,
)

router = APIRouter(
    prefix="/api/courses",
    tags=["courses"],
    responses={404: {"description": "Не найдено"}},
)


# Роуты для курсов
@router.get("/", response_model=List[CourseSchema])
async def read_courses(db: Session = Depends(get_db)):
    """Получить список всех курсов"""
    return get_courses(db)


@router.get("/{course_id}", response_model=CourseSchema)
async def read_course(course_id: str, db: Session = Depends(get_db)):
    """Получить информацию о конкретном курсе по ID"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return db_course


@router.post("/", response_model=CourseSchema)
async def create_new_course(course: CourseCreate, db: Session = Depends(get_db)):
    """Создать новый курс"""
    return create_course(db=db, course=course)


@router.put("/{course_id}", response_model=CourseSchema)
async def update_existing_course(
    course_id: str, course: CourseUpdate, db: Session = Depends(get_db)
):
    """Обновить существующий курс"""
    return update_course(db=db, course_id=course_id, course=course)


@router.delete("/{course_id}")
async def delete_existing_course(course_id: str, db: Session = Depends(get_db)):
    """Удалить курс"""
    return delete_course(db=db, course_id=course_id)


# Роуты для загрузки изображений
@router.post("/{course_id}/upload-image")
async def upload_course_image(
    course_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Загрузить изображение для курса"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файл должен быть изображением")

    result = await save_course_image(course_id, file)

    db_course.icon = result["path"]
    db.commit()
    db.refresh(db_course)

    return result


# Роуты для информации о курсе
@router.post("/{course_id}/info/", response_model=CourseInfoSchema)
async def create_course_info_endpoint(
    course_id: str, info: CourseInfoCreate, db: Session = Depends(get_db)
):
    """Создать блок информации о курсе"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    return create_course_info(db, course_id, info)


@router.put("/{course_id}/info/{info_id}", response_model=CourseInfoSchema)
async def update_course_info_endpoint(
    course_id: str, info_id: str, info: CourseInfoCreate, db: Session = Depends(get_db)
):
    """Обновить блок информации о курсе"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_info = (
        db.query(CourseInfo)
        .filter(CourseInfo.id == info_id, CourseInfo.course_id == course_id)
        .first()
    )

    if db_info is None:
        raise HTTPException(status_code=404, detail="Информация о курсе не найдена")

    db_info.title = info.title
    db_info.subtitle = info.subtitle

    db.commit()
    db.refresh(db_info)

    return db_info


@router.delete("/{course_id}/info/{info_id}")
async def delete_course_info_endpoint(
    course_id: str, info_id: str, db: Session = Depends(get_db)
):
    """Удалить блок информации о курсе"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_info = (
        db.query(CourseInfo)
        .filter(CourseInfo.id == info_id, CourseInfo.course_id == course_id)
        .first()
    )

    if db_info is None:
        raise HTTPException(status_code=404, detail="Информация о курсе не найдена")

    db.delete(db_info)
    db.commit()

    return {"detail": f"Информация о курсе с ID {info_id} успешно удалена"}


# Роуты для разделов курса
@router.post("/{course_id}/sections/", response_model=SectionSchema)
async def create_section_endpoint(
    course_id: str, section: SectionCreate, db: Session = Depends(get_db)
):
    """Создать раздел для курса"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    return create_course_section(db, course_id, section)


@router.put("/{course_id}/sections/{section_id}", response_model=SectionSchema)
async def update_section_endpoint(
    course_id: str,
    section_id: str,
    section: SectionCreate,
    db: Session = Depends(get_db),
):
    """Обновить раздел курса"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db_section.name = section.name
    db.commit()
    db.refresh(db_section)

    return db_section


@router.delete("/{course_id}/sections/{section_id}")
async def delete_section_endpoint(
    course_id: str, section_id: str, db: Session = Depends(get_db)
):
    """Удалить раздел курса"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db.delete(db_section)
    db.commit()

    return {"detail": f"Раздел с ID {section_id} успешно удален"}


# Роуты для уроков
@router.post("/{course_id}/sections/{section_id}/content", response_model=LessonSchema)
async def create_lesson_endpoint(
    course_id: str, section_id: str, lesson: LessonCreate, db: Session = Depends(get_db)
):
    """Создать урок для раздела курса"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db_lesson = Lesson(
        id=lesson.id,
        name=lesson.name,
        passing=lesson.passing,
        description=lesson.description,
    )

    db.add(db_lesson)
    db.flush()

    db_section.lessons.append(db_lesson)

    db.commit()
    db.refresh(db_lesson)

    return db_lesson


@router.put(
    "/{course_id}/sections/{section_id}/content/{lesson_id}",
    response_model=LessonSchema,
)
async def update_lesson_endpoint(
    course_id: str,
    section_id: str,
    lesson_id: str,
    lesson: LessonCreate,
    db: Session = Depends(get_db),
):
    """Обновить урок в разделе курса"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if db_lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")

    db_lesson.name = lesson.name
    db_lesson.passing = lesson.passing
    if lesson.description:
        db_lesson.description = lesson.description

    db.commit()
    db.refresh(db_lesson)

    return db_lesson


@router.delete("/{course_id}/sections/{section_id}/content/{lesson_id}")
async def delete_lesson_endpoint(
    course_id: str, section_id: str, lesson_id: str, db: Session = Depends(get_db)
):
    """Удалить урок из раздела курса"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if db_lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")

    db_section.lessons.remove(db_lesson)
    db.delete(db_lesson)
    db.commit()

    return {"detail": f"Урок с ID {lesson_id} успешно удален"}


# Роуты для описания урока
@router.put(
    "/{course_id}/sections/{section_id}/content/{lesson_id}/description",
    response_model=LessonSchema,
)
async def update_lesson_description_endpoint(
    course_id: str,
    section_id: str,
    lesson_id: str,
    description: Dict[str, str] = Body(...),
    db: Session = Depends(get_db),
):
    """Обновить описание урока"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if db_lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")

    if "description" in description:
        db_lesson.description = description["description"]
        db.commit()
        db.refresh(db_lesson)

        return {
            "id": db_lesson.id,
            "name": db_lesson.name,
            "passing": db_lesson.passing,
            "description": db_lesson.description or "",
        }
    else:
        raise HTTPException(status_code=400, detail="Поле 'description' обязательно")


@router.delete("/{course_id}/sections/{section_id}/content/{lesson_id}/description")
async def delete_lesson_description_endpoint(
    course_id: str, section_id: str, lesson_id: str, db: Session = Depends(get_db)
):
    """Удалить описание урока"""
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if db_lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")

    db_lesson.description = None
    db.commit()

    return {"detail": f"Описание урока с ID {lesson_id} успешно удалено"}
