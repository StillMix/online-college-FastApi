from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Связующая таблица для разделов и контента
lesson_sections = Table(
    "lesson_sections",
    Base.metadata,
    Column(
        "section_id", String(255), ForeignKey("sections.id"), primary_key=True
    ),  # Изменено с Integer на String
    Column(
        "lesson_id", String(255), ForeignKey("lessons.id"), primary_key=True
    ),  # Изменено с Integer на String
)


class Course(Base):
    __tablename__ = "courses"

    id = Column(
        String(255), primary_key=True, index=True
    )  # Изменено с Integer на String
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

    id = Column(
        String(255), primary_key=True, index=True
    )  # Используем String вместо Integer
    title = Column(String(255), nullable=False)
    subtitle = Column(Text, nullable=False)
    course_id = Column(
        String(255), ForeignKey("courses.id")
    )  # Используем String вместо Integer

    course = relationship("Course", back_populates="info")


class Section(Base):
    __tablename__ = "sections"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    course_id = Column(String(255), ForeignKey("courses.id"))

    # Добавляем поле content как свойство, а не колонку
    @property
    def content(self):
        return self.lessons

    @content.setter
    def content(self, value):
        # Этот метод нужен для совместимости с API, но на самом деле мы не будем использовать его
        pass

    course = relationship("Course", back_populates="sections")
    lessons = relationship(
        "Lesson", secondary=lesson_sections, back_populates="sections"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(
        String(255), primary_key=True, index=True
    )  # Изменено с Integer на String
    name = Column(String(255), nullable=False)
    passing = Column(String(10), default="no")  # "yes" или "no"
    description = Column(Text, nullable=True)

    sections = relationship(
        "Section", secondary=lesson_sections, back_populates="lessons"
    )
