from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class FraudRuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    dslExpression: str = Field(..., min_length=3, max_length=2000)
    enabled: bool = True
    priority: int = Field(..., ge=1)

class FraudRuleUpdateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    dslExpression: str = Field(..., min_length=3, max_length=2000)
    enabled: bool
    priority: int = Field(..., ge=1)

class FraudRule(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    dslExpression: str
    enabled: bool
    priority: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
