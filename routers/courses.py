from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from schemas.course import CourseCreate, CourseUpdate, Course as CourseSchema
from services.courses import (
    create_course,
    get_course_by_id,
    get_all_courses,
    update_course,
    delete_course,
)

router = APIRouter()


@router.post("/", response_model=CourseSchema, status_code=status.HTTP_201_CREATED)
async def create_course_endpoint(
    course: CourseCreate, db: AsyncSession = Depends(get_db)
):
    """
    Создание нового курса
    """
    return await create_course(db, course)


@router.get("/", response_model=List[CourseSchema])
async def read_courses(db: AsyncSession = Depends(get_db)):
    """
    Получение всех курсов
    """
    return await get_all_courses(db)


@router.get("/{course_id}", response_model=CourseSchema)
async def read_course(course_id: int, db: AsyncSession = Depends(get_db)):
    """
    Получение курса по ID
    """
    db_course = await get_course_by_id(db, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return db_course


@router.put("/{course_id}", response_model=CourseSchema)
async def update_course_endpoint(
    course_id: int, course_update: CourseUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Обновление курса
    """
    db_course = await get_course_by_id(db, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return await update_course(db, db_course, course_update)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_endpoint(course_id: int, db: AsyncSession = Depends(get_db)):
    """
    Удаление курса
    """
    db_course = await get_course_by_id(db, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")
    await delete_course(db, db_course)
    return None
