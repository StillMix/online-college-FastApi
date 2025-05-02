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
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    extract_toc: bool = True,
    create_lessons: bool = True,
    extract_content: bool = True,
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
        page_texts = {}  # Тексты по страницам для извлечения содержимого

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            full_text += page_text
            page_texts[page_num] = page_text

        # Находим структуру с помощью регулярных выражений для извлечения заголовков разных уровней
        main_sections = re.findall(r"^\s*(\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE)
        sub_sections = re.findall(
            r"^\s*(\d+\.\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE
        )
        sub_sub_sections = re.findall(
            r"^\s*(\d+\.\d+\.\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE
        )

        # Собираем все заголовки для последующего извлечения контента
        all_headings = main_sections + sub_sections + sub_sub_sections
        all_headings.sort(key=lambda x: x[0])  # Сортируем по номеру раздела

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

        # Создаем разделы и словарь для отслеживания связей
        sections = []
        section_map = {}  # Для связывания разделов с их идентификаторами
        lessons_count = 0

        # Создаем основные разделы
        for section_id, section_name in main_sections:
            section_uuid = str(uuid.uuid4())
            section = SectionCreate(id=section_uuid, name=section_name)
            sections.append(section)
            section_map[section_id] = section_uuid

        # Собираем уроки для каждого раздела
        section_lessons = {section_id: [] for section_id, _ in main_sections}

        # Добавляем подсекции как уроки
        for subsection_id, subsection_name in sub_sections:
            main_id = subsection_id.split(".")[0]
            if main_id in section_map:
                lesson_uuid = str(uuid.uuid4())

                # Ищем текст урока, если extract_content=True
                lesson_description = f"Урок по теме: {subsection_name}"
                if extract_content:
                    # Поиск контента для урока (упрощенная версия)
                    # Здесь должен быть более сложный алгоритм для извлечения текста между заголовками
                    pattern = f"{subsection_id}\\s+{re.escape(subsection_name)}\\s+(.*?)(?=\\d+\\.\\d+|\\d+\\.|$)"
                    content_match = re.search(pattern, full_text, re.DOTALL)
                    if content_match:
                        lesson_description = content_match.group(1).strip()

                lesson = {
                    "id": lesson_uuid,
                    "name": subsection_name,
                    "passing": "no",
                    "description": lesson_description,
                }
                section_lessons[main_id].append(lesson)

        # Также добавляем подподсекции как уроки
        for subsubsection_id, subsubsection_name in sub_sub_sections:
            main_id = subsubsection_id.split(".")[0]
            if main_id in section_map:
                lesson_uuid = str(uuid.uuid4())

                # Ищем текст урока
                lesson_description = f"Урок по теме: {subsubsection_name}"
                if extract_content:
                    pattern = f"{subsubsection_id}\\s+{re.escape(subsubsection_name)}\\s+(.*?)(?=\\d+\\.\\d+\\.\\d+|\\d+\\.\\d+|\\d+\\.|$)"
                    content_match = re.search(pattern, full_text, re.DOTALL)
                    if content_match:
                        lesson_description = content_match.group(1).strip()

                lesson = {
                    "id": lesson_uuid,
                    "name": subsubsection_name,
                    "passing": "no",
                    "description": lesson_description,
                }
                section_lessons[main_id].append(lesson)

        course_data.sections = sections

        # Создаем курс в базе данных
        from services.course import create_course

        db_course = create_course(db, course_data)

        # Создаем уроки и связываем их с разделами
        if create_lessons:
            from services.course import create_course_lesson

            lessons_count = 0

            for section_id, section_name in main_sections:
                section_uuid = section_map[section_id]

                # Создаем уроки из подразделов
                for lesson_data in section_lessons[section_id]:
                    create_course_lesson(db, db_course.id, section_uuid, lesson_data)
                    lessons_count += 1

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
