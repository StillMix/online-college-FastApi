from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=False)
    type = Column(String, nullable=False)
    timetoendL = Column(String, nullable=False)  # Уровень сложности курса
    color = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    icontype = Column(String, nullable=False)
    titleForCourse = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Отношения с другими таблицами
    info = relationship("CourseInfo", back_populates="course", cascade="all, delete-orphan")
    sections = relationship("CourseSection", back_populates="course", cascade="all, delete-orphan")

class CourseInfo(Base):
    __tablename__ = "course_info"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=False)
    
    # Отношения с другими таблицами
    course = relationship("Course", back_populates="info")

class CourseSection(Base):
    __tablename__ = "course_sections"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    order_id = Column(String, nullable=False)  # ID для порядка отображения
    name = Column(String, nullable=False)
    
    # Отношения с другими таблицами
    course = relationship("Course", back_populates="sections")
    lessons = relationship("Lesson", back_populates="section", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("course_sections.id", ondelete="CASCADE"))
    order_id = Column(String, nullable=False)  # ID для порядка отображения
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    passing = Column(String, default="no")
    
    # Отношения с другими таблицами
    section = relationship("CourseSection", back_populates="lessons")