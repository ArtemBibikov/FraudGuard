from fastapi import HTTPException, status

StatisticsAdminOnlyException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может получать доступ к статистике"
)

InvalidDateRangeException = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Неверный диапазон дат"
)

InvalidDateFormatException = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Неверный формат даты"
)

PeriodTooLongException = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Период слишком длинный"
)

InvalidParameterException = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Неверный параметр"
)

UserRiskProfileAccessException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="USER может получать доступ только к своему профилю риска"
)

InvalidUUIDException = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Неверный формат UUID пользователя"
)