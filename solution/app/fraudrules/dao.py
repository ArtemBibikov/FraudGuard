from ..dao.base import BaseDAO
from .models import FraudRule


class FraudRuleDAO(BaseDAO):
    model = FraudRule
