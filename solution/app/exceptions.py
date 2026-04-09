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

InsufficientPermissionsException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Недостаточно прав. Требуется роль ADMIN",
)

UserCreationFailedException = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Не удалось создать пользователя"
)

UserDeactivatedException = HTTPException(
    status_code=status.HTTP_423_LOCKED,
    detail="Аккаунт пользователя деактивирован"
)

