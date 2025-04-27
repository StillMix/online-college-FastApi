# models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base
from models.user_course import user_course


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    img = Column(String, nullable=True)
    name = Column(String, nullable=True)
    role = Column(String, default="student")  # Добавляем роль с дефолтным значением
    courses = relationship("Course", secondary=user_course, backref="users")
