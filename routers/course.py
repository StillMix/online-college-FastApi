from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Body,
    Query,
)
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from database import get_db
from models.course import Course
from schemas.course import Course as CourseSchema, CourseCreate, CourseUpdate
from services.course import (
    get_courses,
    get_course,
    create_course,
    update_course,
    delete_course,
    save_course_image,
    update_lesson_passing,
    update_lesson_description,
)

router = APIRouter(
    prefix="/api/courses",
    tags=["courses"],
    responses={404: {"description": "Не найдено"}},
)


@router.get("/", response_model=List[CourseSchema])
async def read_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Получить список всех курсов
    """
    courses = get_courses(db, skip=skip, limit=limit)
    return courses


@router.get("/{course_id}", response_model=CourseSchema)
async def read_course(course_id: str, db: Session = Depends(get_db)):
    """
    Получить информацию о конкретном курсе по ID
    """
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return db_course


@router.post("/", response_model=CourseSchema)
async def create_new_course(course: CourseCreate, db: Session = Depends(get_db)):
    """
    Создать новый курс
    """
    return create_course(db=db, course=course)


@router.post("/{course_id}/sections/", response_model=Section)
async def create_course_section(
    course_id: str, section: SectionCreate, db: Session = Depends(get_db)
):
    """
    Создать раздел для курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Создаем раздел
    db_section = Section(id=section.id, name=section.name, course_id=course_id)

    db.add(db_section)
    db.commit()
    db.refresh(db_section)

    # Создаем контент раздела, если он есть
    for lesson_item in section.content:
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
    db.refresh(db_section)

    return db_section


@router.delete("/{course_id}/sections/{section_id}")
async def delete_course_section(
    course_id: str, section_id: str, db: Session = Depends(get_db)
):
    """
    Удалить раздел курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Ищем раздел
    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    # Удаляем раздел
    db.delete(db_section)
    db.commit()

    return {"detail": f"Раздел с ID {section_id} успешно удален"}


@router.put("/{course_id}/sections/{section_id}", response_model=Section)
async def update_course_section(
    course_id: str,
    section_id: str,
    section: SectionCreate,
    db: Session = Depends(get_db),
):
    """
    Обновить раздел курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Ищем раздел
    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    # Обновляем раздел
    db_section.name = section.name
    db.commit()

    return db_section


@router.post("/{course_id}/sections/", response_model=Section)
async def create_course_section(
    course_id: str, section: SectionCreate, db: Session = Depends(get_db)
):
    """
    Создать раздел для курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Создаем раздел
    db_section = Section(id=section.id, name=section.name, course_id=course_id)

    db.add(db_section)
    db.commit()
    db.refresh(db_section)

    # Создаем контент раздела, если он есть
    for lesson_item in section.content:
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
    db.refresh(db_section)

    return db_section


@router.delete("/{course_id}/sections/{section_id}")
async def delete_course_section(
    course_id: str, section_id: str, db: Session = Depends(get_db)
):
    """
    Удалить раздел курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Ищем раздел
    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    # Удаляем раздел
    db.delete(db_section)
    db.commit()

    return {"detail": f"Раздел с ID {section_id} успешно удален"}


@router.put("/{course_id}/sections/{section_id}", response_model=Section)
async def update_course_section(
    course_id: str,
    section_id: str,
    section: SectionCreate,
    db: Session = Depends(get_db),
):
    """
    Обновить раздел курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Ищем раздел
    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    # Обновляем раздел
    db_section.name = section.name
    db.commit()

    return db_section


@router.post("/{course_id}/sections/{section_id}/content", response_model=Lesson)
async def create_lesson(
    course_id: str, section_id: str, lesson: LessonCreate, db: Session = Depends(get_db)
):
    """
    Создать урок для раздела курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Ищем раздел
    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    # Создаем урок
    db_lesson = Lesson(
        id=lesson.id,
        name=lesson.name,
        passing=lesson.passing,
        description=lesson.description,
    )

    db.add(db_lesson)
    db.flush()

    # Связываем урок и раздел
    db_section.lessons.append(db_lesson)

    db.commit()
    db.refresh(db_lesson)

    return db_lesson


@router.delete("/{course_id}/sections/{section_id}/content/{lesson_id}")
async def delete_lesson(
    course_id: str, section_id: str, lesson_id: str, db: Session = Depends(get_db)
):
    """
    Удалить урок из раздела курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Ищем раздел
    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    # Ищем урок
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if db_lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")

    # Удаляем урок из раздела
    db_section.lessons.remove(db_lesson)

    # Удаляем урок из базы данных
    db.delete(db_lesson)
    db.commit()

    return {"detail": f"Урок с ID {lesson_id} успешно удален"}


@router.put(
    "/{course_id}/sections/{section_id}/content/{lesson_id}", response_model=Lesson
)
async def update_lesson(
    course_id: str,
    section_id: str,
    lesson_id: str,
    lesson: LessonCreate,
    db: Session = Depends(get_db),
):
    """
    Обновить урок в разделе курса
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Ищем раздел
    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    # Ищем урок
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if db_lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")

    # Обновляем урок
    db_lesson.name = lesson.name
    db_lesson.passing = lesson.passing

    db.commit()
    db.refresh(db_lesson)

    return db_lesson


@router.put("/{course_id}/sections/{section_id}/content/{lesson_id}/description")
async def update_lesson_description_endpoint(
    course_id: str,
    section_id: str,
    lesson_id: str,
    description: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Обновить описание урока
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Ищем раздел
    db_section = (
        db.query(Section)
        .filter(Section.id == section_id, Section.course_id == course_id)
        .first()
    )

    if db_section is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    # Ищем урок
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if db_lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")

    # Обновляем описание урока
    if "description" in description:
        return update_lesson_description(db, lesson_id, description["description"])
    else:
        raise HTTPException(status_code=400, detail="Поле 'description' обязательно")


@router.put("/{course_id}", response_model=CourseSchema)
async def update_existing_course(
    course_id: str, course: CourseUpdate, db: Session = Depends(get_db)
):
    """
    Обновить существующий курс
    """
    return update_course(db=db, course_id=course_id, course=course)


@router.delete("/{course_id}")
async def delete_existing_course(course_id: str, db: Session = Depends(get_db)):
    """
    Удалить курс
    """
    return delete_course(db=db, course_id=course_id)


@router.post("/{course_id}/upload-image")
async def upload_course_image(
    course_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)
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

    # Обновляем путь к иконке в базе данных
    db_course.icon = result["path"]
    db.commit()
    db.refresh(db_course)

    return result


@router.patch("/{course_id}/lessons/{lesson_id}/passing")
async def update_lesson_passing_status(
    course_id: str,
    lesson_id: str,
    passing: str = Query(..., description="Статус прохождения урока: 'yes' или 'no'"),
    db: Session = Depends(get_db),
):
    """
    Обновить статус прохождения урока
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Проверяем значение passing
    if passing not in ["yes", "no"]:
        raise HTTPException(
            status_code=400, detail="Значение passing должно быть 'yes' или 'no'"
        )

    # Обновляем статус прохождения
    return update_lesson_passing(db, lesson_id, passing)


@router.patch("/{course_id}/lessons/{lesson_id}/description")
async def update_lesson_description_content(
    course_id: str,
    lesson_id: str,
    description: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """
    Обновить описание урока
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Обновляем описание урока
    return update_lesson_description(db, lesson_id, description)


@router.post("/{course_id}/upload-with-data")
async def upload_image_with_course_data(
    course_id: str,
    file: UploadFile = File(...),
    course_data: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Загрузить изображение вместе с данными о курсе
    """
    # Проверяем, существует ли курс
    db_course = get_course(db, course_id=course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    # Проверяем, что файл - изображение
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файл должен быть изображением")

    # Парсим данные курса
    try:
        course_dict = json.loads(course_data)
        course = CourseUpdate(**course_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка в данных курса: {str(e)}")

    # Сохраняем изображение
    result = await save_course_image(course_id, file)

    # Добавляем путь к изображению в данные курса
    course.icon = result["path"]

    # Обновляем курс
    updated_course = update_course(db, course_id, course)

    return updated_course
