# config.py - تنظیمات و ثابت‌های اصلی (نسخه نهایی کامل)

import os
from datetime import timedelta

# ================================================================
# تنظیمات اولیه
# ================================================================

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

# ================================================================
# تنظیمات Webhook (برای Railway)
# ================================================================

WEBHOOK_PORT = int(os.environ.get("PORT", 8443))
WEBHOOK_URL = os.environ.get("RAILWAY_STATIC_URL", "")

USE_WEBHOOK = bool(WEBHOOK_URL)

# ================================================================
# داده‌های ثابت سطح کاربران
# ================================================================

LEVEL_DATA = {
    1: {"required": 0, "minPoints": 5, "maxPoints": 15, "cooldown": 300, "reward": 0, "features": ["شروع ماجراجویی"]},
    2: {"required": 5, "minPoints": 10, "maxPoints": 20, "cooldown": 300, "reward": 50, "features": ["پنجه", "شکار", "دریافت هاپو پوینت"]},
    3: {"required": 15, "minPoints": 15, "maxPoints": 25, "cooldown": 300, "reward": 225, "features": ["هاپو", "انتقال هاپویی"]},
    4: {"required": 40, "minPoints": 20, "maxPoints": 35, "cooldown": 300, "reward": 500, "features": ["بانک هاپویی"]},
    5: {"required": 75, "minPoints": 25, "maxPoints": 40, "cooldown": 295, "reward": 1000, "features": ["یخچال هاپویی", "ارتقا بیشتر"]},
    6: {"required": 115, "minPoints": 35, "maxPoints": 50, "cooldown": 295, "reward": 1750, "features": ["قاچاق هاپویی", "ارتقا بیشتر"]},
    7: {"required": 175, "minPoints": 50, "maxPoints": 75, "cooldown": 295, "reward": 2500, "features": ["ارتقا بیشتر"]},
    8: {"required": 250, "minPoints": 75, "maxPoints": 100, "cooldown": 295, "reward": 3450, "features": ["ارتقا بیشتر"]},
    9: {"required": 350, "minPoints": 100, "maxPoints": 125, "cooldown": 295, "reward": 4625, "features": ["ارتقا بیشتر"]},
    10: {"required": 475, "minPoints": 125, "maxPoints": 175, "cooldown": 290, "reward": 6000, "features": ["ارتقا بیشتر"]},
    11: {"required": 625, "minPoints": 150, "maxPoints": 225, "cooldown": 290, "reward": 7500, "features": ["ارتقا بیشتر"]},
    12: {"required": 800, "minPoints": 175, "maxPoints": 275, "cooldown": 290, "reward": 9250, "features": ["ارتقا بیشتر"]},
    13: {"required": 975, "minPoints": 200, "maxPoints": 325, "cooldown": 290, "reward": 11250, "features": ["ارتقا بیشتر"]},
    14: {"required": 1175, "minPoints": 225, "maxPoints": 375, "cooldown": 290, "reward": 13400, "features": ["ارتقا بیشتر"]},
    15: {"required": 1400, "minPoints": 250, "maxPoints": 425, "cooldown": 285, "reward": 15750, "features": ["ارتقا بیشتر"]},
    16: {"required": 1650, "minPoints": 275, "maxPoints": 475, "cooldown": 285, "reward": 18250, "features": ["ارتقا بیشتر"]},
    17: {"required": 1925, "minPoints": 300, "maxPoints": 525, "cooldown": 285, "reward": 21000, "features": ["ارتقا بیشتر"]},
    18: {"required": 2225, "minPoints": 325, "maxPoints": 575, "cooldown": 285, "reward": 24000, "features": ["ارتقا بیشتر"]},
    19: {"required": 2550, "minPoints": 350, "maxPoints": 625, "cooldown": 285, "reward": 27250, "features": ["ارتقا بیشتر"]},
    20: {"required": 2900, "minPoints": 375, "maxPoints": 675, "cooldown": 280, "reward": 30500, "features": ["نهایی"]},
}
MAX_LEVEL = 20

# ================================================================
# سیستم هاپو - کامل
# ================================================================

# اسامی هاپو (تصادفی)
HAPO_NAMES = ['رکس', 'لوسی', 'بارنی', 'مکس', 'بلا', 'چارلی', 'راکی', 'مولی', 'تدی', 'لونا', 'سیمبا', 'نلا', 'بادی', 'مایلو', 'کوکو', 'روبی', 'اسکار', 'جک', 'دِیزی', 'تایسون']

# اسامی مقام‌ها با عدد داخل پرانتز
RANK_NAMES = [
    "تازه‌وارد (0)",   # Rank 0 - سقف سطح 5
    "حرفه‌ای (1)",     # Rank 1 - سقف سطح 10
    "استاد (2)",       # Rank 2 - سقف سطح 15
    "افسانه (3)",      # Rank 3 - سقف سطح 20
    "بی‌نهایت (4)"     # Rank 4 - سقف سطح 25
]

# هزینه ارتقا مقام (از مقام 0 به 1، 1 به 2، 2 به 3، 3 به 4)
RANK_UP_PRICES = [15000, 150000, 1500000, 15000000]

# ظرفیت هاپو بر اساس سطح کل (1 تا 25)
HAPO_CAPACITY = {
    1: 500, 2: 5000, 3: 10000, 4: 15000, 5: 20000,
    6: 25000, 7: 30000, 8: 35000, 9: 40000, 10: 50000,
    11: 70000, 12: 90000, 13: 110000, 14: 130000, 15: 150000,
    16: 170000, 17: 190000, 18: 200000, 19: 300000, 20: 400000,
    21: 450000, 22: 500000, 23: 550000, 24: 600000, 25: 650000
}

# تولید هاپو در ثانیه بر اساس سطح کل (1 تا 25)
HAPO_PRODUCTION = {
    1: 0.1, 2: 0.2, 3: 1.0, 4: 1.5, 5: 2.0,
    6: 2.5, 7: 3.0, 8: 3.5, 9: 4.0, 10: 4.5,
    11: 5.0, 12: 5.5, 13: 6.0, 14: 6.5, 15: 7.0,
    16: 7.5, 17: 8.0, 18: 8.5, 19: 9.0, 20: 9.5,
    21: 10.0, 22: 10.5, 23: 11.0, 24: 11.5, 25: 12.0
}

# ================================================================
# هزینه ارتقا سطح هاپو (مستقل از مقام) - فقط 1 تا 20
# ================================================================

HAPO_LEVEL_PRICES = {
    1: 250,      # سطح 1 → 2
    2: 500,      # سطح 2 → 3
    3: 5000,     # سطح 3 → 4
    4: 15000,    # سطح 4 → 5
    5: 25000,    # سطح 5 → 6
    6: 50000,    # سطح 6 → 7
    7: 75000,    # سطح 7 → 8
    8: 150000,   # سطح 8 → 9
    9: 300000,   # سطح 9 → 10
    10: 500000,  # سطح 10 → 11
    11: 750000,  # سطح 11 → 12
    12: 1000000, # سطح 12 → 13
    13: 1500000, # سطح 13 → 14
    14: 2500000, # سطح 14 → 15
    15: 5000000, # سطح 15 → 16
    16: 7500000, # سطح 16 → 17
    17: 10000000, # سطح 17 → 18
    18: 15000000, # سطح 18 → 19
    19: 20000000, # سطح 19 → 20
}

# ================================================================
# سیستم پنجه و شکار
# ================================================================

CLAW_DATA = {
    1: {"cost": 500, "cooldown": 60, "common": 95, "uncommon": 5, "epic": 0, "legendary": 0},
    2: {"cost": 5000, "cooldown": 55, "common": 80, "uncommon": 15, "epic": 5, "legendary": 0},
    3: {"cost": 25000, "cooldown": 50, "common": 60, "uncommon": 25, "epic": 10, "legendary": 5},
    4: {"cost": 75000, "cooldown": 45, "common": 40, "uncommon": 30, "epic": 20, "legendary": 10},
    5: {"cost": 250000, "cooldown": 40, "common": 20, "uncommon": 35, "epic": 30, "legendary": 15},
    6: {"cost": 1000000, "cooldown": 35, "common": 10, "uncommon": 30, "epic": 40, "legendary": 20},
    7: {"cost": 3250000, "cooldown": 30, "common": 5, "uncommon": 25, "epic": 45, "legendary": 25},
}
MAX_CLAW_LEVEL = 7

# ================================================================
# عکس‌های پنجه (هر سطح)
# ================================================================

CLAW_IMAGES = {
    1: "https://raw.githubusercontent.com/KnoX4545/HopDog/main/claw_1.jpg",
    2: "https://raw.githubusercontent.com/KnoX4545/HopDog/main/claw_2.jpg",
    3: "https://raw.githubusercontent.com/KnoX4545/HopDog/main/claw_3.jpg",
    4: "https://raw.githubusercontent.com/KnoX4545/HopDog/main/claw_4.jpg",
    5: "https://raw.githubusercontent.com/KnoX4545/HopDog/main/claw_5.jpg",
    6: "https://raw.githubusercontent.com/KnoX4545/HopDog/main/claw_6.jpg",
    7: "https://raw.githubusercontent.com/KnoX4545/HopDog/main/claw_7.jpg",
}

# ================================================================
# حیوانات شکار
# ================================================================

ANIMALS = {
    "common": [
        {"name": "خرگوش", "emoji": "🐇", "weightMin": 0.25, "weightMax": 0.50, "multiplier": 80, "nutrition": 1},
        {"name": "سنجاب", "emoji": "🐿️", "weightMin": 0.50, "weightMax": 0.99, "multiplier": 60, "nutrition": 1},
        {"name": "جوجه‌تیغی", "emoji": "🦔", "weightMin": 0.10, "weightMax": 0.20, "multiplier": 300, "nutrition": 1},
        {"name": "اردک", "emoji": "🦆", "weightMin": 0.75, "weightMax": 1.45, "multiplier": 50, "nutrition": 1},
    ],
    "uncommon": [
        {"name": "روباه", "emoji": "🦊", "weightMin": 1.00, "weightMax": 1.99, "multiplier": 50, "nutrition": 2},
        {"name": "آهو", "emoji": "🦌", "weightMin": 1.50, "weightMax": 2.50, "multiplier": 40, "nutrition": 2},
        {"name": "گراز", "emoji": "🐗", "weightMin": 2.00, "weightMax": 2.99, "multiplier": 35, "nutrition": 2},
    ],
    "epic": [
        {"name": "گرگ", "emoji": "🐺", "weightMin": 3.00, "weightMax": 4.99, "multiplier": 30, "nutrition": 3},
        {"name": "خرس", "emoji": "🐻", "weightMin": 5.00, "weightMax": 7.99, "multiplier": 20, "nutrition": 3},
        {"name": "پلنگ", "emoji": "🐆", "weightMin": 8.00, "weightMax": 11.99, "multiplier": 20, "nutrition": 3},
    ],
    "legendary": [
        {"name": "اژدها", "emoji": "🐉", "weightMin": 12.00, "weightMax": 17.99, "multiplier": 15, "nutrition": 5},
        {"name": "یونیکورن", "emoji": "🦄", "weightMin": 5.00, "weightMax": 7.99, "multiplier": 20, "nutrition": 5},
        {"name": "فنیکس", "emoji": "🔥", "weightMin": 10.00, "weightMax": 20.00, "multiplier": 10, "nutrition": 5},
        {"name": "نهنگ بزرگ", "emoji": "🐋", "weightMin": 15.00, "weightMax": 25.00, "multiplier": 10, "nutrition": 5},
    ]
}

RARITY_NAMES = {"common": "معمولی", "uncommon": "کمیاب", "epic": "حماسی", "legendary": "افسانه‌ای"}
RARITY_COLORS = {"common": "⚪", "uncommon": "🔵", "epic": "🟣", "legendary": "🟡"}

# ================================================================
# تنظیمات بانک
# ================================================================

BANK_REQUIRED_LEVEL = 4
BANK_PURCHASE_COST = 5000
BANK_INTEREST_RATE = 0.03
BANK_MAX_DAILY_INTEREST = 350000
BANK_INTEREST_HOUR = 6
BANK_ACCOUNT_CHANGE_COST = 1250

# ================================================================
# تنظیمات انتقال هاپویی
# ================================================================

TRANSFER_MIN_AMOUNT = 50
TRANSFER_MAX_AMOUNT = 500000
TRANSFER_COOLDOWN = 30
TRANSFER_MIN_LEVEL_SENDER = 3
TRANSFER_MIN_LEVEL_RECEIVER = 2

# ================================================================
# تنظیمات زندان
# ================================================================

JAIL_REASON_SPAM = "اسپم"
JAIL_REASON_MEOW = "میو میو (گربه بی ادب)"
JAIL_REASON_SMUGGLE = "قاچاق هاپویی ناموفق"
JAIL_DURATION_SPAM = 15 * 60
JAIL_DURATION_MEOW = 5 * 60
JAIL_DURATION_SMUGGLE = 40 * 60
JAIL_FINE_SPAM = 3750
JAIL_FINE_MEOW = 1250
JAIL_FINE_SMUGGLE = 5000
JAIL_MAX_SPAM_COMMANDS = 5
JAIL_SPAM_WINDOW = 10
JAIL_VOTE_DURATION = 60
JAIL_VOTE_NEEDED = 3
JAIL_MEOW_COOLDOWN = 60

# ================================================================
# تنظیمات هاپوی خیابونی
# ================================================================

STREET_HAPO_INTERVAL = 6 * 3600
STREET_HAPO_DECISION_TIME = 60
STREET_HAPO_MAX_ATTEMPTS = 3
STREET_HAPO_SUCCESS_CHANCE = 0.30

STREET_HAPO_COSTS = [50, 75, 100]

STREET_HAPO_REWARD_MIN = 500
STREET_HAPO_REWARD_MAX = 999

STREET_HAPO_FAIL_MESSAGES = [
    "{name} باعث شد هاپوی خیابونی از ترس سکته کنه 💔",
    "{name} باعث شد هاپوی خیابونی زیر برف از سرما یخ بزنه ❄️",
    "{name} هاپوی خیابونی رو ترسوند و باعث شد بمیره 😱",
    "هاپوی خیابونی مرد، فقط مرد بدون هیچ دلیلی 🖤",
    "{name} باعث شد با یک گربه وحشی درگیر بشه و بمیره 🐱⚔️"
]

STREET_HAPO_IMAGE_URL = "https://raw.githubusercontent.com/KnoX4545/HopDog/main/street_hapo.jpg"

# ================================================================
# تنظیمات یخچال هاپویی
# ================================================================

FRIDGE_REQUIRED_LEVEL = 5
FRIDGE_PURCHASE_COST = 32000
FRIDGE_MAX_LEVEL = 5
FRIDGE_CAPACITY = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5
}
FRIDGE_UPGRADE_COSTS = {
    1: 0,
    2: 195000,
    3: 415000,
    4: 750000,
    5: 1200000
}
FRIDGE_COOK_MULTIPLIER_SELL = 10
FRIDGE_COOK_MULTIPLIER_FOOD = 2

# ================================================================
# تنظیمات قاچاق هاپویی
# ================================================================

SMUGGLE_REQUIRED_LEVEL = 6
SMUGGLE_MIN_HAPO = 3
SMUGGLE_MAX_HAPO = 15
SMUGGLE_TIME_PER_HAPO = 1200  # 20 دقیقه به ثانیه
SMUGGLE_REWARD_MIN = 12500
SMUGGLE_REWARD_MAX = 24000
SMUGGLE_JAIL_DURATION = 40 * 60
SMUGGLE_JAIL_FINE = 5000
SMUGGLE_SUCCESS_CHANCE = 0.60
SMUGGLE_FAIL_CHANCE = 0.40

# ================================================================
# تنظیمات بازی‌ها (جدید)
# ================================================================

GAME_REQUIRED_LEVEL = 2
GAME_HOST_REQUIRED_LEVEL = 3
GAME_XO_MIN_BET = 50
GAME_XO_MAX_BET = 1000000
GAME_TURN_TIMEOUT = 60  # 60 ثانیه
GAME_COOLDOWN = 120  # 2 دقیقه بین بازی‌ها
GAME_XO_BOARD_SIZE = 3
GAME_MAX_ACTIVE_GAMES = 50
GAME_CLEANUP_DELAY = 300  # 5 دقیقه بعد از پایان بازی

# ================================================================
# تنظیمات لیدربرد
# ================================================================

LEADERBOARD_MAX_USERS = 250
LEADERBOARD_MAX_GROUPS = 5

# ================================================================
# سایر تنظیمات
# ================================================================

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "9061")
HUNT_DECISION_TIMER = 60
MIN_MEMBERS_TO_STAY = 5
