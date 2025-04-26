from typing import List, Optional
from pydantic import BaseModel, Field


# Схемы для уроков
class LessonBase(BaseModel):
    name: str
    passing: str = "no"
    description: Optional[str] = None


class LessonCreate(LessonBase):
    id: str


class Lesson(LessonBase):
    id: str

    class Config:
        orm_mode = True
        from_attributes = True


# Схемы для разделов курса
class SectionBase(BaseModel):
    name: str


class SectionCreate(SectionBase):
    id: str
    content: List[LessonCreate]


class Section(SectionBase):
    id: str
    content: List[Lesson]

    class Config:
        orm_mode = True
        from_attributes = True


# Схемы для информации о курсе
class CourseInfoBase(BaseModel):
    title: str
    subtitle: str


class CourseInfoCreate(CourseInfoBase):
    id: str


class CourseInfo(CourseInfoBase):
    id: str

    class Config:
        orm_mode = True
        from_attributes = True


# Схемы для курсов
class CourseBase(BaseModel):
    title: str
    subtitle: str
    type: str
    timetoendL: str
    color: str = "#a63cf9"
    icontype: str
    titleForCourse: str


class CourseCreate(CourseBase):
    id: Optional[str] = None
    icon: Optional[str] = None
    info: List[CourseInfoCreate]
    course: List[
        SectionCreate
    ]  # Здесь называем "course" для совместимости с фронтендом


class CourseUpdate(CourseBase):
    icon: Optional[str] = None
    info: List[CourseInfoCreate]
    course: List[SectionCreate]


class Course(CourseBase):
    id: str
    icon: Optional[str] = None
    info: List[CourseInfo]
    course: List[Section] = Field(
        ..., alias="sections"
    )  # Переименовываем для совместимости

    class Config:
        orm_mode = True
        from_attributes = True
        allow_population_by_field_name = True
