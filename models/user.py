from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    img = Column(String, nullable=True)
    name = Column(String, nullable=True)
