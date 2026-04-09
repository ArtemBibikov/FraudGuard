from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class RiskMerchant(BaseModel):
    merchantId: str
    merchantCategoryCode: Optional[str]
    txCount: int
    gmv: float
    declineRate: float = Field(..., ge=0, le=1)

class TimeSeriesPoint(BaseModel):
    bucketStart: datetime
    txCount: int
    gmv: float
    approvalRate: float = Field(..., ge=0, le=1)
    declineRate: float = Field(..., ge=0, le=1)

class TimeSeriesResponse(BaseModel):
    points: List[TimeSeriesPoint]

class SRuleMatchStats(BaseModel):
    ruleId: UUID
    ruleName: str
    matches: int
    shareOfDeclines: float = Field(..., ge=0, le=1)
    uniqueUsers: int
    uniqueMerchants: int

class RulesMatchResponse(BaseModel):
    items: List[SRuleMatchStats]

class UserRiskProfile(BaseModel):
    userId: str
    txCount_24h: int
    gmv_24h: float
    distinctDevices_24h: int
    distinctIps_24h: int
    distinctCities_24h: int
    declineRate_30d: float = Field(..., ge=0, le=1)
    lastSeenAt: Optional[datetime]

class OverviewStats(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime
    volume: int
    gmv: float
    approvalRate: float = Field(..., ge=0, le=1)
    declineRate: float = Field(..., ge=0, le=1)
    topRiskMerchants: List[RiskMerchant]
