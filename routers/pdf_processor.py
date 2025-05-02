import io
import re
import pdfplumber
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from models.course import Course, CourseInfo, Section, Lesson
from database import get_db
from schemas.course import CourseCreate, CourseInfoCreate, SectionCreate, LessonCreate
import uuid

router = APIRouter(
    prefix="/api/pdf",
    tags=["pdf_processor"],
    responses={404: {"description": "Не найдено"}},
)


@router.post("/preview")
async def preview_main_sections_from_pdf(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Файл должен быть PDF")

    try:
        # Определяем текущее время для названия
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        course_title = f"{file.filename} - {timestamp}"

        print(f"Получен файл: {file.filename}")
        content = await file.read()

        print("Извлекаем текст из PDF...")
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            page_texts = [page.extract_text() or "" for page in pdf.pages]
            full_text = "\n".join(page_texts)
            print(f"Текст извлечен. Количество страниц: {len(pdf.pages)}")

        # Паттерны для разделов и подразделов
        main_section_pattern = (
            r"^\s*(\d{1,3})[\.\-]?\s+([А-ЯЁA-Z\s]+(?:[А-ЯЁA-Z0-9\s\-]+)*)$"
        )
        sub_section_pattern = r"^\s*(\d+(?:\.\d+)+)[\.\-]?\s+(.+)$"

        print("Начинаем поиск главных разделов...")
        main_sections = re.findall(main_section_pattern, full_text, re.MULTILINE)
        print(f"Найдено {len(main_sections)} главных разделов.")

        print("Начинаем поиск подразделов...")
        sub_section_matches = list(
            re.finditer(sub_section_pattern, full_text, re.MULTILINE)
        )
        print(f"Найдено {len(sub_section_matches)} подразделов.")

        # Собираем основные разделы
        unique_sections = {}
        for num, title in main_sections:
            title = title.strip()
            if len(title.replace(" ", "")) > 2:
                # Генерация уникального ID для раздела
                unique_sections[num] = {
                    "id": f"section_{uuid.uuid4().hex}",
                    "title": title,
                    "subsections": [],
                }
        print(f"Основные разделы обработаны. Количество: {len(unique_sections)}")

        # Обрабатываем подразделы с текстом и фильтром только заглавных
        for i, match in enumerate(sub_section_matches):
            num = match.group(1)
            title = match.group(2).strip()
            # Фильтр: только заглавные заголовки
            if title != title.upper():
                continue
            # Определяем текст подраздела до следующего подраздела
            start_idx = match.start()
            end_idx = (
                sub_section_matches[i + 1].start()
                if i + 1 < len(sub_section_matches)
                else len(full_text)
            )
            section_text = full_text[start_idx:end_idx].strip()

            main_section_num = num.split(".")[0]
            if main_section_num in unique_sections:
                unique_sections[main_section_num]["subsections"].append(
                    {"num": num, "title": title, "text": section_text}
                )

        # Сортировка разделов и подразделов
        sorted_sections = sorted(unique_sections.items(), key=lambda x: int(x[0]))
        for _, sec in sorted_sections:
            sec["subsections"].sort(
                key=lambda x: list(map(int, x["num"].split(".")))
            )  # Сортировка подразделов

        print("Сортировка завершена. Готовим результат.")

        # Формирование результата
        result = {
            "title": course_title,
            "subtitle": "Базовый курс для начинающих программистов",
            "type": "ПРОГРАММИРОВАНИЕ",
            "timetoendL": "С НУЛЯ",
            "color": "#2d82b7",
            "icon": "",
            "icontype": "programIcon",
            "titleForCourse": course_title,
            "info": [],
            "sections": [],  # Меняем с "course" на "sections"
        }

        # Наполняем результат разделами и подразделами
        for num, sec in sorted_sections:
            section_data = {
                "id": sec["id"],  # Используем уникальный ID для раздела
                "name": sec["title"],
                "content": [],
            }

            for subsection in sec["subsections"]:
                subsection_data = {
                    "id": f"content_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}",
                    "name": subsection["title"],
                    "passing": "no",
                    "description": subsection["text"],
                }
                section_data["content"].append(subsection_data)

            result["sections"].append(section_data)  # Меняем с "course" на "sections"

        # Создание нового курса в базе данных
        # Генерируем уникальный ID для курса
        course_id = str(uuid.uuid4())

        # Создаем курс в базе данных
        db_course = Course(
            id=course_id,
            title=course_title,
            subtitle="Базовый курс для начинающих программистов",
            type="ПРОГРАММИРОВАНИЕ",
            timetoendL="С НУЛЯ",
            color="#2d82b7",
            icon="",
            icontype="programIcon",
            titleForCourse=course_title,
        )
        db.add(db_course)
        db.flush()  # Необходимо для получения ID курса

        # Создаем разделы и уроки
        for section_data in result["sections"]:
            db_section = Section(
                id=section_data["id"],
                name=section_data["name"],
                course_id=course_id,
            )
            db.add(db_section)
            db.flush()

            # Создаем уроки для этого раздела
            for content_item in section_data["content"]:
                db_lesson = Lesson(
                    id=content_item["id"],
                    name=content_item["name"],
                    passing=content_item["passing"],
                    description=content_item["description"],
                )
                db.add(db_lesson)
                db.flush()

                # Связываем урок с разделом
                db_section.content.append(db_lesson)

        db.commit()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при чтении PDF: {str(e)}")


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
