# config.py - تنظیمات و ثابت‌های اصلی

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

# اگر RAILWAY_STATIC_URL تنظیم شده باشد، از Webhook استفاده کن
USE_WEBHOOK = bool(WEBHOOK_URL)

# ================================================================
# داده‌های ثابت
# ================================================================

LEVEL_DATA = {
    1: {"required": 0, "minPoints": 5, "maxPoints": 15, "cooldown": 300, "reward": 0, "features": ["شروع ماجراجویی"]},
    2: {"required": 5, "minPoints": 10, "maxPoints": 20, "cooldown": 300, "reward": 50, "features": ["پنجه", "شکار", "دریافت هاپو پوینت"]},
    3: {"required": 15, "minPoints": 15, "maxPoints": 25, "cooldown": 300, "reward": 225, "features": ["هاپو"]},
    4: {"required": 40, "minPoints": 20, "maxPoints": 35, "cooldown": 300, "reward": 500, "features": ["بانک هاپویی"]},
    5: {"required": 75, "minPoints": 25, "maxPoints": 40, "cooldown": 295, "reward": 1000, "features": ["ارتقا بیشتر"]},
    6: {"required": 115, "minPoints": 35, "maxPoints": 50, "cooldown": 295, "reward": 1750, "features": ["ارتقا بیشتر"]},
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

HAPO_NAMES = ['رکس', 'لوسی', 'بارنی', 'مکس', 'بلا', 'چارلی', 'راکی', 'مولی', 'تدی', 'لونا', 'سیمبا', 'نلا', 'بادی', 'مایلو', 'کوکو', 'روبی', 'اسکار', 'جک', 'دِیزی', 'تایسون']
RANK_NAMES = ['تازه‌وارد', 'حرفه‌ای', 'استاد', 'افسانه', 'بی‌نهایت']

HAPO_CAPACITY = {i: 500 * i for i in range(1, 26)}
HAPO_CAPACITY.update({5: 20000, 10: 50000, 15: 150000, 20: 400000, 25: 650000})

HAPO_PRODUCTION = {i: 0.1 + (i-1) * 0.5 for i in range(1, 26)}
HAPO_PRODUCTION.update({5: 2.0, 10: 4.5, 15: 7.0, 20: 9.5, 25: 12.0})

HAPO_LEVEL_PRICES = {
    1: 250, 2: 500, 3: 5000, 4: 7500, 5: 15000,
    6: 25000, 7: 50000, 8: 75000, 9: 150000, 10: 300000,
    11: 500000, 12: 750000, 13: 1000000, 14: 1500000, 15: 2500000,
    16: 5000000, 17: 7500000, 18: 10000000, 19: 15000000, 20: 20000000,
    21: 25000000, 22: 30000000, 23: 35000000, 24: 40000000, 25: 50000000
}

RANK_UP_PRICES = [15000, 150000, 1500000, 15000000]

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
# عکس‌های پنجه (هر سطح) - آدرس مستقیم از GitHub
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
JAIL_DURATION_SPAM = 15 * 60
JAIL_DURATION_MEOW = 5 * 60
JAIL_FINE_SPAM = 3750
JAIL_FINE_MEOW = 1250
JAIL_MAX_SPAM_COMMANDS = 5
JAIL_SPAM_WINDOW = 10
JAIL_VOTE_DURATION = 60
JAIL_VOTE_NEEDED = 3
JAIL_MEOW_COOLDOWN = 60

# ================================================================
# تنظیمات هاپوی خیابونی
# ================================================================

STREET_HAPO_INTERVAL = 6 * 3600  # هر ۶ ساعت یکبار (به ثانیه)
STREET_HAPO_DECISION_TIME = 60  # ۶۰ ثانیه فرصت برای نجات
STREET_HAPO_MAX_ATTEMPTS = 3  # حداکثر ۳ تلاش
STREET_HAPO_SUCCESS_CHANCE = 0.30  # ۳۰% شانس موفقیت

STREET_HAPO_COSTS = [50, 75, 100]  # هزینه هر تلاش (اول، دوم، سوم)

STREET_HAPO_REWARD_MIN = 500  # حداقل جایزه موفقیت
STREET_HAPO_REWARD_MAX = 999  # حداکثر جایزه موفقیت

STREET_HAPO_FAIL_MESSAGES = [
    "{name} باعث شد هاپوی خیابونی از ترس سکته کنه 💔",
    "{name} باعث شد هاپوی خیابونی زیر برف از سرما یخ بزنه ❄️",
    "{name} هاپوی خیابونی رو ترسوند و باعث شد بمیره 😱",
    "هاپوی خیابونی مرد، فقط مرد بدون هیچ دلیلی 🖤",
    "{name} باعث شد با یک گربه وحشی درگیر بشه و بمیره 🐱⚔️"
]

STREET_HAPO_IMAGE_URL = "https://raw.githubusercontent.com/KnoX4545/HopDog/main/street_hapo.jpg"

# ================================================================
# سایر تنظیمات
# ================================================================

ADMIN_PASSWORD = "9061"
HUNT_DECISION_TIMER = 60
MIN_MEMBERS_TO_STAY = 5
