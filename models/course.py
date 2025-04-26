from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

# Связь многие-ко-многим между разделами и уроками
lesson_section = Table(
    "lesson_sections",
    Base.metadata,
    Column("section_id", String, ForeignKey("sections.id"), primary_key=True),
    Column("lesson_id", String, ForeignKey("lessons.id"), primary_key=True),
)


class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    subtitle = Column(String)
    type = Column(String)
    timetoendL = Column(String)
    color = Column(String)
    icon = Column(String)
    icontype = Column(String)
    titleForCourse = Column(String)

    # Отношения
    info = relationship(
        "CourseInfo", back_populates="course", cascade="all, delete-orphan"
    )
    sections = relationship(
        "Section", back_populates="course", cascade="all, delete-orphan"
    )


class CourseInfo(Base):
    __tablename__ = "course_info"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    subtitle = Column(Text)
    course_id = Column(String, ForeignKey("courses.id"))

    # Отношения
    course = relationship("Course", back_populates="info")


class Section(Base):
    __tablename__ = "sections"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    course_id = Column(String, ForeignKey("courses.id"))

    content = relationship(
        "Lesson",
        secondary=lesson_section,
        back_populates="sections", 
    )

    course = relationship("Course", back_populates="sections")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    passing = Column(String)
    description = Column(Text, nullable=True)

    sections = relationship(
        "Section", secondary=lesson_section, back_populates="content"
    )
