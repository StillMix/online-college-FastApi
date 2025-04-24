from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from database import get_db
from models.user import User
from schemas.token import TokenData
from config import settings
from services.users import get_user_by_id

#