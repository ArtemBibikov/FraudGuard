from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from ..enums import TransactionStatus, TransactionChannel, CurrencyCode
from .utils import (
    HIGH_AMOUNT_THRESHOLD,
    MAX_BATCH_SIZE,
    check_lat_range,
    check_lon_range,
    check_cords_pair,
    check_amount_range,
    format_transaction_amount,
    get_transaction_risk_score,
)

class TransactionLocation(BaseModel):
    country: Optional[str] = Field(None, max_length=2)
    city: Optional[str] = Field(None, max_length=128)
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    
    @field_validator('latitude')
    @classmethod
    def validate_latitude_range(cls, v):
        return check_lat_range(v)

    @field_validator('longitude')
    @classmethod
    def validate_longitude_range(cls, v):
        return check_lon_range(v)

    @model_validator(mode='after')
    @classmethod
    def validate_coordinate_pair(cls, values):
        return check_cords_pair(values)

class TransactionCreateRequest(BaseModel):
    userId: Optional[UUID] = None
    amount: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12)
    currency: CurrencyCode
    merchantId: Optional[str] = Field(None, max_length=64)
    merchantCategoryCode: Optional[str] = Field(None, max_length=4)
    timestamp: datetime
    ipAddress: Optional[str] = Field(None, max_length=64)
    deviceId: Optional[str] = Field(None, max_length=128)
    channel: Optional[TransactionChannel] = None
    location: Optional[TransactionLocation] = None
    metadata: Optional[dict] = None
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        return check_amount_range(v)

    def get_risk_score(self):
        return get_transaction_risk_score(self)

    def is_high_value(self):
        return self.amount > HIGH_AMOUNT_THRESHOLD

class TransactionBatchCreateRequest(BaseModel):
    items: list[TransactionCreateRequest] = Field(..., min_items=1, max_items=MAX_BATCH_SIZE)

    def get_total_amount(self):
        return sum(item.amount for item in self.items)

    def get_high_value_count(self):
        return sum(1 for item in self.items if item.is_high_value())

class TransactionResponse(BaseModel):
    id: UUID
    userId: UUID
    amount: Decimal
    currency: CurrencyCode
    status: TransactionStatus
    merchantId: Optional[str]
    merchantCategoryCode: Optional[str]
    timestamp: datetime
    ipAddress: Optional[str]
    deviceId: Optional[str]
    channel: Optional[TransactionChannel]
    location: Optional[TransactionLocation]
    isFraud: bool
    metadata: Optional[dict]
    createdAt: datetime
    updatedAt: datetime
    
    def get_formatted_amount(self):
        return format_transaction_amount(self.amount)

    def get_risk_score(self):
        return get_transaction_risk_score(self)
    
    model_config = {
        "json_encoders": {
            Decimal: float,
        }
    }

class FraudRuleEvaluationResult(BaseModel):
    ruleId: UUID
    ruleName: str
    priority: int
    enabled: bool
    matched: bool
    description: str

class TransactionDecision(BaseModel):
    transaction: TransactionResponse
    ruleResults: list[FraudRuleEvaluationResult]

    def get_matched_rules_count(self):
        return sum(1 for rule in self.ruleResults if rule.matched)

class PagedTransactions(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    size: int
    def get_total_amount(self):
        return sum(item.amount for item in self.items)

class TransactionBatchResultItem(BaseModel):
    index: int
    decision: Optional[TransactionDecision] = None
    error: Optional[dict] = None

    def is_successful(self):
        return self.error is None

class TransactionBatchResult(BaseModel):
    items: list[TransactionBatchResultItem]
    def get_success_count(self):
        return sum(1 for item in self.items if item.is_successful())

    def get_error_count(self):
        return sum(1 for item in self.items if not item.is_successful())
