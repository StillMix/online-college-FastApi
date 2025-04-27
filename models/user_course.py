# models/user_course.py
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from database import Base

# Связь многие-ко-многим между пользователями и курсами
user_course = Table(
    "user_courses",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("course_id", String, ForeignKey("courses.id"), primary_key=True),
)
