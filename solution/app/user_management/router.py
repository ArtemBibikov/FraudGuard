from fastapi import APIRouter, Depends, Query, status, Response
from uuid import UUID
from .schemas import User, UserUpdateRequest, UserCreateRequest, PagedUsers
from .exceptions import (
    UserAccessForbiddenException, 
    AdminOnlyAccessException, 
    UserAlreadyExistException,
    UserCannotChangeRoleOrIsActiveException,
    UserNotFoundException,
    UserCanOnlyUpdateOwnProfileException,
    UserCannotChangeRoleOrIsActiveEnException,
    OnlyAdminCanCreateUsersException,
    OnlyAdminCanDeactivateUsersException
)
from ..users.dao import UserDAO
from ..dependencies import get_current_user
from ..users.auth import get_password_hash

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

@router.get('/me')
async def get_me(current_user = Depends(get_current_user)):
    return {
        'id': str(current_user.id),
        'email': current_user.email,
        'fullName': current_user.full_name,
        'age': current_user.age,
        'region': current_user.region,
        'gender': current_user.gender,
        'maritalStatus': current_user.marital_status,
        'role': current_user.role,
        'isActive': current_user.is_active,
        'createdAt': current_user.created_at,
        'updatedAt': current_user.updated_at
    }

@router.put('/me')
async def update_me(user_update: UserUpdateRequest, current_user = Depends(get_current_user)):
    if user_update.role is not None or user_update.isActive is not None:
        raise UserCannotChangeRoleOrIsActiveException

    update_data = {}

    if user_update.fullName is not None:
        update_data['full_name'] = user_update.fullName
    if user_update.age is not None:
        update_data['age'] = user_update.age
    if user_update.region is not None:
        update_data['region'] = user_update.region
    if user_update.gender is not None:
        update_data['gender'] = user_update.gender
    if user_update.maritalStatus is not None:
        update_data['marital_status'] = user_update.maritalStatus

    if not update_data:
        return {
            'id': str(current_user.id),
            'email': current_user.email,
            'fullName': current_user.full_name,
            'age': current_user.age,
            'region': current_user.region,
            'gender': current_user.gender,
            'maritalStatus': current_user.marital_status,
            'role': current_user.role,
            'isActive': current_user.is_active,
            'createdAt': current_user.created_at,
            'updatedAt': current_user.updated_at
        }

    updated_user = await UserDAO.update(current_user.id, **update_data)

    if not updated_user:
        raise UserNotFoundException

    return {
        'id': str(updated_user.id),
        'email': updated_user.email,
        'fullName': updated_user.full_name,
        'age': updated_user.age,
        'region': updated_user.region,
        'gender': updated_user.gender,
        'maritalStatus': updated_user.marital_status,
        'role': updated_user.role,
        'isActive': updated_user.is_active,
        'createdAt': updated_user.created_at,
        'updatedAt': updated_user.updated_at
    }

@router.get('/{user_id}')
async def get_user_by_id(user_id: str, current_user = Depends(get_current_user)):
    if current_user.role == "USER" and str(current_user.id) != user_id:
        raise UserAccessForbiddenException
    
    user_uuid = UUID(user_id)
    user = await UserDAO.find_by_id(user_uuid)  
    
    if not user:
        raise UserNotFoundException
    
    return {
        'id': str(user.id),
        'email': user.email,
        'firstName': user.full_name,
        'lastName': '',
        'dateOfBirth': None,
        'address': None,
        'phoneNumber': None,
        'maritalStatus': user.marital_status,  
        'role': user.role,
        'isActive': user.is_active,  
        'createdAt': user.created_at,  
        'updatedAt': user.updated_at   
    }

@router.put('/{user_id}')
async def update_user_by_id(user_id: str, user_update: UserUpdateRequest, current_user = Depends(get_current_user)):
    if current_user.role == "USER" and str(current_user.id) != user_id:
        raise UserCanOnlyUpdateOwnProfileException
    
    if current_user.role == "USER" and (user_update.role is not None or user_update.isActive is not None):
        raise UserCannotChangeRoleOrIsActiveEnException
    
    user_uuid = UUID(user_id)
    update_data = {}
    
    if user_update.fullName is not None:
        update_data['full_name'] = user_update.fullName
    if user_update.age is not None:
        update_data['age'] = user_update.age
    if user_update.region is not None:
        update_data['region'] = user_update.region
    if user_update.gender is not None:
        update_data['gender'] = user_update.gender
    if user_update.maritalStatus is not None:
        update_data['marital_status'] = user_update.maritalStatus
    
    updated_user = await UserDAO.update(user_uuid, **update_data)
    
    if not updated_user:
        raise UserNotFoundException
    
    return User.model_validate({
        'id': updated_user.id,
        'email': updated_user.email,
        'fullName': updated_user.full_name,
        'age': updated_user.age,
        'region': updated_user.region,
        'gender': updated_user.gender,
        'maritalStatus': updated_user.marital_status,
        'role': updated_user.role,
        'isActive': updated_user.is_active,
        'createdAt': updated_user.created_at,
        'updatedAt': updated_user.updated_at
    })

@router.get('')
async def list_users(page: int = Query(0), size: int = Query(20), current_user = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise AdminOnlyAccessException
    
    users = await UserDAO.find_all(page=page, size=size)
    total = await UserDAO.count()
    
    user_dtos = [
        User(
            id=user.id,
            email=user.email,
            fullName=user.full_name,
            age=user.age,
            region=user.region,
            gender=user.gender,
            maritalStatus=user.marital_status,
            role=user.role,
            isActive=user.is_active,
            createdAt=user.created_at,
            updatedAt=user.updated_at,
        )
        for user in users
    ]
    
    return PagedUsers(
        items=user_dtos,
        total=total,
        page=page,
        size=size
    )

@router.post('', status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreateRequest, current_user = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise OnlyAdminCanCreateUsersException
    
    found_user = await UserDAO.find_one_or_none(email=user_create.email)
    if found_user:
        raise UserAlreadyExistException

    hashed_password = get_password_hash(user_create.password)
    
    new_user = await UserDAO.add(
        email=user_create.email,
        password_hash=hashed_password,
        full_name=user_create.fullName,
        age=user_create.age,
        region=user_create.region,
        gender=user_create.gender,
        marital_status=user_create.maritalStatus,
        role=user_create.role,
        is_active=True
    )
    
    return User.model_validate({
        'id': new_user.id,
        'email': new_user.email,
        'fullName': new_user.full_name,
        'age': new_user.age,
        'region': new_user.region,
        'gender': new_user.gender,
        'maritalStatus': new_user.marital_status,
        'role': new_user.role,
        'isActive': new_user.is_active,
        'createdAt': new_user.created_at,
        'updatedAt': new_user.updated_at
    })

@router.delete('/{user_id}')
async def delete_user(user_id: str, current_user = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise OnlyAdminCanDeactivateUsersException
    
    user_uuid = UUID(user_id)
    updated_user = await UserDAO.update(
        user_uuid,
        is_active=False
    )
    
    if not updated_user:
        raise UserNotFoundException
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
