from typing import List, Optional
from pydantic import BaseModel, Field

# Схемы для уроков
class LessonBase(BaseModel):
    id: str
    name: str
    passing: str = "no"
    description: Optional[str] = None

class LessonCreate(LessonBase):
    pass

class Lesson(LessonBase):
    class Config:
        orm_mode = True

# Схемы для разделов курса
class SectionBase(BaseModel):
    id: str
    name: str
    content: List[LessonBase]

class SectionCreate(SectionBase):
    pass

class Section(SectionBase):
    class Config:
        orm_mode = True

# Схемы для информации о курсе
class CourseInfoBase(BaseModel):
    id: str
    title: str
    subtitle: str

class CourseInfoCreate(CourseInfoBase):
    pass

class CourseInfo(CourseInfoBase):
    class Config:
        orm_mode = True

# Схемы для курсов
class CourseBase(BaseModel):
    title: str
    subtitle: str
    type: str
    timetoendL: str
    color: str = "#a63cf9"
    icon: str
    icontype: str
    titleForCourse: str

class CourseCreate(CourseBase):
    info: List[CourseInfoCreate]
    course: List[SectionCreate]  # Здесь называем "course" для совместимости с фронтендом

class CourseUpdate(CourseBase):
    info: List[CourseInfoCreate]
    course: List[SectionCreate]  # Здесь называем "course" для совместимости с фронтендом

class Course(CourseBase):
    id: str
    info: List[CourseInfo]
    course: List[Section] = Field(..., alias="sections")  # Если в ORM это называется sections

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

# Схема для ответа с списком курсов
class CourseList(BaseModel):
    courses: List[Course]