import os
from datetime import datetime, timezone
from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from .config import settings
from .exceptions import (
    TokenAbsentException,
    IncorrectTokenFormatException,
    TokenExpiredException,
    UserIsNotPresentException,
    InvalidAuthSchemeException, 
    UserDeactivatedException, 
    InsufficientPermissionsException
)
from .users.dao import UserDAO

security = HTTPBearer()

def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme.lower() != "bearer":
        raise InvalidAuthSchemeException
    token = credentials.credentials
    if not token:
        raise TokenAbsentException

    return token

async def get_current_user(token: str = Depends(get_token)):
    try:
        secret_key = os.getenv("RANDOM_SECRET", settings.SECRET_KEY)
        payload = jwt.decode(
            token, secret_key, algorithms=["HS256"]
        )
    except JWTError:
        raise IncorrectTokenFormatException

    expire = payload.get("exp")
    if not expire or expire < datetime.now(timezone.utc).timestamp():
        raise TokenExpiredException

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UserIsNotPresentException

    role = payload.get("role")
    if not role or role not in ["USER", "ADMIN"]:
        raise IncorrectTokenFormatException

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise UserIsNotPresentException

    user = await UserDAO.find_by_id(user_id)
    if not user:
        raise UserIsNotPresentException

    if user.role != role:
        raise IncorrectTokenFormatException
    if not user.is_active:
        raise UserDeactivatedException

    return user


async def get_current_admin_user(current_user = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise InsufficientPermissionsException
    return current_user
