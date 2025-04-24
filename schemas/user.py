from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    login: str
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    login: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    avatar: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_admin: bool
    avatar: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class User(UserInDB):
    # Публичная модель пользователя, исключает некоторые поля
    pass