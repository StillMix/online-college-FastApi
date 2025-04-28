# schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


class SendVerificationCode(BaseModel):
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserCreate(BaseModel):
    login: str
    email: EmailStr
    password: str
    verification_code: str

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    login: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    img: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


class UserOut(BaseModel):
    id: int
    login: str
    email: str
    name: Optional[str] = None
    img: Optional[str] = None
    role: str = "student"

    class Config:
        orm_mode = True


class UserCourse(BaseModel):
    course_id: str
    user_id: int


class LessonCompletion(BaseModel):
    lesson_id: str
    user_id: int
