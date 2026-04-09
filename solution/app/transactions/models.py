import uuid
from sqlalchemy import Column, Integer, String, UUID, Enum, Boolean, DateTime, Text, Numeric
from sqlalchemy.sql.functions import func
from ..database import Base
from ..enums.enums import TransactionStatus, TransactionChannel, CurrencyCode

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.APPROVED)
    merchantId = Column(String(100), nullable=True)
    merchantCategoryCode = Column(String(4), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    ipAddress = Column(String(45), nullable=True)
    deviceId = Column(String(100), nullable=True)
    channel = Column(Enum(TransactionChannel), nullable=True)
    isFraud = Column(Boolean, default=False, nullable=False)
    transaction_metadata = Column(Text, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
