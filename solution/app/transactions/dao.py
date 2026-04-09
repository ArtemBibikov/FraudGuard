from ..dao.base import BaseDAO
from .models import Transaction

class TransactionDAO(BaseDAO):
    model = Transaction
