from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SendVerificationCode(BaseModel):
    email: EmailStr


class UserCreate(BaseModel):
    login: str
    email: EmailStr
    password: str
    verification_code: str

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    login: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    img: Optional[str]
    name: Optional[str]


class UserOut(BaseModel):
    id: int
    login: str
    email: str
    name: Optional[str] = None
    img: Optional[str] = None

    class Config:
        orm_mode = True
