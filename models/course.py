from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

# Связующая таблица для разделов и контента
lesson_sections = Table(
    "lesson_sections",
    Base.metadata,
    Column("section_id", String(255), ForeignKey("sections.id"), primary_key=True),
    Column("lesson_id", String(255), ForeignKey("lessons.id"), primary_key=True),
)


class Course(Base):
    __tablename__ = "courses"

    id = Column(String(255), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    timetoendL = Column(String(50), nullable=False)
    color = Column(String(50), nullable=False, default="#a63cf9")
    icon = Column(String(255), nullable=True)
    icontype = Column(String(255), nullable=False)
    titleForCourse = Column(String(255), nullable=False)

    # Связи с другими таблицами
    info = relationship(
        "CourseInfo", back_populates="course", cascade="all, delete-orphan"
    )
    sections = relationship(
        "Section", back_populates="course", cascade="all, delete-orphan"
    )


class CourseInfo(Base):
    __tablename__ = "course_info"

    id = Column(String(255), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(Text, nullable=False)
    course_id = Column(String(255), ForeignKey("courses.id"))

    course = relationship("Course", back_populates="info")


class Section(Base):
    __tablename__ = "sections"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    course_id = Column(String(255), ForeignKey("courses.id"))

    course = relationship("Course", back_populates="sections")
    lessons = relationship(
        "Lesson", secondary=lesson_sections, back_populates="sections"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    passing = Column(String(10), default="no")  # "yes" или "no"
    description = Column(Text, nullable=True)

    sections = relationship(
        "Section", secondary=lesson_sections, back_populates="lessons"
    )
