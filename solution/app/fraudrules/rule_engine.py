from datetime import datetime

from ..enums.enums import TransactionStatus
from ..utils.dsl_validator import validate_dsl_expression
from .schemas import FraudRule

def fraud_rule_to_dto(rule):
    return FraudRule.model_validate({
        'id': rule.id,
        'name': rule.name,
        'description': rule.description,
        'dslExpression': rule.dsl_expression,
        'enabled': rule.enabled,
        'priority': rule.priority,
        'createdAt': rule.created_at,
        'updatedAt': rule.updated_at
    })

def get_rule_data(rule):
    if isinstance(rule, dict):
        return {
            "id": rule.get("id"),
            "name": rule.get("name", ""),
            "priority": rule.get("priority", 100),
            "dsl_expression": rule.get("dslExpression", ""),
            "enabled": rule.get("enabled", True)
        }
    else:
        return {
            "id": rule.id,
            "name": rule.name,
            "priority": rule.priority,
            "dsl_expression": rule.dsl_expression,
            "enabled": rule.enabled
        }

def make_rule_result(rule_data, matched, description):
    return {
        "ruleId": rule_data["id"],
        "ruleName": rule_data["name"],
        "priority": rule_data["priority"],
        "enabled": rule_data["enabled"],
        "matched": matched,
        "description": description
    }

def get_field_val(field, ctx):
    if field == "amount":
        return ctx.transaction.get("amount")
    elif field == "user.age":
        user_data = ctx.transaction.get("user", {})
        age_val = user_data.get("age")
        if age_val is not None:
            try:
                return int(age_val)
            except (ValueError, TypeError):
                return age_val
        return age_val
    elif field == "user.score":
        user_data = ctx.transaction.get("user", {})
        return user_data.get("score")
    elif field == "currency":
        return ctx.transaction.get("currency")
    elif field == "merchantId":
        return ctx.transaction.get("merchantId")
    else:
        return None

def compare_vals(field_val, op, val):
    if field_val is None:
        return False

    try:
        field_num = float(field_val)
        val_num = float(val)
    except (ValueError, TypeError):
        if op == "==":
            return str(field_val) == str(val)
        elif op == "!=":
            return str(field_val) != str(val)
        return False

    if op == ">":
        return field_num > val_num
    elif op == ">=":
        return field_num >= val_num
    elif op == "<":
        return field_num < val_num
    elif op == "<=":
        return field_num <= val_num
    elif op == "==":
        return field_num == val_num
    elif op == "!=":
        return field_num != val_num
    else:
        return False

class RuleEvaluationContext:
    
    def __init__(self, transaction, user=None, metadata=None):
        self.transaction = transaction
        self.user = user or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class RuleEngine:
    
    def __init__(self):
        self.tier_level = 1
    
    def evaluate_transaction(self, tx_data, rules, user_ctx=None):
        ctx = RuleEvaluationContext(tx_data, user_ctx)

        active_rules = [r for r in rules if r.enabled]

        sorted_rules = sorted(active_rules, key=lambda r: (r.priority, r.id))
        
        results = []
        for rule in sorted_rules:
            result = self._eval_rule(rule, ctx)
            results.append(result)
        
        return results
    
    def _eval_rule(self, rule, ctx):
        rule_data = get_rule_data(rule)
        
        try:
            if self.tier_level == 0:
                return make_rule_result(rule_data, False, "DSL disabled")

            is_valid, norm_expr, errors = validate_dsl_expression(rule_data["dsl_expression"], self.tier_level)
            if not is_valid or errors:
                err_msg = "Rule validation failed: " + ', '.join([e.message for e in errors])
                return make_rule_result(rule_data, False, err_msg)

            matched = self._parse_and_eval(norm_expr, ctx)
            desc = f"Rule {rule_data['name']} triggered" if matched else f"Rule {rule_data['name']} not triggered"
            
            return make_rule_result(rule_data, matched, desc)
        except Exception as e:
            return make_rule_result(
                rule_data, False, 
                f"Rule error: {str(e)}"
            )
    
    def _parse_and_eval(self, expr, ctx):
        try:
            parts = expr.split(' ')
            if len(parts) != 3:
                return False

            field, op, val = parts
            field_val = get_field_val(field, ctx)
            
            result = compare_vals(field_val, op, val)
            
            return result
        except Exception as e:
            return False

    def determine_transaction_status(self, rule_results):
        for result in rule_results:
            if result.get("matched", False):
                return TransactionStatus.DECLINED
        
        return TransactionStatus.APPROVED
