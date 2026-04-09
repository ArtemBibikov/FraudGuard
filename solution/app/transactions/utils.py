MAX_AMOUNT = 999999999.99
HIGH_AMOUNT_THRESHOLD = 10000
MAX_BATCH_SIZE = 500
HIGH_RISK_COUNTRIES = ['US', 'GB', 'DE', 'FR', 'CA', 'AU']

def check_lat_range(v):
    if v is not None and (v < -90 or v > 90):
        raise ValueError('должно быть между -90 и 90')
    return v

def check_lon_range(v):
    if v is not None and (v< -180 or v > 180):
        raise ValueError('должно быть между -180 и 180')
    return v

def check_cords_pair(values):
    lat = values.latitude
    lon = values.longitude
    if (lat is not None) != (lon is not None):
        raise ValueError('широта и долгота должны быть предоставлены вместе')
    return values

def check_amount_range(v):
    if v <= 0:
        raise ValueError('должно быть больше 0')
    if v > MAX_AMOUNT:
        raise ValueError(f'должно быть меньше или равно {MAX_AMOUNT}')
    return v

def format_transaction_amount(amount):
    return float(amount)

def is_high_risk_country(country_code):
    return country_code in HIGH_RISK_COUNTRIES

def get_transaction_risk_score(transaction):
    score = 0
    if transaction.amount > HIGH_AMOUNT_THRESHOLD:
        score += 2
    if hasattr(transaction, 'ipAddress') and transaction.ipAddress:
        score += 1
    if hasattr(transaction, 'deviceId') and transaction.deviceId:
        score += 1
    if hasattr(transaction, 'location') and transaction.location and transaction.location.country:
        if is_high_risk_country(transaction.location.country):
            score += 3
    return score
