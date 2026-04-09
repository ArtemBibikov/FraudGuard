from ..users.schemas import AuthResponse, UserResponse


def response_auth(access_token, new_user):
    return AuthResponse(
        accessToken=access_token,
        expiresIn=3600,
        user=UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            fullName=new_user.full_name,
            age=new_user.age,
            region=new_user.region,
            gender=new_user.gender,
            maritalStatus=new_user.marital_status,
            role=new_user.role,
            isActive=new_user.is_active,
            createdAt=new_user.created_at.isoformat() if new_user.created_at else "",
            updatedAt=new_user.updated_at.isoformat() if new_user.updated_at else ""
        )
    )
