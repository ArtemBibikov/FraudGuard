import enum

class Gender(str, enum.Enum):
    """
    Пол пользователя.
    Используется в моделях User и схемах
    """
    MALE = "MALE"
    FEMALE = "FEMALE"

class MaritalStatus(str, enum.Enum):
    """
    Семейное положение пользователя.
    Используется в моделях User и схемах
    """
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"
    WIDOWED = "WIDOWED"

class UserRole(str, enum.Enum):
    """
    Роли пользователей в системе антифрода.
    """
    ADMIN = "ADMIN"
    USER = "USER"

class TransactionStatus(str, enum.Enum):
    """
    Статус транзакции.
    """
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"

class TransactionChannel(str, enum.Enum):
    """
    Канал транзакции.
    """
    WEB = "WEB"
    MOBILE = "MOBILE"
    POS = "POS"
    OTHER = "OTHER"

class CurrencyCode(str, enum.Enum):
    """
    Коды валют.
    """
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"