import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import EmailStr
from jose import jwt

from ..config import settings
from .dao import UserDAO

pwd_context = CryptContext(schemes=["argon2","bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=3600)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    secret_key = os.getenv("RANDOM_SECRET", settings.SECRET_KEY)
    encode_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm="HS256"
    )
    return encode_jwt


async def auth_user(email: EmailStr, password: str):
    user = await UserDAO.find_one_or_none(email=email)
    if user and verify_password(password, user.password_hash):
        return user

    return None