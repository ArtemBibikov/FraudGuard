from fastapi import APIRouter, Depends, status
from uuid import UUID
from ..utils.dsl_validator import validate_dsl_expression
from .exceptions import (
    RuleNameAlreadyExistsException,
    RuleNotFoundException
)
from .schemas import FraudRuleCreateRequest, FraudRuleUpdateRequest
from .dao import FraudRuleDAO
from .rule_engine import fraud_rule_to_dto

router = APIRouter(
    prefix='/fraud-rules',
    tags=['Fraud Rules']
)

@router.post('', status_code=status.HTTP_201_CREATED)
async def create_fraud_rule(rule_data: FraudRuleCreateRequest):
    existing_rule = await FraudRuleDAO.find_one_or_none(name=rule_data.name)
    if existing_rule:
        raise RuleNameAlreadyExistsException
    
    new_rule = await FraudRuleDAO.add(
        name=rule_data.name,
        description=rule_data.description,
        dsl_expression=rule_data.dslExpression,
        enabled=rule_data.enabled,
        priority=rule_data.priority
    )
    return fraud_rule_to_dto(new_rule)

@router.get('')
async def list_fraud_rules():
    rules = await FraudRuleDAO.find_all()
    sorted_r = sorted(rules, key=lambda x: (x.priority, x.id))
    
    return [fraud_rule_to_dto(rule) for rule in sorted_r]

@router.get('/{rule_id}')
async def get_fraud_rule(rule_id: str):
    rule_uuid = UUID(rule_id)
    rule = await FraudRuleDAO.find_by_id(rule_uuid)
    if not rule:
        raise RuleNotFoundException
    
    return fraud_rule_to_dto(rule)

@router.put('/{rule_id}')
async def update_fraud_rule(rule_id: str, rule_update: FraudRuleUpdateRequest):
    rule_uuid = UUID(rule_id)
    
    existing_rule = await FraudRuleDAO.find_one_or_none(name=rule_update.name)
    if existing_rule and existing_rule.id != rule_uuid:
        raise RuleNameAlreadyExistsException
    
    updated_rule = await FraudRuleDAO.update(
        rule_uuid,
        name=rule_update.name,
        description=rule_update.description,
        dsl_expression=rule_update.dslExpression,
        enabled=rule_update.enabled,
        priority=rule_update.priority
    )
    
    if not updated_rule:
        raise RuleNotFoundException
    return fraud_rule_to_dto(updated_rule)

@router.delete('/{rule_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_fraud_rule(rule_id: str):
    rule_uuid = UUID(rule_id)
    updated_rule = await FraudRuleDAO.update(
        rule_uuid,
        enabled=False
    )
    if not updated_rule:
        raise RuleNotFoundException
    
    return

@router.post('/validate')
async def validate_rule(dsl_data: dict):
    dsl_expression = dsl_data.get("dslExpression", "")
    is_valid, normalized_expression, errors = validate_dsl_expression(dsl_expression, tier_level=2)
    
    error_list = []
    for error in errors:
        error_dict = {
            "code": error.code,
            "message": error.message
        }
        if error.position is not None:
            error_dict["position"] = error.position
        if error.near is not None:
            error_dict["near"] = error.near
        error_list.append(error_dict)
    
    return {
        "isValid": is_valid,
        "normalizedExpression": normalized_expression if is_valid else None,
        "errors": error_list
    }
