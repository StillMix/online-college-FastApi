from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from models.course import Course, CourseInfo, CourseSection, Lesson
from schemas.course import CourseCreate, CourseUpdate

async def create_course(db: AsyncSession, course: CourseCreate) -> Course:
    """
    Создание нового курса со всеми связанными данными
    """
    # Создаем основную запись курса
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
    await db.flush()  # Получаем ID курса перед сохранением деталей
    
    # Добавляем информацию о курсе
    for info_item in course.info:
        db_info = CourseInfo(
            course_id=db_course.id,
            title=info_item.title,
            subtitle=info_item.subtitle
        )
        db.add(db_info)
    
    # Добавляем разделы и уроки
    for section in course.sections:
        db_section = CourseSection(
            course_id=db_course.id,
            order_id=section.order_id,
            name=section.name
        )
        db.add(db_section)
        await db.flush()  # Получаем ID раздела
        
        # Добавляем уроки для раздела
        for lesson in section.lessons:
            db_lesson = Lesson(
                section_id=db_section.id,
                order_id=lesson.order_id,
                name=lesson.name,
                description=lesson.description,
                passing=lesson.passing
            )
            db.add(db_lesson)
    
    await db.commit()
    await db.refresh(db_course)
    
    # Загружаем полные данные курса со всеми отношениями
    result = await db.execute(
        select(Course)
        .where(Course.id == db_course.id)
        .options(
            selectinload(Course.info),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
    )
    return result.scalar_one()

async def get_all_courses(db: AsyncSession) -> List[Course]:
    """
    Получение всех курсов с информацией
    """
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.info),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
    )
    return result.scalars().all()

async def get_course_by_id(db: AsyncSession, course_id: int) -> Optional[Course]:
    """
    Получение курса по ID со всеми связанными данными
    """
    result = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.info),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
    )
    return result.scalar_one_or_none()

async def update_course(
    db: AsyncSession, course: Course, course_update: CourseUpdate
) -> Course:
    """
    Обновление курса и всех связанных данных
    """
    # Обновляем основные поля курса
    for key, value in course_update.dict(exclude={"info", "sections"}).items():
        setattr(course, key, value)
    
    # Если есть обновления для info, обрабатываем их
    if course_update.info is not None:
        # Удаляем существующие записи
        await db.execute(
            sql_delete(CourseInfo).where(CourseInfo.course_id == course.id)
        )
        
        # Создаем новые записи
        for info_item in course_update.info:
            db_info = CourseInfo(
                course_id=course.id,
                title=info_item.title,
                subtitle=info_item.subtitle
            )
            db.add(db_info)
    
    # Если есть обновления для разделов, обрабатываем их
    if course_update.sections is not None:
        # Получаем существующие разделы для обновления или удаления
        existing_sections = {
            section.order_id: section for section in course.sections
        }
        
        # Обрабатываем каждый раздел из обновления
        for section_update in course_update.sections:
            if section_update.order_id in existing_sections:
                # Обновляем существующий раздел
                db_section = existing_sections[section_update.order_id]
                db_section.name = section_update.name
                
                # Если есть обновления для уроков, обрабатываем их
                if section_update.lessons is not None:
                    # Удаляем существующие уроки
                    await db.execute(
                        sql_delete(Lesson).where(Lesson.section_id == db_section.id)
                    )
                    
                    # Создаем новые уроки
                    for lesson in section_update.lessons:
                        db_lesson = Lesson(
                            section_id=db_section.id,
                            order_id=lesson.order_id,
                            name=lesson.name,
                            description=lesson.description,
                            passing=lesson.passing
                        )
                        db.add(db_lesson)
            else:
                # Создаем новый раздел
                db_section = CourseSection(
                    course_id=course.id,
                    order_id=section_update.order_id,
                    name=section_update.name
                )
                db.add(db_section)
                await db.flush()  # Получаем ID раздела
                
                # Создаем уроки для нового раздела
                if section_update.lessons:
                    for lesson in section_update.lessons:
                        db_lesson = Lesson(
                            section_id=db_section.id,
                            order_id=lesson.order_id,
                            name=lesson.name,
                            description=lesson.description,
                            passing=lesson.passing
                        )
                        db.add(db_lesson)
        
        # Удаляем разделы, которых нет в обновлении
        update_order_ids = {section.order_id for section in course_update.sections}
        for order_id, section in existing_sections.items():
            if order_id not in update_order_ids:
                await db.delete(section)
    
    await db.commit()
    await db.refresh(course)
    
    # Загружаем обновленные данные курса
    result = await db.execute(
        select(Course)
        .where(Course.id == course.id)
        .options(
            selectinload(Course.info),
            selectinload(Course.sections).selectinload(CourseSection.lessons)
        )
    )
    return result.scalar_one()

async def delete_course(db: AsyncSession, course: Course) -> None:
    """
    Удаление курса и всех связанных данных
    """
    await db.delete(course)
    await db.commit()