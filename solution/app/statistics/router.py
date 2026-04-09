from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from datetime import datetime, timezone, timedelta
from uuid import UUID

from ..dependencies import get_current_user
from ..transactions.dao import TransactionDAO
from ..fraudrules.dao import FraudRuleDAO
from ..enums.enums import TransactionStatus
from .schemas import (
    OverviewStats,
    RiskMerchant,
    TimeSeriesResponse,
    TimeSeriesPoint,
    SRuleMatchStats,
    RulesMatchResponse,
    UserRiskProfile
)

from .exceptions import (
    StatisticsAdminOnlyException,
    InvalidDateRangeException,
    InvalidDateFormatException,
    PeriodTooLongException,
    UserRiskProfileAccessException,
    InvalidUUIDException
)

router = APIRouter()


def parse_date(date_str: str) -> datetime:
    if not date_str:
        return None
    
    date_str = date_str.replace('%3A', ':')
    
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        raise InvalidDateFormatException


@router.get('/overview')
async def get_overview_stats(
        from_: Optional[str] = Query(None, alias="from"),
        to_date: Optional[str] = Query(None, alias="to"),
        timezone_str: Optional[str] = Query("UTC"),
        current_user=Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise StatisticsAdminOnlyException()
    
    try:
        to_dt = parse_date(to_date) if to_date else datetime.now(timezone.utc)
        from_dt = parse_date(from_) if from_ else to_dt - timedelta(days=30)
        
        if from_dt >= to_dt:
            raise InvalidDateRangeException("from должен быть меньше to")
        
        if (to_dt - from_dt).days > 90:
            raise PeriodTooLongException("Максимальный период 90 дней")
        
        transactions = await TransactionDAO.find_all(page=0, size=1000)
        
        filtered_tx = []
        for tx in transactions:
            if hasattr(tx, 'timestamp'):
                tx_time = tx.timestamp
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                if from_dt <= tx_time < to_dt:
                    filtered_tx.append(tx)
        
        if not filtered_tx:
            return OverviewStats(
                **{"from": from_dt.replace(microsecond=0), "to": to_dt.replace(microsecond=0)},
                volume=0,
                gmv=0.0,
                approvalRate=0.0,
                declineRate=0.0,
                topRiskMerchants=[]
            )
        
        volume = len(filtered_tx)
        gmv = sum(float(tx.amount) for tx in filtered_tx if hasattr(tx, 'amount'))
        
        approved = sum(1 for tx in filtered_tx 
                      if hasattr(tx, 'status') and tx.status == TransactionStatus.APPROVED)
        declined = sum(1 for tx in filtered_tx 
                      if hasattr(tx, 'status') and tx.status == TransactionStatus.DECLINED)
        
        approval_rate = approved / volume if volume > 0 else 0.0
        decline_rate = declined / volume if volume > 0 else 0.0
        
        merchant_stats = {}
        for tx in filtered_tx:
            if hasattr(tx, 'merchantId') and tx.merchantId:
                mid = tx.merchantId
                if mid not in merchant_stats:
                    merchant_stats[mid] = {
                        'merchantId': mid,
                        'merchantCategoryCode': getattr(tx, 'merchantCategoryCode', None),
                        'txCount': 0,
                        'gmv': 0.0,
                        'declineCount': 0
                    }
                
                merchant_stats[mid]['txCount'] += 1
                if hasattr(tx, 'amount'):
                    merchant_stats[mid]['gmv'] += float(tx.amount)
                
                if hasattr(tx, 'status') and tx.status == TransactionStatus.DECLINED:
                    merchant_stats[mid]['declineCount'] += 1
        
        risk_merchants = []
        for stats in merchant_stats.values():
            if stats['txCount'] > 0:
                decline_rate = stats['declineCount'] / stats['txCount']
                risk_merchants.append(RiskMerchant(
                    merchantId=stats['merchantId'],
                    merchantCategoryCode=stats['merchantCategoryCode'],
                    txCount=stats['txCount'],
                    gmv=stats['gmv'],
                    declineRate=decline_rate
                ))
        
        risk_merchants.sort(key=lambda x: x.declineRate, reverse=True)
        top_risk_merchants = risk_merchants[:10]
        
        return OverviewStats(
            **{"from": from_dt.replace(microsecond=0), "to": to_dt.replace(microsecond=0)},
            volume=volume,
            gmv=gmv,
            approvalRate=approval_rate,
            declineRate=decline_rate,
            topRiskMerchants=top_risk_merchants
        )
        
    except Exception as e:
        if isinstance(e, (InvalidDateFormatException, InvalidDateRangeException, PeriodTooLongException)):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при получении статистики: {str(e)}'
        )


@router.get('/transactions/timeseries')
async def get_transactions_timeseries(
        from_date: Optional[str] = Query(None, alias="from", description="Начало периода (RFC3339)"),
        to_date: Optional[str] = Query(None, alias="to", description="Конец периода (RFC3339)"),
        group_by: str = Query("day", description="Группировка: hour, day"),
        current_user=Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise StatisticsAdminOnlyException()
    
    try:
        to_dt = parse_date(to_date) if to_date else datetime.now(timezone.utc)
        from_dt = parse_date(from_date) if from_date else to_dt - timedelta(days=30)
        
        transactions = await TransactionDAO.find_all(page=0, size=1000)
        
        filtered_tx = []
        for tx in transactions:
            if hasattr(tx, 'timestamp'):
                tx_time = tx.timestamp
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                if from_dt <= tx_time < to_dt:
                    filtered_tx.append(tx)
        
        if not filtered_tx:
            return TimeSeriesResponse(points=[])
        
        bucket_size = timedelta(hours=1) if group_by == "hour" else timedelta(days=1)
        buckets = {}
        
        current = from_dt
        while current < to_dt:
            buckets[current] = {
                'txCount': 0,
                'gmv': 0.0,
                'approved': 0,
                'declined': 0
            }
            current += bucket_size
        
        for tx in filtered_tx:
            tx_time = tx.timestamp
            if tx_time.tzinfo is None:
                tx_time = tx_time.replace(tzinfo=timezone.utc)
            
            bucket_start = from_dt
            while bucket_start + bucket_size <= tx_time:
                bucket_start += bucket_size
            
            if bucket_start in buckets:
                buckets[bucket_start]['txCount'] += 1
                if hasattr(tx, 'amount'):
                    buckets[bucket_start]['gmv'] += float(tx.amount)
                
                if hasattr(tx, 'status'):
                    if tx.status == TransactionStatus.APPROVED:
                        buckets[bucket_start]['approved'] += 1
                    elif tx.status == TransactionStatus.DECLINED:
                        buckets[bucket_start]['declined'] += 1
        
        points = []
        for bucket_start, stats in buckets.items():
            if stats['txCount'] > 0:
                approval_rate = stats['approved'] / stats['txCount']
                decline_rate = stats['declined'] / stats['txCount']
            else:
                approval_rate = decline_rate = 0.0
            
            points.append(TimeSeriesPoint(
                bucketStart=bucket_start.replace(microsecond=0),
                txCount=stats['txCount'],
                gmv=stats['gmv'],
                approvalRate=approval_rate,
                declineRate=decline_rate
            ))
        
        return TimeSeriesResponse(points=points)
        
    except Exception as e:
        if isinstance(e, (InvalidDateFormatException, InvalidDateRangeException, PeriodTooLongException)):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при получении таймсерии: {str(e)}'
        )


@router.get('/rules/matches')
async def get_rules_matches(
        from_date: Optional[str] = Query(None, alias="from"),
        to_date: Optional[str] = Query(None, alias="to"),
        current_user=Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise StatisticsAdminOnlyException()
    
    try:
        to_dt = parse_date(to_date) if to_date else datetime.now(timezone.utc)
        from_dt = parse_date(from_date) if from_date else to_dt - timedelta(days=30)
        
        rules = await FraudRuleDAO.find_all(page=0, size=1000)
        transactions = await TransactionDAO.find_all(page=0, size=1000)
        
        filtered_tx = []
        for tx in transactions:
            if hasattr(tx, 'timestamp'):
                tx_time = tx.timestamp
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                if from_dt <= tx_time < to_dt:
                    filtered_tx.append(tx)
        
        rule_stats = {}
        total_declined = 0
        
        for rule in rules:
            rule_stats[rule.id] = {
                'ruleId': rule.id,
                'ruleName': rule.name,
                'matches': 0,
                'declines': 0,
                'users': set(),
                'merchants': set()
            }
        
        for tx in filtered_tx:
            if hasattr(tx, 'status') and tx.status == TransactionStatus.DECLINED:
                total_declined += 1
                
                for rule_id in rule_stats:
                    rule_stats[rule_id]['matches'] += 1
                    rule_stats[rule_id]['declines'] += 1
                    
                    if hasattr(tx, 'userId'):
                        rule_stats[rule_id]['users'].add(tx.userId)
                    if hasattr(tx, 'merchantId'):
                        rule_stats[rule_id]['merchants'].add(tx.merchantId)
        
        items = []
        for stats in rule_stats.values():
            share_of_declines = stats['declines'] / total_declined if total_declined > 0 else 0.0
            
            items.append(SRuleMatchStats(
                ruleId=stats['ruleId'],
                ruleName=stats['ruleName'],
                matches=stats['matches'],
                shareOfDeclines=share_of_declines,
                uniqueUsers=len(stats['users']),
                uniqueMerchants=len(stats['merchants'])
            ))
        
        return RulesMatchResponse(items=items)
        
    except Exception as e:
        if isinstance(e, (InvalidDateFormatException, InvalidDateRangeException, PeriodTooLongException)):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при получении статистики правил: {str(e)}'
        )


@router.get('/merchants/risk')
async def get_merchants_risk(
        from_date: Optional[str] = Query(None, alias="from"),
        to_date: Optional[str] = Query(None, alias="to"),
        current_user=Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise StatisticsAdminOnlyException()
    
    try:
        to_dt = parse_date(to_date) if to_date else datetime.now(timezone.utc)
        from_dt = parse_date(from_date) if from_date else to_dt - timedelta(days=30)
        
        transactions = await TransactionDAO.find_all(page=0, size=1000)
        
        filtered_tx = []
        for tx in transactions:
            if hasattr(tx, 'timestamp'):
                tx_time = tx.timestamp
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                if from_dt <= tx_time < to_dt:
                    filtered_tx.append(tx)
        
        merchant_stats = {}
        for tx in filtered_tx:
            if hasattr(tx, 'merchantId') and tx.merchantId:
                mid = tx.merchantId
                if mid not in merchant_stats:
                    merchant_stats[mid] = {
                        'merchantId': mid,
                        'merchantCategoryCode': getattr(tx, 'merchantCategoryCode', None),
                        'txCount': 0,
                        'gmv': 0.0,
                        'declineCount': 0
                    }
                
                merchant_stats[mid]['txCount'] += 1
                if hasattr(tx, 'amount'):
                    merchant_stats[mid]['gmv'] += float(tx.amount)
                
                if hasattr(tx, 'status') and tx.status == TransactionStatus.DECLINED:
                    merchant_stats[mid]['declineCount'] += 1
        
        merchants = []
        for stats in merchant_stats.values():
            if stats['txCount'] > 0:
                decline_rate = stats['declineCount'] / stats['txCount']
                merchants.append(RiskMerchant(
                    merchantId=stats['merchantId'],
                    merchantCategoryCode=stats['merchantCategoryCode'],
                    txCount=stats['txCount'],
                    gmv=stats['gmv'],
                    declineRate=decline_rate
                ))
        
        merchants.sort(key=lambda x: x.declineRate, reverse=True)
        
        return merchants
        
    except Exception as e:
        if isinstance(e, (InvalidDateFormatException, InvalidDateRangeException, PeriodTooLongException)):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при получении статистики рисков merchants: {str(e)}'
        )


@router.get('/users/{user_id}/risk-profile')
async def get_user_risk_profile(
        user_id: str,
        current_user=Depends(get_current_user)
):
    if current_user.role == "USER" and current_user.id != user_id:
        raise UserRiskProfileAccessException()
    
    try:
        try:
            UUID(user_id)
        except ValueError:
            raise InvalidUUIDException()
        
        transactions = await TransactionDAO.find_all(page=0, size=1000)
        
        user_transactions = []
        for tx in transactions:
            if hasattr(tx, 'userId') and str(tx.userId) == user_id:
                user_transactions.append(tx)
        
        if not user_transactions:
            return UserRiskProfile(
                userId=user_id,
                txCount_24h=0,
                gmv_24h=0.0,
                distinctDevices_24h=0,
                distinctIps_24h=0,
                distinctCities_24h=0,
                declineRate_30d=0.0,
                lastSeenAt=None
            )
        
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)
        month_ago = now - timedelta(days=30)
        
        recent_tx = []
        for tx in user_transactions:
            if hasattr(tx, 'timestamp'):
                tx_time = tx.timestamp
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                if tx_time > day_ago:
                    recent_tx.append(tx)
        
        tx_count_24h = len(recent_tx)
        gmv_24h = sum(float(tx.amount) for tx in recent_tx if hasattr(tx, 'amount'))
        
        devices = set()
        ips = set()
        cities = set()
        
        for tx in recent_tx:
            if hasattr(tx, 'deviceId'):
                devices.add(tx.deviceId)
            if hasattr(tx, 'ipAddress'):
                ips.add(tx.ipAddress)
            if hasattr(tx, 'location') and hasattr(tx.location, 'city'):
                cities.add(tx.location.city)
        
        month_tx = []
        for tx in user_transactions:
            if hasattr(tx, 'timestamp'):
                tx_time = tx.timestamp
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                if tx_time > month_ago:
                    month_tx.append(tx)
        
        declined_count = sum(1 for tx in month_tx 
                           if hasattr(tx, 'status') and tx.status == TransactionStatus.DECLINED)
        decline_rate_30d = declined_count / len(month_tx) if month_tx else 0.0
        
        last_seen = None
        if user_transactions:
            last_tx = max(user_transactions, key=lambda x: x.timestamp)
            last_seen = last_tx.timestamp
        
        return UserRiskProfile(
            userId=user_id,
            txCount_24h=tx_count_24h,
            gmv_24h=gmv_24h,
            distinctDevices_24h=len(devices),
            distinctIps_24h=len(ips),
            distinctCities_24h=len(cities),
            declineRate_30d=decline_rate_30d,
            lastSeenAt=last_seen
        )
        
    except Exception as e:
        if isinstance(e, (UserRiskProfileAccessException, InvalidUUIDException)):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при получении профиля риска: {str(e)}'
        )
