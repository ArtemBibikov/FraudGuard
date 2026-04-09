from fastapi import HTTPException, status

RuleNameAlreadyExistsException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Правило с таким именем уже существует"
)

RuleNotFoundException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Правило не найдено"
)

OnlyAdminCanAccessRulesException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может получать доступ к правилам мошенничества"
)

OnlyAdminCanCreateRulesException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может создавать правила"
)

OnlyAdminCanUpdateRulesException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может обновлять правила"
)

OnlyAdminCanDeleteRulesException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может удалять правила"
)

OnlyAdminCanValidateRulesException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Только ADMIN может валидировать DSL"
)
