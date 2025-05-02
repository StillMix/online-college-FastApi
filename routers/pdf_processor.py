# routers/pdf_processor.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
import PyPDF2
import re
import io
import uuid
from models.course import Course, CourseInfo, Section, Lesson
from database import get_db
from schemas.course import CourseCreate, CourseInfoCreate, SectionCreate, LessonCreate

router = APIRouter(
    prefix="/api/pdf",
    tags=["pdf_processor"],
    responses={404: {"description": "Не найдено"}},
)


@router.post("/extract_course")
async def extract_course_from_pdf(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """
    Извлекает структуру курса из PDF-файла и создает соответствующие записи в базе данных
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате PDF")

    try:
        # Читаем PDF файл
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

        # Извлекаем текст
        full_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            full_text += page.extract_text()

        # Находим структуру с помощью регулярных выражений
        # Это базовый пример, который потребует доработки для вашего формата PDF
        main_sections = re.findall(r"(\d+)\.\s+([^\n]+)", full_text)
        sub_sections = re.findall(r"(\d+\.\d+)\s+([^\n]+)", full_text)

        # Создаем структуру курса
        course_id = str(uuid.uuid4())
        course_title = main_sections[0][1] if main_sections else "Новый курс из PDF"

        course_data = CourseCreate(
            id=course_id,
            title=course_title,
            subtitle="Курс, импортированный из PDF",
            type="ДРУГОЕ",
            timetoendL="В СОБСТВЕННОМ ТЕМПЕ",
            color="#2d82b7",
            icon="",
            icontype="programIcon",
            titleForCourse=f"Курс создан автоматически из PDF-файла: {file.filename}",
            info=[],
            sections=[],
        )

        # Создаем разделы и уроки на основе структуры PDF
        sections = []
        lessons_data = []  # Для хранения данных об уроках и их связях с разделами

        for section_id, section_name in main_sections:
            section_uuid = str(uuid.uuid4())
            section = SectionCreate(id=section_uuid, name=section_name)
            sections.append(section)

            # Находим подразделы для текущего раздела
            related_subsections = [
                s for s in sub_sections if s[0].startswith(section_id + ".")
            ]

            # Создаем уроки из подразделов
            for subsection_id, subsection_name in related_subsections:
                lesson_uuid = str(uuid.uuid4())
                lesson = LessonCreate(
                    id=lesson_uuid,
                    name=subsection_name,
                    passing="no",
                    description=f"Урок по теме: {subsection_name}",
                )
                lessons_data.append((section_uuid, lesson))

        course_data.sections = sections

        # Создаем курс в базе данных
        from services.course import create_course, create_lesson

        db_course = create_course(db, course_data)

        # Создаем уроки и связываем их с разделами
        for section_uuid, lesson in lessons_data:
            create_lesson(db, section_uuid, lesson)

        # Подсчитываем общее количество уроков
        lessons_count = len(lessons_data)

        return {
            "message": "Курс успешно создан из PDF",
            "course_id": db_course.id,
            "title": db_course.title,
            "sections_count": len(sections),
            "lessons_count": lessons_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при обработке PDF: {str(e)}"
        )
