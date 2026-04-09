from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
from uuid import UUID
from pydantic import ValidationError
import json

from .schemas import (
    TransactionCreateRequest,
    TransactionResponse,
    TransactionLocation,
    TransactionDecision,
    PagedTransactions,
    TransactionBatchResult,
    TransactionBatchResultItem,
)
from ..fraudrules.dao import FraudRuleDAO
from ..dependencies import get_current_user
from ..fraudrules.rule_engine import RuleEngine
from ..enums.enums import TransactionStatus
from .dao import TransactionDAO
from ..users.dao import UserDAO

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_transaction(transaction_data: TransactionCreateRequest, current_user=Depends(get_current_user)):
    user_id = current_user.id if current_user.role == "USER" else transaction_data.userId
    
    if current_user.role == "ADMIN" and not user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="userId is required for admin",
        )
    
    user = await UserDAO.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "User not found",
                "details": {"userId": str(user_id)},
            },
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is deactivated",
        )
    
    new_transaction = await TransactionDAO.add(
        userId=user_id,
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        merchantId=transaction_data.merchantId,
        merchantCategoryCode=transaction_data.merchantCategoryCode,
        timestamp=transaction_data.timestamp,
        ipAddress=transaction_data.ipAddress,
        deviceId=transaction_data.deviceId,
        channel=transaction_data.channel.value if transaction_data.channel else None,
        transaction_metadata=str(
            {
                "location": transaction_data.location.dict() if transaction_data.location else None,
                "metadata": transaction_data.metadata,
            }
        )
        if (transaction_data.location or transaction_data.metadata)
        else None,
    )
    
    rule_engine = RuleEngine()
    rules_list = await FraudRuleDAO.find_all(page=0, size=1000, enabled=True)
    
    transaction_context = {
        **new_transaction.__dict__,
        "user": {
            "id": str(user.id),
            "age": user.age,
            "region": user.region,
            "gender": user.gender.value if user.gender else None,
            "maritalStatus": user.marital_status.value if user.marital_status else None,
            "role": user.role.value,
            "isActive": user.is_active,
        }
    }
    
    rule_results = rule_engine.evaluate_transaction(transaction_context, rules_list)
    
    transaction_status = rule_engine.determine_transaction_status(rule_results)
    
    def _serialize_uuids(obj):
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: _serialize_uuids(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_serialize_uuids(item) for item in obj]
        else:
            return obj

    updated_transaction = await TransactionDAO.update(
        new_transaction.id,
        status=transaction_status,
        isFraud=transaction_status == TransactionStatus.DECLINED,
        transaction_metadata=json.dumps(
            _serialize_uuids({
                "ruleResults": rule_results,
                "location": transaction_data.location.dict() if transaction_data.location else None,
                "metadata": transaction_data.metadata,
            })
        ),
    )
    
    return TransactionDecision(
        transaction=TransactionResponse(
            id=updated_transaction.id,
            userId=updated_transaction.userId,
            amount=updated_transaction.amount,
            currency=updated_transaction.currency,
            status=updated_transaction.status,
            merchantId=updated_transaction.merchantId,
            merchantCategoryCode=updated_transaction.merchantCategoryCode,
            timestamp=updated_transaction.timestamp,
            ipAddress=updated_transaction.ipAddress,
            deviceId=updated_transaction.deviceId,
            channel=updated_transaction.channel,
            isFraud=updated_transaction.isFraud,
            location=transaction_data.location,
            metadata=transaction_data.metadata,
            createdAt=updated_transaction.createdAt,
            updatedAt=updated_transaction.updatedAt,
        ),
        ruleResults=rule_results,
    )

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, current_user=Depends(get_current_user)):
    transaction_uuid = UUID(transaction_id)
    transaction = await TransactionDAO.find_by_id(transaction_uuid)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    if current_user.role == "USER" and str(transaction.userId) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="USER can only access their own transactions",
        )
    
    metadata_dict = {}
    if transaction.transaction_metadata:
        try:
            metadata_dict = json.loads(transaction.transaction_metadata)
        except Exception:
            metadata_dict = {}

    location_obj = None
    if metadata_dict.get("location"):
        try:
            location_obj = TransactionLocation(**metadata_dict["location"])
        except Exception:
            location_obj = None

    rule_results = metadata_dict.get("ruleResults", [])

    return TransactionDecision(
        transaction=TransactionResponse(
            id=transaction.id,
            userId=transaction.userId,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            merchantId=transaction.merchantId,
            merchantCategoryCode=transaction.merchantCategoryCode,
            timestamp=transaction.timestamp,
            ipAddress=transaction.ipAddress,
            deviceId=transaction.deviceId,
            channel=transaction.channel,
            isFraud=transaction.isFraud,
            location=location_obj,
            metadata=metadata_dict.get("metadata"),
            createdAt=transaction.createdAt,
            updatedAt=transaction.updatedAt,
        ),
        ruleResults=rule_results,
    )

@router.get("")
async def list_transactions(
    page: int = Query(0),
    size: int = Query(20),
    userId: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    isFraud: Optional[bool] = Query(None),
    current_user=Depends(get_current_user),
):
    if current_user.role == "USER" and userId and userId != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="USER can only view their own transactions",
        )

    transactions = await TransactionDAO.find_all()

    filtered_transactions = []
    for tx in transactions:
        include_tx = True

        if current_user.role == "USER" and tx.userId != current_user.id:
            include_tx = False
        if userId and tx.userId != UUID(userId):
            include_tx = False
        if status and tx.status != status:
            include_tx = False
        if isFraud is not None and tx.isFraud != isFraud:
            include_tx = False

        if include_tx:
            metadata_dict = {}
            if tx.transaction_metadata:
                try:
                    metadata_dict = json.loads(tx.transaction_metadata)
                except Exception:
                    metadata_dict = {}

            location_obj = None
            if metadata_dict.get("location"):
                try:
                    location_obj = TransactionLocation(**metadata_dict["location"])
                except Exception:
                    location_obj = None

            filtered_transactions.append(
                TransactionResponse(
                    id=tx.id,
                    userId=tx.userId,
                    amount=tx.amount,
                    currency=tx.currency,
                    status=tx.status,
                    merchantId=tx.merchantId,
                    merchantCategoryCode=tx.merchantCategoryCode,
                    timestamp=tx.timestamp,
                    ipAddress=tx.ipAddress,
                    deviceId=tx.deviceId,
                    channel=tx.channel,
                    isFraud=tx.isFraud,
                    location=location_obj,
                    metadata=metadata_dict.get("metadata"),
                    createdAt=tx.createdAt,
                    updatedAt=tx.updatedAt,
                )
            )

    filtered_transactions.sort(key=lambda t: (-t.timestamp.timestamp(), 0 if t.status == "DECLINED" else 1, t.id))

    start = page * size
    end = start + size
    page_items = filtered_transactions[start:end]

    return PagedTransactions(
        items=page_items,
        total=len(filtered_transactions),
        page=page,
        size=size,
    )

@router.post("/batch")
async def create_batch_transactions(batch_data: dict, current_user=Depends(get_current_user)):
    results = []
    rule_engine = RuleEngine()
    
    items = batch_data.get("items", []) or []
    for index, item in enumerate(items):
        try:
            try:
                transaction_data = TransactionCreateRequest(**item)
            except ValidationError as e:
                results.append(TransactionBatchResultItem(
                    index=index,
                    decision=None,
                    error={"code": "VALIDATION_FAILED", "message": "Validation failed"}
                ))
                continue
            
            user_id = current_user.id if current_user.role == "USER" else transaction_data.userId
            
            if current_user.role == "USER" and str(current_user.id) != str(transaction_data.userId):
                results.append(TransactionBatchResultItem(
                    index=index,
                    error={"code": "FORBIDDEN", "message": "USER can only create transactions for themselves"}
                ))
                continue
            
            user = await UserDAO.find_by_id(user_id)
            if not user:
                results.append(TransactionBatchResultItem(
                    index=index,
                    error={"code": "NOT_FOUND", "message": "User not found"}
                ))
                continue
            
            if not user.is_active:
                results.append(TransactionBatchResultItem(
                    index=index,
                    error={"code": "FORBIDDEN", "message": "User is deactivated"}
                ))
                continue
            
            if not transaction_data.amount or transaction_data.amount <= 0:
                results.append(TransactionBatchResultItem(
                    index=index,
                    error={"code": "VALIDATION_FAILED", "message": "Amount must be greater than 0"}
                ))
                continue
            
            if not transaction_data.currency:
                results.append(TransactionBatchResultItem(
                    index=index,
                    error={"code": "VALIDATION_FAILED", "message": "Currency is required"}
                ))
                continue
            
            new_transaction = await TransactionDAO.add(
                userId=user_id,
                amount=transaction_data.amount,
                currency=transaction_data.currency,
                merchantId=transaction_data.merchantId,
                merchantCategoryCode=transaction_data.merchantCategoryCode,
                timestamp=transaction_data.timestamp,
                ipAddress=transaction_data.ipAddress,
                deviceId=transaction_data.deviceId,
                channel=transaction_data.channel.value if transaction_data.channel else None,
                transaction_metadata=str(
                    {
                        "location": transaction_data.location.dict() if transaction_data.location else None,
                        "metadata": transaction_data.metadata,
                    }
                )
                if (transaction_data.location or transaction_data.metadata)
                else None,
            )
            
            rules_list = await FraudRuleDAO.find_all(enabled=True)
            
            transaction_context = new_transaction.__dict__.copy()
            transaction_context['user'] = {
                'id': str(user.id),
                'age': user.age,
                'region': user.region,
                'score': getattr(user, 'score', None)
            }
            
            rule_results = rule_engine.evaluate_transaction(transaction_context, rules_list)
            
            transaction_status = rule_engine.determine_transaction_status(rule_results)
            
            updated_transaction = await TransactionDAO.update(
                new_transaction.id,
                status=transaction_status,
                isFraud=(transaction_status == TransactionStatus.DECLINED),
                transaction_metadata=str(
                    {
                        "ruleResults": rule_results,
                        "location": transaction_data.location.dict() if transaction_data.location else None,
                        "metadata": transaction_data.metadata,
                    }
                ),
            )
            
            metadata_dict = {}
            if updated_transaction.transaction_metadata:
                try:
                    metadata_dict = json.loads(updated_transaction.transaction_metadata)
                except:
                    pass
            
            location_obj = None
            if metadata_dict.get("location"):
                try:
                    location_obj = TransactionLocation(**metadata_dict["location"])
                except:
                    pass
            
            results.append(TransactionBatchResultItem(
                index=index,
                decision=TransactionDecision(
                    transaction=TransactionResponse(
                        id=updated_transaction.id,
                        userId=updated_transaction.userId,
                        amount=updated_transaction.amount,
                        currency=updated_transaction.currency,
                        status=updated_transaction.status,
                        merchantId=updated_transaction.merchantId,
                        merchantCategoryCode=updated_transaction.merchantCategoryCode,
                        timestamp=updated_transaction.timestamp,
                        ipAddress=updated_transaction.ipAddress,
                        deviceId=updated_transaction.deviceId,
                        channel=updated_transaction.channel,
                        isFraud=updated_transaction.isFraud,
                        location=location_obj,
                        metadata=metadata_dict.get("metadata"),
                        createdAt=updated_transaction.createdAt,
                        updatedAt=updated_transaction.updatedAt
                    ),
                    ruleResults=rule_results
                )
            ))
            
        except Exception as e:
            results.append(TransactionBatchResultItem(
                index=index,
                decision=None,
                error={"code": "INTERNAL_ERROR", "message": str(e)}
            ))
    
    has_errors = any(item.error is not None for item in results)
    status_code = status.HTTP_207_MULTI_STATUS if has_errors else status.HTTP_201_CREATED
    batch_result = TransactionBatchResult(items=results)
    return JSONResponse(
        content=batch_result.model_dump(mode="json"),
        status_code=status_code,
    )
