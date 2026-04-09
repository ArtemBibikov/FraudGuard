from fastapi import HTTPException, status

UserAccessForbiddenException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="USER может получать доступ только к своему профилю"
)

AdminOnlyAccessException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может получать доступ к списку пользователей"
)

UserAlreadyExistException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Пользователь уже существует",
)

IncorrectEmailORPasswordException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Неверный email или пароль",
)

TokenExpiredException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Токен истек',
)

TokenAbsentException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Токен отсутствует',
)

InvalidAuthSchemeException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Неверная схема аутентификации. Используйте 'Bearer'",
)

IncorrectTokenFormatException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Неверный формат токена",
)

UserIsNotPresentException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Пользователь не найден"
)

UserCannotChangeRoleOrIsActiveException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="USER не может изменять роль или isActive"
)

UserNotFoundException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Пользователь не найден"
)

UserCanOnlyUpdateOwnProfileException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="USER может обновлять только свой профиль"
)

UserCannotChangeRoleOrIsActiveEnException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="USER не может изменять роль или isActive"
)

OnlyAdminCanCreateUsersException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может создавать пользователей"
)

OnlyAdminCanDeactivateUsersException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может деактивировать пользователей"
)
