import re

class DSLError(Exception):
    def __init__(self, message, code="DSL_ERROR", position=None, near=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.position = position
        self.near = near

def check_dsl(expr, tier=0):
    if tier == 0:
        raise DSLError("DSL не поддерживается на этом уровне", "DSL_UNSUPPORTED_TIER")
    
    if not expr or not expr.strip():
        raise DSLError("Пустое выражение", "DSL_PARSE_ERROR", 0, expr)

    expr = re.sub(r'\s+', ' ', expr.strip())
    
    if tier >= 2 and ('AND' in expr or 'OR' in expr):
        expr = expr.replace('(', '').replace(')', '')
        expr = re.sub(r'\s+', ' ', expr.strip())
        expr = expr.replace(' and ', ' AND ').replace(' or ', ' OR ')
        return expr
    
    parts = expr.split()
    if len(parts) != 3:
        raise DSLError("Нужно: поле оператор значение", "DSL_PARSE_ERROR", 0, expr)
    
    field, op, val = parts
    
    allowed_fields = ['amount', 'currency', 'merchantId', 'user.age', 'user.score']
    if field not in allowed_fields:
        raise DSLError(f"Поле {field} не поддерживается", "DSL_INVALID_FIELD", expr.find(field), field)
    
    if op not in ['>', '>=', '<', '<=', '==', '!=']:
        raise DSLError(f"Оператор {op} не поддерживается", "DSL_INVALID_OPERATOR", expr.find(op), op)
    
    if field in ['amount', 'user.age', 'user.score']:
        try:
            float(val)
        except:
            raise DSLError(f"Для поля {field} нужно число", "DSL_INVALID_OPERATOR", expr.find(val), val)
    else:
        if not (val.startswith("'") and val.endswith("'")):
            raise DSLError("Строки в кавычках", "DSL_PARSE_ERROR", expr.find(val), val)
    
    return expr

def validate_dsl_expression(expression, tier_level=0):
    try:
        result = check_dsl(expression, tier_level)
        return True, result, []
    except DSLError as e:
        return False, None, [e]
