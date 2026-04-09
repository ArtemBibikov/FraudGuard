from fastapi import APIRouter,status

from ..exceptions import (
    UserAlreadyExistException,
    IncorrectEmailORPasswordException,
    UserDeactivatedException, UserCreationFailedException)
from ..users.auth import get_password_hash, create_access_token, auth_user
from ..users.dao import UserDAO
from ..users.schemas import AuthResponse, RegisterRequest, LoginRequest
from ..utils.auth_utils import response_auth

router = APIRouter(
    prefix='/auth',
    tags=['Auth']
)

@router.post('/register', response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest) -> AuthResponse:
    found_user = await UserDAO.find_one_or_none(email=user_data.email)
    if found_user:
        raise UserAlreadyExistException
    hashed_password = get_password_hash(user_data.password)

    user_dict = {
        "email": user_data.email,
        "password_hash": hashed_password,
        "full_name": user_data.fullName,
        "age": user_data.age,
        "region": user_data.region,
        "gender": user_data.gender,
        "marital_status": user_data.maritalStatus,
        "role": "USER",
        "is_active": True
    }
    await UserDAO.add(**user_dict)
    new_user = await UserDAO.find_one_or_none(email=user_data.email)
    if not new_user:
        raise UserCreationFailedException
    access_token = create_access_token({
        "sub": str(new_user.id),
        "role": new_user.role
    })
    return response_auth(access_token, new_user)

@router.post('/login', response_model=AuthResponse,  status_code=status.HTTP_200_OK)
async def login(user_data: LoginRequest) -> AuthResponse:
    user = await auth_user(user_data.email, user_data.password)
    if not user:
        raise IncorrectEmailORPasswordException
    if not user.is_active:
        raise UserDeactivatedException
    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })
    return response_auth(access_token, user)
