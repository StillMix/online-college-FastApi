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


# Изменим функцию extract_course_from_pdf в файле routers/pdf_processor.py
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
        # Основные разделы и подразделы до 6 уровня вложенности
        main_sections = re.findall(r"^\s*(\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE)
        sub_sections = re.findall(
            r"^\s*(\d+\.\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE
        )
        sub_sub_sections = re.findall(
            r"^\s*(\d+\.\d+\.\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE
        )
        level4_sections = re.findall(
            r"^\s*(\d+\.\d+\.\d+\.\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE
        )
        level5_sections = re.findall(
            r"^\s*(\d+\.\d+\.\d+\.\d+\.\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE
        )
        level6_sections = re.findall(
            r"^\s*(\d+\.\d+\.\d+\.\d+\.\d+\.\d+)\.?\s+([^\n]+)", full_text, re.MULTILINE
        )

        # Ищем также элементы введения (обычно в начале документа)
        intro_sections = re.findall(
            r"^\s*(Введение|Предисловие|Вступление|Аннотация)[\s\.]*(.*?)$",
            full_text,
            re.MULTILINE,
        )

        # Ищем заголовки с типичной структурой, но без номеров
        unnumbered_sections = re.findall(
            r"^\s*([A-ZА-ЯЁ][A-ZА-ЯЁa-zа-яё\s]{2,})$", full_text, re.MULTILINE
        )

        # Собираем все заголовки для последующего извлечения контента
        all_headings = (
            main_sections
            + sub_sections
            + sub_sub_sections
            + level4_sections
            + level5_sections
            + level6_sections
        )

        # Создаем словарь для быстрого доступа к заголовкам по их идентификаторам
        heading_dict = {id: name for id, name in all_headings}

        # Сортируем заголовки для правильного определения содержимого
        all_headings.sort(
            key=lambda x: [
                int(n) if n.isdigit() else float(n)
                for n in x[0].replace(".", ".0").split(".")
            ]
        )

        # Создаем структуру курса
        course_id = str(uuid.uuid4())
        course_title = file.filename.split(".")[0]
        if main_sections and len(main_sections) > 0:
            course_title = main_sections[0][1]
        elif intro_sections and len(intro_sections) > 0:
            course_title = intro_sections[0][0] + " " + intro_sections[0][1]

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
        processed_ids = set()  # Для отслеживания уже использованных ID

        # Создаем раздел "Введение", если нашли информацию о нем
        if intro_sections:
            intro_uuid = str(uuid.uuid4())
            intro_section = SectionCreate(id=intro_uuid, name="Введение")
            sections.append(intro_section)
            section_map["0"] = intro_uuid  # Используем "0" как ID для введения

            # Создаем уроки для введения
            intro_lessons = []
            for i, (title, content) in enumerate(intro_sections):
                lesson_uuid = str(uuid.uuid4())
                processed_ids.add(lesson_uuid)
                lesson_name = f"{title} {content}" if content else title
                intro_lessons.append(
                    {
                        "id": lesson_uuid,
                        "name": lesson_name[:50],  # Ограничиваем длину имени
                        "passing": "no",
                        "description": f"<h2>{title}</h2><p>{content}</p>",
                    }
                )

            # Также добавляем ненумерованные заголовки в раздел введения
            for i, title in enumerate(
                unnumbered_sections[:3]
            ):  # Ограничиваем количество
                lesson_uuid = str(uuid.uuid4())
                processed_ids.add(lesson_uuid)
                intro_lessons.append(
                    {
                        "id": lesson_uuid,
                        "name": title[:50],  # Ограничиваем длину имени
                        "passing": "no",
                        "description": f"<h3>{title}</h3>",
                    }
                )

            section_lessons = {"0": intro_lessons}
        else:
            section_lessons = {}

        # Создаем основные разделы
        for section_id, section_name in main_sections:
            section_uuid = str(uuid.uuid4())
            section = SectionCreate(id=section_uuid, name=section_name)
            sections.append(section)
            section_map[section_id] = section_uuid
            section_lessons[section_id] = []

        # Функция для извлечения текста между заголовками
        def extract_text_between(start_id, start_name, level):
            start_pattern = f"{re.escape(start_id)}.?\\s+{re.escape(start_name)}"

            # Ищем следующий заголовок того же или более высокого уровня
            next_patterns = []
            if level == 1:  # Для основных разделов
                next_patterns.append(r"(\d+)\.?\s+([^\n]+)")
            elif level == 2:  # Для подразделов
                next_patterns.append(r"(\d+\.\d+)\.?\s+([^\n]+)")
                next_patterns.append(r"(\d+)\.?\s+([^\n]+)")
            elif level == 3:  # Для подподразделов
                next_patterns.append(r"(\d+\.\d+\.\d+)\.?\s+([^\n]+)")
                next_patterns.append(r"(\d+\.\d+)\.?\s+([^\n]+)")
                next_patterns.append(r"(\d+)\.?\s+([^\n]+)")
            elif level >= 4:  # Для всех остальных уровней
                for i in range(level, 0, -1):
                    pattern = r"(\d+" + r"\.\d+" * (i - 1) + r")\.?\s+([^\n]+)"
                    next_patterns.append(pattern)

            # Создаем паттерн для поиска
            content_pattern = f"{start_pattern}(.*?)(?:"
            for i, pat in enumerate(next_patterns):
                if i > 0:
                    content_pattern += "|"
                content_pattern += f"(?:{pat})"
            content_pattern += "|$)"

            content_match = re.search(content_pattern, full_text, re.DOTALL)

            if content_match:
                content = content_match.group(1).strip()
                # Обрабатываем контент - удаляем лишние пробелы, переносы строк и т.д.
                content = re.sub(r"\s+", " ", content)
                # Форматируем как HTML
                return f"<h2>{start_name}</h2><div class='content'>{content}</div>"
            else:
                return f"<h2>{start_name}</h2>"

        # Добавляем подсекции как уроки ко всем основным разделам
        for subsection_id, subsection_name in sub_sections:
            main_id = subsection_id.split(".")[0]
            if main_id in section_map:
                # Генерация уникального ID
                lesson_uuid = str(uuid.uuid4())
                processed_ids.add(lesson_uuid)

                # Ищем текст урока с улучшенным алгоритмом
                lesson_description = ""
                if extract_content:
                    lesson_description = extract_text_between(
                        subsection_id, subsection_name, 2
                    )

                lesson = {
                    "id": lesson_uuid,
                    "name": subsection_name,
                    "passing": "no",
                    "description": lesson_description,
                }
                section_lessons[main_id].append(lesson)

        # Обрабатываем более глубокие уровни заголовков (3-6)
        # Каждый заголовок становится отдельным уроком
        for deeper_sections, level in [
            (sub_sub_sections, 3),
            (level4_sections, 4),
            (level5_sections, 5),
            (level6_sections, 6),
        ]:
            for section_id, section_name in deeper_sections:
                main_id = section_id.split(".")[0]  # Получаем первый уровень

                if main_id in section_map:
                    # Создаем новый урок для этого заголовка
                    lesson_uuid = str(uuid.uuid4())
                    processed_ids.add(lesson_uuid)

                    # Ищем текст урока
                    lesson_description = ""
                    if extract_content:
                        lesson_description = extract_text_between(
                            section_id, section_name, level
                        )

                    # Создаем урок с соответствующим уровнем вложенности в заголовке
                    lesson = {
                        "id": lesson_uuid,
                        "name": section_name,
                        "passing": "no",
                        "description": lesson_description,
                    }

                    # Добавляем урок к соответствующему разделу первого уровня
                    section_lessons[main_id].append(lesson)

        course_data.sections = sections

        # Создаем курс в базе данных
        from services.course import create_course

        db_course = create_course(db, course_data)

        # Создаем уроки и связываем их с разделами
        if create_lessons:
            from services.course import create_course_lesson

            lessons_count = 0

            for section_id in section_lessons:
                if section_id in section_map:
                    section_uuid = section_map[section_id]

                    # Создаем уроки
                    for lesson_data in section_lessons[section_id]:
                        try:
                            # Проверяем, что ID не является дубликатом
                            # Поскольку processed_ids это множество (set), а не список,
                            # просто проверяем наличие ID в множестве
                            if lesson_data["id"] in processed_ids:
                                # Если ID уже использовался, генерируем новый
                                lesson_data["id"] = str(uuid.uuid4())

                            create_course_lesson(
                                db, db_course.id, section_uuid, lesson_data
                            )
                            lessons_count += 1
                        except Exception as e:
                            print(f"Ошибка при создании урока: {str(e)}")
                            continue

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
