from pydantic import BaseModel
from typing import List, Optional


class LessonBase(BaseModel):
    id: str
    name: str
    passing: str
    description: Optional[str] = None


class LessonCreate(LessonBase):
    pass


class Lesson(LessonBase):
    class Config:
        orm_mode = True


class SectionBase(BaseModel):
    id: str
    name: str


class SectionCreate(SectionBase):
    pass


class Section(SectionBase):
    content: List[Lesson] = []

    class Config:
        orm_mode = True


class CourseInfoBase(BaseModel):
    id: str
    title: str
    subtitle: str


class CourseInfoCreate(CourseInfoBase):
    pass


class CourseInfo(CourseInfoBase):
    class Config:
        orm_mode = True


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
    id: Optional[str] = None
    info: List[CourseInfoCreate] = []
    sections: List[SectionCreate] = []


class CourseUpdate(CourseBase):
    id: Optional[str] = None
    info: Optional[List[CourseInfoCreate]] = None
    sections: Optional[List[SectionCreate]] = None


class Course(CourseBase):
    id: str
    info: List[CourseInfo] = []
    sections: List[Section] = []

    class Config:
        orm_mode = True
