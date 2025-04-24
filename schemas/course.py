from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Схемы для информации о курсе
class CourseInfoBase(BaseModel):
    title: str
    subtitle: str

class CourseInfoCreate(CourseInfoBase):
    pass

class CourseInfoUpdate(CourseInfoBase):
    pass

class CourseInfo(CourseInfoBase):
    id: int
    course_id: int
    
    class Config:
        from_attributes = True

# Схемы для уроков
class LessonBase(BaseModel):
    order_id: str
    name: str
    description: Optional[str] = None
    passing: str = "no"

class LessonCreate(LessonBase):
    pass

class LessonUpdate(LessonBase):
    pass

class Lesson(LessonBase):
    id: int
    section_id: int
    
    class Config:
        from_attributes = True

# Схемы для разделов курса
class CourseSectionBase(BaseModel):
    order_id: str
    name: str

class CourseSectionCreate(CourseSectionBase):
    lessons: List[LessonCreate]

class CourseSectionUpdate(CourseSectionBase):
    lessons: Optional[List[LessonUpdate]] = None

class CourseSection(CourseSectionBase):
    id: int
    course_id: int
    lessons: List[Lesson]
    
    class Config:
        from_attributes = True

# Схемы для курсов
class CourseBase(BaseModel):
    title: str
    subtitle: str
    type: str
    timetoendL: str
    color: str
    icon: str
    icontype: str
    titleForCourse: str

class CourseCreate(CourseBase):
    info: List[CourseInfoCreate]
    sections: List[CourseSectionCreate]

class CourseUpdate(CourseBase):
    info: Optional[List[CourseInfoUpdate]] = None
    sections: Optional[List[CourseSectionUpdate]] = None

class Course(CourseBase):
    id: int
    created_at: datetime
    info: List[CourseInfo]
    sections: List[CourseSection]
    
    class Config:
        from_attributes = True