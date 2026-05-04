# config.py
TOKEN = "8665227013:AAE8UMjSfkKW8MSVgPdVbNzKmB5TiE7uoV0"
CRYPTOBOT_TOKEN = "576552:AAp0twvCmv4pUhhgm683APimOYaWSPGRgbp"
ADMIN_ID = 8386036325
USD_TO_UAH = 41.0

# USDT кошельки
USDT_TRC20 = "TG2atiWnGwwwx8v4eMhaeXtNPyoidNJsEj"
USDT_BEP20 = "0xF471b13F7F96acb31B6284a8260eBa2F3Bd98CdD"
USDT_TON = "UQDFRVfhZ_GHs7dlpEGMAec-2Jc6wAdcjwU9YwSOLBYCZMc_"

# Карта
CARD_NUMBER = "4441 1110 6724 1608"

# Минимальные суммы
MIN_DEPOSIT_UAH = 200
MIN_DEPOSIT_USDT = 5
MIN_ORDER_COUNT = 200
MAX_ORDER_COUNT = 1000000

# Бонусы
DEPOSIT_BONUSES = [
    {"min_uah": 0, "min_usdt": 0, "bonus": 0},
    {"min_uah": 500, "min_usdt": 12.5, "bonus": 3},
    {"min_uah": 1000, "min_usdt": 25, "bonus": 5},
    {"min_uah": 2000, "min_usdt": 50, "bonus": 7},
    {"min_uah": 3500, "min_usdt": 87.5, "bonus": 8},
    {"min_uah": 5000, "min_usdt": 125, "bonus": 10},
]

def get_deposit_bonus(amount_uah=None, amount_usdt=None):
    if amount_usdt:
        amount = amount_usdt * USD_TO_UAH
    else:
        amount = amount_uah or 0
    for lvl in reversed(DEPOSIT_BONUSES):
        if amount >= lvl["min_uah"]:
            return lvl["bonus"]
    return 0

def get_bonus_info(amount):
    current_bonus = 0
    next_level = None
    for b in DEPOSIT_BONUSES:
        if amount >= b["min_uah"]:
            current_bonus = b["bonus"]
        elif next_level is None:
            next_level = b
    if next_level:
        next_need = next_level["min_uah"] - amount
        next_bonus = next_level["bonus"]
        return current_bonus, next_need, next_bonus
    return current_bonus, 0, 0