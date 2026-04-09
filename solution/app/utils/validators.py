def validate_password(cls, v):
    special_characters = "!@#$%^&*_"
    min_pass_len= 8

    if len(v) < min_pass_len:
        raise ValueError(f'Минимум {min_pass_len} символов')
    if not any(c.isupper() for c in v):
        raise ValueError('Нужна хотя бы одна заглавная буква')
    if not any(c.isdigit() for c in v):
        raise ValueError('Нужна хотя бы одна цифра')
    if not any(c in special_characters for c in v):
        raise ValueError(f'Нужен хотя бы один из спецсимволов:{special_characters}')
    return v
