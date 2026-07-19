# bot.py - فایل اصلی بات تلگرام (نسخه نهایی با همه تغییرات)

import os
import logging
import random
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================================================================
# تنظیمات اولیه
# ================================================================

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")

# ایجاد پوشه داده‌ها در ریشه پروژه
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
print(f"📁 پوشه داده‌ها: {DATA_DIR}")

# ================================================================
# داده‌های ثابت
# ================================================================

LEVEL_DATA = {
    1: {"required": 0, "minPoints": 5, "maxPoints": 15, "cooldown": 300, "reward": 0, "features": ["شروع ماجراجویی"]},
    2: {"required": 5, "minPoints": 10, "maxPoints": 20, "cooldown": 300, "reward": 50, "features": ["پنجه", "شکار"]},
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

BANK_REQUIRED_LEVEL = 4
BANK_PURCHASE_COST = 5000
BANK_INTEREST_RATE = 0.03
BANK_MAX_DAILY_INTEREST = 350000
ADMIN_PASSWORD = "9061"

# ================================================================
# متن‌ها
# ================================================================

WELCOME_PRIVATE = """🐾 ربات سرگرمی هاپویی 🐶

🐕 یه هاپوی بامزه برای گروهت…
کافیه توی گروه هاپ هاپ کنی تا هاپ پوینت بگیری 🐶

⭐️ هاپ پوینت جمع کن و با بقیه رقابت کن
🏆 لیدربرد هاپویی رو فتح کن و پادشاه هاپو ها شو

✨ چرا هاپویی ؟

⚡ پاسخگویی فوق‌العاده سریع
🛠️ عملکرد پایدار و بدون باگ
🔄 آپدیت‌های هفتگی
👥 کامیونیتی فعال و پرانرژی
🚨 پشتیبانی ۲۴ ساعته
🪙 کاملاً رایگان برای همه

🐶 کافیه ربات رو به گروهت اضافه کنی…
بعدش شروع کنی به هاپ هاپ کردن"""

WELCOME_GROUP = """🐕 یه هاپوی ناز اینجاست
...شروع کنید به هاپ هاپ 🐶

دستورات:
🐾 هاپ هاپ - گرفتن هاپو پوینت
📊 وضعیت - مشاهده وضعیت خودت
📚 آکادمی - راهنمای کامل"""

# ================================================================
# کلاس مدیریت بازی با ذخیره‌سازی در فایل
# ================================================================

class HopDogGame:
    def __init__(self, user_id, username=""):
        self.user_id = user_id
        self.username = username
        self.data = self.load_data()
        if not self.data:
            self.reset_data()

    def get_data_file_path(self):
        return os.path.join(DATA_DIR, f"{self.user_id}.json")

    def reset_data(self):
        self.data = {
            "user_id": self.user_id,
            "player_name": self.username or f"کاربر{self.user_id}",
            "hop_point": 0,
            "last_hop_time": 0,
            "level": 1,
            "hop_count": 0,
            "is_admin": False,
            "claw_level": 0,
            "last_hunt_time": 0,
            "hunt_active": False,
            "hapo_owned": False,
            "hapo_name": "",
            "hapo_rank": 0,
            "hapo_level": 1,
            "hapo_food": 4,
            "hapo_harvest": 0,
            "hapo_last_update": datetime.now().timestamp(),
            "bank_opened": False,
            "bank_balance": 0,
            "bank_last_interest_at": 0,
            "has_seen_welcome": False,
            "current_hunt_animal": None,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        self.save_data()

    def load_data(self):
        try:
            file_path = self.get_data_file_path()
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._ensure_fields(data)
                    return data
            return None
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return None

    def _ensure_fields(self, data):
        default_fields = {
            "user_id": self.user_id,
            "player_name": self.username or f"کاربر{self.user_id}",
            "hop_point": 0,
            "last_hop_time": 0,
            "level": 1,
            "hop_count": 0,
            "is_admin": False,
            "claw_level": 0,
            "last_hunt_time": 0,
            "hunt_active": False,
            "hapo_owned": False,
            "hapo_name": "",
            "hapo_rank": 0,
            "hapo_level": 1,
            "hapo_food": 4,
            "hapo_harvest": 0,
            "hapo_last_update": datetime.now().timestamp(),
            "bank_opened": False,
            "bank_balance": 0,
            "bank_last_interest_at": 0,
            "has_seen_welcome": False,
            "current_hunt_animal": None,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        for key, value in default_fields.items():
            if key not in data:
                data[key] = value

    def save_data(self):
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            file_path = self.get_data_file_path()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            return False

    def get_level_data(self, level):
        return LEVEL_DATA.get(level, LEVEL_DATA[1])

    def get_required_for_level(self, level):
        if level >= MAX_LEVEL:
            return float('inf')
        return self.get_level_data(level + 1)["required"]

    def get_cooldown_for_level(self, level):
        return self.get_level_data(level)["cooldown"]

    def do_hop(self):
        now = datetime.now().timestamp()
        cooldown = self.get_cooldown_for_level(self.data["level"])
        
        if self.data["last_hop_time"] > 0 and (now - self.data["last_hop_time"]) < cooldown:
            remaining = cooldown - (now - self.data["last_hop_time"])
            return {"success": False, "remaining": remaining}
        
        level_data = self.get_level_data(self.data["level"])
        earned = random.randint(level_data["minPoints"], level_data["maxPoints"])
        
        self.data["hop_point"] += earned
        self.data["last_hop_time"] = now
        self.data["hop_count"] += 1
        
        required = self.get_required_for_level(self.data["level"])
        if self.data["level"] < MAX_LEVEL and self.data["hop_count"] >= required:
            self.data["hop_count"] = 0
            self.data["level"] += 1
            reward = self.get_level_data(self.data["level"])["reward"]
            self.data["hop_point"] += reward
            self.save_data()
            return {
                "success": True, 
                "earned": earned, 
                "level_up": True, 
                "new_level": self.data["level"],
                "reward": reward
            }
        
        self.save_data()
        return {"success": True, "earned": earned, "level_up": False}

    def get_hapo_total_level(self):
        return self.data["hapo_rank"] * 5 + self.data["hapo_level"]

    def get_hapo_max_food(self):
        return (self.data["hapo_rank"] + 1) * 4

    def get_hapo_capacity(self):
        total = self.get_hapo_total_level()
        return HAPO_CAPACITY.get(total, 500)

    def get_hapo_production(self):
        total = self.get_hapo_total_level()
        return HAPO_PRODUCTION.get(total, 0.1)

    def get_hapo_upgrade_price(self):
        total = self.get_hapo_total_level()
        if total >= 25:
            return float('inf')
        return HAPO_LEVEL_PRICES.get(total + 1, 10000000)

    def get_hapo_food_status(self):
        max_food = self.get_hapo_max_food()
        food = self.data["hapo_food"]
        if food == 0:
            return {"text": "دیگه کار نمیکنم", "speed": 0}
        if food / max_food < 0.25:
            return {"text": "من گشنمه", "speed": 0.5}
        if food / max_food < 0.75:
            return {"text": "شکمم پره", "speed": 1.0}
        return {"text": "عاشقتم", "speed": 1.5}

    def update_hapo_production(self):
        now = datetime.now().timestamp()
        elapsed = now - self.data["hapo_last_update"]
        capacity = self.get_hapo_capacity()
        status = self.get_hapo_food_status()
        
        if self.data["hapo_food"] > 0 and self.data["hapo_harvest"] < capacity:
            gained = self.get_hapo_production() * status["speed"] * elapsed
            self.data["hapo_harvest"] = min(capacity, self.data["hapo_harvest"] + gained)
        
        if self.data["hapo_food"] > 0:
            decay = int((elapsed / (12 * 3600)) * 6)
            if decay > 0:
                self.data["hapo_food"] = max(0, int(self.data["hapo_food"] - decay))
        
        self.data["hapo_last_update"] = now
        self.save_data()

    def buy_hapo(self):
        if self.data["level"] < 3:
            return {"success": False, "reason": "سطح 3 لازم است"}
        if self.data["hop_point"] < 300:
            return {"success": False, "reason": "300 هاپو پوینت لازم است"}
        if self.data["hapo_owned"]:
            return {"success": False, "reason": "شما قبلاً هاپو دارید"}
        
        self.data["hop_point"] -= 300
        self.data["hapo_owned"] = True
        self.data["hapo_name"] = random.choice(HAPO_NAMES)
        self.data["hapo_rank"] = 0
        self.data["hapo_level"] = 1
        self.data["hapo_food"] = self.get_hapo_max_food()
        self.data["hapo_harvest"] = 0
        self.data["hapo_last_update"] = datetime.now().timestamp()
        self.save_data()
        return {"success": True, "name": self.data["hapo_name"]}

    def get_claw_data(self, level):
        return CLAW_DATA.get(level)

    def get_claw_cost(self, level):
        data = self.get_claw_data(level)
        return data["cost"] if data else float('inf')

    def get_claw_cooldown(self, level):
        data = self.get_claw_data(level)
        return data["cooldown"] if data else float('inf')

    def buy_claw(self):
        if self.data["level"] < 2:
            return {"success": False, "reason": "سطح 2 لازم است"}
        if self.data["claw_level"] >= 1:
            return {"success": False, "reason": "شما قبلاً پنجه دارید"}
        
        cost = self.get_claw_cost(1)
        if self.data["hop_point"] < cost:
            return {"success": False, "reason": f"{cost} هاپو پوینت لازم است"}
        
        self.data["hop_point"] -= cost
        self.data["claw_level"] = 1
        self.save_data()
        return {"success": True}

    def upgrade_claw(self):
        current = self.data["claw_level"]
        if current >= MAX_CLAW_LEVEL:
            return {"success": False, "reason": "پنجه در بالاترین سطح است"}
        
        next_level = current + 1
        cost = self.get_claw_cost(next_level)
        if self.data["hop_point"] < cost:
            return {"success": False, "reason": f"{cost} هاپو پوینت لازم است"}
        
        self.data["hop_point"] -= cost
        self.data["claw_level"] = next_level
        self.save_data()
        return {"success": True, "new_level": next_level}

    def get_random_animal(self):
        if self.data["claw_level"] == 0:
            return None
        
        claw_data = self.get_claw_data(self.data["claw_level"])
        rand = random.random() * 100
        
        if rand < claw_data["common"]:
            rarity = "common"
        elif rand < claw_data["common"] + claw_data["uncommon"]:
            rarity = "uncommon"
        elif rand < claw_data["common"] + claw_data["uncommon"] + claw_data["epic"]:
            rarity = "epic"
        else:
            rarity = "legendary"
        
        animals = ANIMALS[rarity]
        animal = random.choice(animals)
        weight = round(animal["weightMin"] + random.random() * (animal["weightMax"] - animal["weightMin"]), 1)
        value = int(weight * animal["multiplier"])
        
        return {
            **animal,
            "rarity": rarity,
            "rarity_name": RARITY_NAMES[rarity],
            "weight": weight,
            "value": value
        }

    def do_hunt(self):
        if self.data["level"] < 2:
            return {"success": False, "reason": "سطح 2 لازم است"}
        if self.data["claw_level"] == 0:
            return {"success": False, "reason": "شما پنجه ندارید"}
        if self.data.get("hunt_active", False):
            return {"success": False, "reason": "در حال شکار هستید"}
        
        cooldown = self.get_claw_cooldown(self.data["claw_level"]) * 60
        now = datetime.now().timestamp()
        if self.data["last_hunt_time"] > 0 and (now - self.data["last_hunt_time"]) < cooldown:
            remaining = cooldown - (now - self.data["last_hunt_time"])
            return {"success": False, "reason": "خسته‌ام", "remaining": remaining}
        
        self.data["last_hunt_time"] = now
        self.data["hunt_active"] = True
        self.save_data()
        
        animal = self.get_random_animal()
        if not animal:
            self.data["hunt_active"] = False
            self.save_data()
            return {"success": False, "reason": "خطا در شکار"}
        
        self.data["hunt_active"] = False
        self.data["current_hunt_animal"] = animal
        self.save_data()
        return {"success": True, "animal": animal}

    def sell_animal(self):
        animal = self.data.get("current_hunt_animal")
        if not animal:
            return {"success": False, "reason": "هیچ حیوانی برای فروش وجود ندارد"}
        value = animal["value"]
        self.data["hop_point"] += value
        self.data["current_hunt_animal"] = None
        self.save_data()
        return {"success": True, "value": value}

    def feed_hapo(self):
        animal = self.data.get("current_hunt_animal")
        if not animal:
            return {"success": False, "reason": "هیچ حیوانی برای غذا دادن وجود ندارد"}
        if not self.data["hapo_owned"]:
            return {"success": False, "reason": "شما هاپو ندارید"}
        
        max_food = self.get_hapo_max_food()
        if self.data["hapo_food"] >= max_food:
            return {"success": False, "reason": "هاپو سیر است"}
        
        nutrition = animal["nutrition"]
        new_food = min(max_food, int(self.data["hapo_food"] + nutrition))
        actual = new_food - int(self.data["hapo_food"])
        self.data["hapo_food"] = new_food
        self.data["current_hunt_animal"] = None
        self.save_data()
        return {"success": True, "fed": actual}

    def open_bank(self):
        if self.data["level"] < BANK_REQUIRED_LEVEL:
            return {"success": False, "reason": f"سطح {BANK_REQUIRED_LEVEL} لازم است"}
        if self.data["bank_opened"]:
            return {"success": False, "reason": "بانک قبلاً باز شده است"}
        if self.data["hop_point"] < BANK_PURCHASE_COST:
            return {"success": False, "reason": f"{BANK_PURCHASE_COST} هاپو پوینت لازم است"}
        
        self.data["hop_point"] -= BANK_PURCHASE_COST
        self.data["bank_opened"] = True
        self.data["bank_balance"] = 0
        self.data["bank_last_interest_at"] = datetime.now().timestamp()
        self.save_data()
        return {"success": True}

    def apply_bank_interest(self):
        if not self.data["bank_opened"]:
            return
        
        now = datetime.now().timestamp()
        if self.data["bank_last_interest_at"] == 0:
            self.data["bank_last_interest_at"] = now
            return
        
        interest = min(int(self.data["bank_balance"] * BANK_INTEREST_RATE), BANK_MAX_DAILY_INTEREST)
        if interest > 0:
            self.data["bank_balance"] += interest
            self.data["bank_last_interest_amount"] = interest
        
        self.data["bank_last_interest_at"] = now
        self.save_data()

    def deposit(self, amount):
        if not self.data["bank_opened"]:
            return {"success": False, "reason": "بانک باز نشده است"}
        if self.data["hop_point"] < amount:
            return {"success": False, "reason": "موجودی قابل استفاده کافی نیست"}
        if amount <= 0:
            return {"success": False, "reason": "مبلغ نامعتبر است"}
        
        self.data["hop_point"] -= amount
        self.data["bank_balance"] += amount
        self.save_data()
        return {"success": True, "new_balance": self.data["bank_balance"]}

    def withdraw(self, amount):
        if not self.data["bank_opened"]:
            return {"success": False, "reason": "بانک باز نشده است"}
        if self.data["bank_balance"] < amount:
            return {"success": False, "reason": "موجودی بانک کافی نیست"}
        if amount <= 0:
            return {"success": False, "reason": "مبلغ نامعتبر است"}
        
        self.data["bank_balance"] -= amount
        self.data["hop_point"] += amount
        self.save_data()
        return {"success": True, "new_balance": self.data["bank_balance"]}

# ================================================================
# دیکشنری کاربران
# ================================================================

user_games = {}

def get_game(user_id, username=""):
    if user_id not in user_games:
        user_games[user_id] = HopDogGame(user_id, username)
    return user_games[user_id]

# ================================================================
# متن‌های راهنما (آکادمی)
# ================================================================

ACADEMY_MAIN = """📚 آکادمی هاپویی ✨

🐾 جایی که هاپوهای کنجکاو جواب سوال‌هاشون رو پیدا میکنن

لطفا بخش مورد نظر را انتخاب کنید ⬇️"""

ACADEMY_SUB_SYSTEM = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️

لطفا بخش مورد نظر را انتخاب کنید ⬇️"""

ACADEMY_SUB_FEATURES = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : قابلیت ها 🔓

لطفا بخش مورد نظر را انتخاب کنید ⬇️"""

ACADEMY_SUB_ADVENTURE = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾

لطفا بخش مورد نظر را انتخاب کنید ⬇️"""

ACADEMY_SYSTEM_PAGE1 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : سطح کاربران 🐾

✨ لیست سطح های موجود کاربران ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 1
┘─ 💰 پوینت : 5 - 15 🪙
┘─ ⏳ زمان : 5:00
┘─ 🔓 قابلیت ها : شروع
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 2
┘─ 🐾 هاپ مورد نیاز : 5
┘─ 💰 پوینت : 10 - 20 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 50 🪙
┘─ 🔓 قابلیت ها : پنجه، شکار
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 3
┘─ 🐾 هاپ مورد نیاز : 15
┘─ 💰 پوینت : 15 - 25 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 225 🪙
┘─ 🔓 قابلیت ها : هاپو
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 4
┘─ 🐾 هاپ مورد نیاز : 40
┘─ 💰 پوینت : 20 - 35 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 500 🪙
┘─ 🔓 قابلیت ها : بانک هاپویی
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 5
┘─ 🐾 هاپ مورد نیاز : 75
┘─ 💰 پوینت : 25 - 40 🪙
┘─ ⏳ زمان : 4:55
┘─ 💝 جایزه ارتقا : 1000 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر"""

ACADEMY_SYSTEM_PAGE2 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : سطح کاربران 🐾

✨ لیست سطح های موجود کاربران ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 6
┘─ 🐾 هاپ مورد نیاز : 115
┘─ 💰 پوینت : 35 - 50 🪙
┘─ ⏳ زمان : 4:55
┘─ 💝 جایزه ارتقا : 1750 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 7
┘─ 🐾 هاپ مورد نیاز : 175
┘─ 💰 پوینت : 50 - 75 🪙
┘─ ⏳ زمان : 4:55
┘─ 💝 جایزه ارتقا : 2500 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 8
┘─ 🐾 هاپ مورد نیاز : 250
┘─ 💰 پوینت : 75 - 100 🪙
┘─ ⏳ زمان : 4:55
┘─ 💝 جایزه ارتقا : 3450 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 9
┘─ 🐾 هاپ مورد نیاز : 350
┘─ 💰 پوینت : 100 - 125 🪙
┘─ ⏳ زمان : 4:55
┘─ 💝 جایزه ارتقا : 4625 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 10
┘─ 🐾 هاپ مورد نیاز : 475
┘─ 💰 پوینت : 125 - 175 🪙
┘─ ⏳ زمان : 4:50
┘─ 💝 جایزه ارتقا : 6000 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر"""

ACADEMY_SYSTEM_PAGE3 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : سطح کاربران 🐾

✨ لیست سطح های موجود کاربران ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 11
┘─ 🐾 هاپ مورد نیاز : 625
┘─ 💰 پوینت : 150 - 225 🪙
┘─ ⏳ زمان : 4:50
┘─ 💝 جایزه ارتقا : 7500 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 12
┘─ 🐾 هاپ مورد نیاز : 800
┘─ 💰 پوینت : 175 - 275 🪙
┘─ ⏳ زمان : 4:50
┘─ 💝 جایزه ارتقا : 9250 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 13
┘─ 🐾 هاپ مورد نیاز : 975
┘─ 💰 پوینت : 200 - 325 🪙
┘─ ⏳ زمان : 4:50
┘─ 💝 جایزه ارتقا : 11250 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 14
┘─ 🐾 هاپ مورد نیاز : 1175
┘─ 💰 پوینت : 225 - 375 🪙
┘─ ⏳ زمان : 4:50
┘─ 💝 جایزه ارتقا : 13400 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 15
┘─ 🐾 هاپ مورد نیاز : 1400
┘─ 💰 پوینت : 250 - 425 🪙
┘─ ⏳ زمان : 4:45
┘─ 💝 جایزه ارتقا : 15750 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر"""

ACADEMY_SYSTEM_PAGE4 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : سطح کاربران 🐾

✨ لیست سطح های موجود کاربران ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 16
┘─ 🐾 هاپ مورد نیاز : 1650
┘─ 💰 پوینت : 275 - 475 🪙
┘─ ⏳ زمان : 4:45
┘─ 💝 جایزه ارتقا : 18250 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 17
┘─ 🐾 هاپ مورد نیاز : 1925
┘─ 💰 پوینت : 300 - 525 🪙
┘─ ⏳ زمان : 4:45
┘─ 💝 جایزه ارتقا : 21000 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 18
┘─ 🐾 هاپ مورد نیاز : 2225
┘─ 💰 پوینت : 325 - 575 🪙
┘─ ⏳ زمان : 4:45
┘─ 💝 جایزه ارتقا : 24000 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 19
┘─ 🐾 هاپ مورد نیاز : 2550
┘─ 💰 پوینت : 350 - 625 🪙
┘─ ⏳ زمان : 4:45
┘─ 💝 جایزه ارتقا : 27250 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 20
┘─ 🐾 هاپ مورد نیاز : 2900
┘─ 💰 پوینت : 375 - 675 🪙
┘─ ⏳ زمان : 4:40
┘─ 💝 جایزه ارتقا : 30500 🪙
┘─ 🔓 قابلیت ها : نهایی"""

ACADEMY_ANIMALS_PAGE1 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : حیوانات 🐾

✨ لیست حیوانات موجود ⬇️

〰️〰️〰️〰️〰️〰️〰️
🐇 خرگوش
⭐ سطح : معمولی
⚖️ وزن : 0.25 - 0.50 کیلو
💰 ارزش : ~20 🪙
🥩 ارزش غذایی : 1 کالری
〰️〰️〰️〰️〰️〰️〰️
🐿️ سنجاب
⭐ سطح : معمولی
⚖️ وزن : 0.50 - 0.99 کیلو
💰 ارزش : ~30 🪙
🥩 ارزش غذایی : 1 کالری
〰️〰️〰️〰️〰️〰️〰️
🦔 جوجه‌تیغی
⭐ سطح : معمولی
⚖️ وزن : 0.10 - 0.20 کیلو
💰 ارزش : ~30 🪙
🥩 ارزش غذایی : 1 کالری
〰️〰️〰️〰️〰️〰️〰️
🦆 اردک
⭐ سطح : معمولی
⚖️ وزن : 0.75 - 1.45 کیلو
💰 ارزش : ~50 🪙
🥩 ارزش غذایی : 1 کالری
〰️〰️〰️〰️〰️〰️〰️
🦊 روباه
⭐ سطح : کمیاب
⚖️ وزن : 1.00 - 1.99 کیلو
💰 ارزش : ~75 🪙
🥩 ارزش غذایی : 2 کالری"""

ACADEMY_ANIMALS_PAGE2 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : حیوانات 🐾

✨ لیست حیوانات موجود ⬇️

〰️〰️〰️〰️〰️〰️〰️
🦌 آهو
⭐ سطح : کمیاب
⚖️ وزن : 1.50 - 2.50 کیلو
💰 ارزش : ~80 🪙
🥩 ارزش غذایی : 2 کالری
〰️〰️〰️〰️〰️〰️〰️
🐗 گراز
⭐ سطح : کمیاب
⚖️ وزن : 2.00 - 2.99 کیلو
💰 ارزش : ~80 🪙
🥩 ارزش غذایی : 2 کالری
〰️〰️〰️〰️〰️〰️〰️
🐺 گرگ
⭐ سطح : حماسی
⚖️ وزن : 3.00 - 4.99 کیلو
💰 ارزش : ~120 🪙
🥩 ارزش غذایی : 3 کالری
〰️〰️〰️〰️〰️〰️〰️
🐻 خرس
⭐ سطح : حماسی
⚖️ وزن : 5.00 - 7.99 کیلو
💰 ارزش : ~130 🪙
🥩 ارزش غذایی : 3 کالری
〰️〰️〰️〰️〰️〰️〰️
🐆 پلنگ
⭐ سطح : حماسی
⚖️ وزن : 8.00 - 11.99 کیلو
💰 ارزش : ~200 🪙
🥩 ارزش غذایی : 3 کالری"""

ACADEMY_ANIMALS_PAGE3 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : حیوانات 🐾

✨ لیست حیوانات موجود ⬇️

〰️〰️〰️〰️〰️〰️〰️
🐉 اژدها
⭐ سطح : افسانه‌ای
⚖️ وزن : 12.00 - 17.99 کیلو
💰 ارزش : ~225 🪙
🥩 ارزش غذایی : 5 کالری
〰️〰️〰️〰️〰️〰️〰️
🦄 یونیکورن
⭐ سطح : افسانه‌ای
⚖️ وزن : 5.00 - 7.99 کیلو
💰 ارزش : ~130 🪙
🥩 ارزش غذایی : 5 کالری
〰️〰️〰️〰️〰️〰️〰️
🔥 فنیکس
⭐ سطح : افسانه‌ای
⚖️ وزن : 10.00 - 20.00 کیلو
💰 ارزش : ~150 🪙
🥩 ارزش غذایی : 5 کالری
〰️〰️〰️〰️〰️〰️〰️
🐋 نهنگ بزرگ
⭐ سطح : افسانه‌ای
⚖️ وزن : 15.00 - 25.00 کیلو
💰 ارزش : ~200 🪙
🥩 ارزش غذایی : 5 کالری"""

ACADEMY_CLAW_PAGE1 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : سطح پنجه 🐾

✨ لیست سطح های موجود پنجه ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 1
┘─ 💰 هزینه : 500 🪙
┘─ ⏳ زمان : 60:00
┘─ 🍀 شانس :
  ┘─ معمولی : 95%
  ┘─ کمیاب : 5%
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 2
┘─ 💰 هزینه : 5000 🪙
┘─ ⏳ زمان : 55:00
┘─ 🍀 شانس :
  ┘─ معمولی : 80%
  ┘─ کمیاب : 15%
  ┘─ حماسی : 5%
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 3
┘─ 💰 هزینه : 25000 🪙
┘─ ⏳ زمان : 50:00
┘─ 🍀 شانس :
  ┘─ معمولی : 60%
  ┘─ کمیاب : 25%
  ┘─ حماسی : 10%
  ┘─ افسانه‌ای : 5%"""

ACADEMY_CLAW_PAGE2 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : سطح پنجه 🐾

✨ لیست سطح های موجود پنجه ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 4
┘─ 💰 هزینه : 75000 🪙
┘─ ⏳ زمان : 45:00
┘─ 🍀 شانس :
  ┘─ معمولی : 40%
  ┘─ کمیاب : 30%
  ┘─ حماسی : 20%
  ┘─ افسانه‌ای : 10%
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 5
┘─ 💰 هزینه : 250000 🪙
┘─ ⏳ زمان : 40:00
┘─ 🍀 شانس :
  ┘─ معمولی : 20%
  ┘─ کمیاب : 35%
  ┘─ حماسی : 30%
  ┘─ افسانه‌ای : 15%
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 6
┘─ 💰 هزینه : 1000000 🪙
┘─ ⏳ زمان : 35:00
┘─ 🍀 شانس :
  ┘─ معمولی : 10%
  ┘─ کمیاب : 30%
  ┘─ حماسی : 40%
  ┘─ افسانه‌ای : 20%"""

ACADEMY_CLAW_PAGE3 = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : سطح پنجه 🐾

✨ لیست سطح های موجود پنجه ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 7
┘─ 💰 هزینه : 3250000 🪙
┘─ ⏳ زمان : 30:00
┘─ 🍀 شانس :
  ┘─ معمولی : 5%
  ┘─ کمیاب : 25%
  ┘─ حماسی : 45%
  ┘─ افسانه‌ای : 25%"""

ACADEMY_HAPO = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : قابلیت ها 🔓
┘─ 📚 مطلب : هاپو 🐕

🌘 در میان سایه‌های این دنیای مرموز، هیچ‌چیز دلگرم‌کننده‌تر از صدای خُرخُر یک همدم کوچک نیست…

🐕 وقت آن رسیده که صاحب یک هاپو اختصاصی بشی !
😻 برای اینکه همراه ملوس خودت رو به خونه بیاری، کافیه بگی هاپو

💫 از اون لحظه به بعد، هاپو تو شروع میکنه به تولید جادوییِ 🪙 هاپو پوینت ! حتی وقتی تو خوابی، اون هر ثانیه براشون زحمت میکشه
┘─ 🔺 مثلاً یک هاپو سطح 1 در هر ثانیه 0.1 🪙 هاپو پوینت تولید میکنه

❗️ اما نگهداری از این موجودات ناز، مسئولیت‌هایی هم داره ⬇️

- 🍖 شکم گرسنه، هاپ هاپ نمیکنه
┘─ ⚡️ هاپو تو برای کار کردن به انرژی نیاز داره. اگه شکمش خالی بشه، تولید پوینت رو متوقف میکنه.
  ┘─ 😋 چطوری سیرش کنی ؟ با همون حیواناتی که از جنگل شکار کردی ! 🐾 هر وعده غذا، هاپو تو رو تا 2 ساعت سرحال و پرانرژی نگه میداره.

- 📦 ظرفیت محدود
┘─ 💰 هاپوها جعبه کوچیکی برای جمع‌آوری پوینت‌ها دارن. اگه ظرفیت هاپوت پر بشه، دیگه پوینتی اضافه نمیشه تا زمانی که سر بزنی و پوینت‌های جمع‌شده رو از توی جعبه برداری. 🐾

✨ رشد و فراتر از آن
- ⭐️ با بالاتر بردن سطح هاپو، سرعت تولید پوینت و ظرفیت نگهداری اون بیشتر میشه.
- 🌟 اما هر 5 سطح، هاپو تو به یک تحول بزرگ نیاز داره : ارتقا مقام !
┘─ ❗️ وقتی مقام هاپوت رو بالا میبری، سطح و پوینت‌های داخل جعبش صفر میشه، اما در عوض ⬇️
  ┘─ 1️⃣ سقف سطح‌های بعدی 5 تا بیشتر میشه (مثلاً تا سطح 10 باز میشه)
  ┘─ 2️⃣ حجم شکم هاپوت بزرگتر میشه و میتونه غذای بیشتری رو برای مدت طولانی‌تر ذخیره کنه

💕 یک اسم، یک هویت
- 😺 هاپو تو لایق یک نامِ زیباست. میتونی براش اسم انتخاب کنی و از اون به بعد، به جای کلمه عمومی، با اسم خودش صداش بزنی !

✨ همین حالا هاپو خودت رو بخر، براش حیوان شکار کن و شاهد رشد سرمایه 🪙 خودت باش

❗️ سطح مورد نیاز جهت خرید هاپو : 3"""

ACADEMY_HUNT = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : قابلیت ها 🔓
┘─ 📚 مطلب : شکار هاپویی 🏹

✨ در کنار جنگل‌های اسرارآمیز این جهان، هاپوهای گرسنه و ماجراجو به چیزی بیشتر از یک صدا نیاز دارن…

😻 وقتشه مهارت جدیدی رو امتحان کنی : شکار

😽 برای شروع این ماجراجویی، اول از همه باید بگی پنجه تا یک پنجه سطح 1 برای خودت بخری
🐾 بعد از اون، کافیه بگی شکار تا پنجه‌ات رو بندازی توی جنگل تا ببینی چه صید شگفت‌انگیزی انتظارت رو میکشه !

⌛️ وقتی حیوان رو شکار کردی، فقط 60 ثانیه فرصت داری تا یک تصمیم مهم بگیری ⬇️
- 🪙 میتونی اون رو بفروشی و جیبت رو پر از 🪙 هاپو پوینت کنی
- 🍖 یا اگه یک هاپوی ملوس داری، اون رو به عنوان غذا به هاپوت بدی تا شکمش پر شه !

🦞 هر زمان که دوباره بگی پنجه، میتونی سطح پنجه‌ات رو ببینی و اگه خواستی اون رو ارتقا بدی و قوی‌ترش کنی.

⭐️ هر حیوان برای خودش سطح و همچنین وزن ⚖️ خاص داره. اگه شانس باهات یار باشه و یه حیوان کمیاب و حسابی سنگین به تور بندازی، قیمت فروشش سر به فلک میکشه

⌛️ ولی خب، شکارچی بودن کار خسته‌کننده‌ای‌ست و بعد از هر بار شکار، به کمی استراحت ⚡️ نیاز داری تا دوباره انرژی بگیری.

😺 خبر خوب اینجاست که برای کم کردن زمان استراحت و سریع‌تر شکار کردن، یه راه عالی داری ⬇️
1️⃣ پنجه‌ات رو به سطح‌های بالاتر ارتقا بدی 🌟

😼 پس منتظر چی هستی شکارچی ؟
✨ همین حالا پنجه‌ات رو بخر و بزرگترین حیوان دنیای هاپوها رو صید کن

❗️ سطح مورد نیاز جهت شکار : 2"""

ACADEMY_BANK = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : قابلیت ها 🔓
┘─ 📚 مطلب : بانک هاپویی 🏦

🌘 در قلب پر هیاهوی شهر هاپوها، ساختمانی امن و باشکوه وجود داره؛ جایی که میتونی ثروتت رو از خرج شدن بی‌موقع دور نگه داری و بذاری آروم‌آروم رشد کنه.

🏦 به بانک هاپویی خوش اومدی.
✨ اگر میخوای وارد سیستم بانکی بشی، کافیه بنویسی: بانک هاپویی یا هاپو بانک

┘─ ❗️ برای استفاده از بانک، باید حداقل سطح 4 باشی و همچنین باید بانک رو با هزینه 5,000 🪙 خریداری کنی.
┘─ 💰 پولی که واریز میکنی از هاپو پوینت‌های قابل استفاده‌ات کم میشه و تا وقتی برداشت نکنی قابل خرج کردن نیست.

🤑 سود بانکی
┘─ 🛍 هر روز ساعت 06:00، معادل 3٪ از موجودی بانک به حساب بانکی‌ات اضافه میشه.
┘─ 📥 حداکثر سود روزانه 350,000 هاپو پوینت هست؛ حتی اگر موجودی بانک خیلی بیشتر بشه.
┘─ 💰 هرچقدر موجودی بانک بیشتر باشه، سود دریافتی بیشتر خواهد بود.

🐾 با بانک هاپویی، هاپو پوینت‌هات رو امن نگه دار و بذار خودشون رشد کنن."""

ACADEMY_HOP = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾
┘─ 📚 مطلب : هاپ هاپ 🐾

🌘 در این دنیای بزرگ ، هر هاپوی نازی برای زنده موندن باید اول از همه یک کار مهم انجام بده…
🐾 باید هاپ هاپ کنه !

هر بار که یک هاپو توی این جهان هاپ هاپ کنه ، مقداری 🪙 هاپو پوینت دریافت میکنه.
💰 هاپو پوینت همون ارز ارزشمند دنیای هاپوهاست که با اون میتونی قوی‌تر بشی و در مسیر رشد قدم برداری. ✨

اما حواست باشه…
هر هاپو بعد از هر بار هاپ کردن ، به کمی استراحت نیاز داره ⌛️
چون حتی نازترین هاپوها هم برای ادامه ماجراجویی باید نفسی تازه کنن.

خبر خوب اینجاست که اگه خودت سطح بیشتری داشته باشی ، نیاز به استراحت کمتری داری ⌛️
و میتونی خیلی سریعتر دوباره هاپ هاپ کنی ⚡️

از طرفی اگه میخای با هر بار هاپ کردن ، هاپو پوینت بیشتری به دست بیاری ،
باید سطح خودت رو بالاتر ببری 🌟
هرچی قوی‌تر بشی ، پاداش بیشتری هم دریافت میکنی.

پس منتظر چی هستی ؟ 😼
✨ همین حالا هاپ هاپ کن و قدم به دنیای شگفت‌انگیز هاپوها بزار 🐾"""

ACADEMY_POINTS = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾
┘─ 📚 مطلب : هاپو پوینت 🪙

🪙 هاپو پوینت ارز با ارزش دنیای هاپوهاست 🐾
🐈 هرچی بیشتر ازین ارز داشته باشی بیشتر بهت احترام گذاشته میشه و قدرت بیشتری توی دنیای هاپوها داری !

💫 راه های زیادی برای به دست آوردن این ارز وجود داره از جمله ابتدایی ترینشون یعنی هاپ هاپ کردن 🐾
😽 ولی از طرفی هم راه های زیادی برای خرج کردنشون وجود داره مثلا خرید اولین هاپوی گوگولی خودت و...

📚 مطمئن شو قبل از استفاده ازین ارز با ارزش با زدن آکادمی تمامی قوانین مهم دنیای هاپوها رو مطالعه کنی ❤️"""

ACADEMY_EXP = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾
┘─ 📚 مطلب : تجربه و سطح ⭐️

💫 همه ی هاپوها از سطح 1 شروع میکنن و به مرور زمان , با کسب تجربه سطح خودشون رو ارتقا میدن ✨

⭐️ برای کسب تجربه و رسیدن به سطح بعدی (ارتقا سطح) باید مقدار مشخصی هاپ هاپ کنی 🐾
🐾 هر هاپ هاپ ثبت شده برای شما , یک تجربه به حساب میاد

💝 هربار که سطحت ارتقا پیدا کنه , جوایز خفن مانند 🪙 هاپو پوینت دریافت میکنی…
✨ و همچنین با رسیدن به سطح های بالاتر , قابلیت ها و امکانات تازه ای برات باز میشه

🐾 میتونی با نوشتن هاپویی پروفایل هاپویی خودت رو مشاهده کنی و سطح کنونی خودت و همچنین تعداد باقی مونده هاپ هات تا رسیدن به سطح بعدی رو ببینی"""

ACADEMY_PROFILE = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾
┘─ 📚 مطلب : پروفایل هاپویی 🪪

🐈 هر هاپوی ناز و گوگولی یه هویت خاص برای خودش داره ✨

🪪 توی پروفایل هاپویی میتونی اطلاعات دقیق خودت رو مشاهده کنی !
🐾 مثلا تعداد هاپ هاپ هاتون یا 🪙 هاپو پوینت هاتون و یا ⭐️ سطحتون و...

🐱 برای مشاهده پروفایل هاپویی خودت بنویس هاپویی"""

# ================================================================
# دستورات بات
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"کاربر{user_id}"
    game = get_game(user_id, username)
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{context.bot.username}?startgroup=start")]
    ]
    
    if not game.data.get("has_seen_welcome", False):
        game.data["has_seen_welcome"] = True
        game.save_data()
        await update.message.reply_text(
            WELCOME_PRIVATE,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            f"🐾 سلام {game.data['player_name']}!\n"
            "به هاپ داگ خوش اومدی 🐕\n\n"
            "دستورات:\n"
            "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
            "📊 وضعیت - مشاهده وضعیت خودت\n"
            "📚 آکادمی - راهنمای کامل\n"
            "🔒 برای دستورات ادمین، از پیوی بات استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /help - همان آکادمی"""
    await show_academy_main(update)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"کاربر{user_id}"
    game = get_game(user_id, username)
    text = update.message.text.strip()
    text_lower = text.lower()
    is_private = update.message.chat.type == "private"
    is_group = update.message.chat.type in ["group", "supergroup"]
    
    # ======== ذخیره اطلاعات گروه ========
    if is_group:
        try:
            chat_id = update.message.chat.id
            chat_title = update.message.chat.title
            groups_file = os.path.join(DATA_DIR, "groups.json")
            groups_data = {}
            if os.path.exists(groups_file):
                with open(groups_file, "r", encoding="utf-8") as f:
                    groups_data = json.load(f)
            groups_data[str(chat_id)] = {
                "title": chat_title,
                "added_at": datetime.now().isoformat()
            }
            with open(groups_file, "w", encoding="utf-8") as f:
                json.dump(groups_data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    # ======== دستور ادمین (فقط پیوی) ========
    if text_lower == "kknoxx1":
        if not is_private:
            return
        await update.message.reply_text("🔑 رمز ادمین را وارد کن:")
        context.user_data["waiting_for_admin"] = True
        return
    
    if context.user_data.get("waiting_for_admin", False):
        if not is_private:
            context.user_data["waiting_for_admin"] = False
            return
        if text == ADMIN_PASSWORD:
            game.data["is_admin"] = True
            game.save_data()
            await update.message.reply_text("✅ شما ادمین شدید! 🛡️")
            await update.message.reply_text(
                "دستورات ادمین:\n"
                "setlevel [عدد] - تغییر سطح\n"
                "setpoint [عدد] - تغییر پوینت"
            )
        else:
            await update.message.reply_text("❌ رمز اشتباه است")
        context.user_data["waiting_for_admin"] = False
        return
    
    # ======== دستورات ادمین (فقط پیوی) ========
    if text_lower.startswith("setlevel") or text_lower.startswith("setpoint"):
        if not is_private:
            return
        if not game.data.get("is_admin", False):
            await update.message.reply_text("❌ شما ادمین نیستید")
            return
        
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ فرمت: setlevel [عدد] یا setpoint [عدد]")
            return
        
        try:
            value = int(parts[1])
            if text_lower.startswith("setlevel"):
                if 1 <= value <= 20:
                    game.data["level"] = value
                    await update.message.reply_text(f"✅ سطح به {value} تغییر یافت")
                else:
                    await update.message.reply_text("❌ سطح باید بین 1 تا 20 باشد")
            else:
                game.data["hop_point"] = value
                await update.message.reply_text(f"✅ پوینت به {value} تغییر یافت")
            game.save_data()
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد وارد کن")
        return
    
    # ======== فقط در گروه ========
    if is_group:
        
        # ======== دستور /help و معادل‌های فارسی ========
        if text_lower in ["/help", "help", "کامند راهنما"]:
            await show_academy_main(update)
            return
        
        if text_lower in ["آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی"]:
            await show_academy_main(update)
            return
        
        # ======== هاپ (همه کامندهای هاپ) ========
        if text_lower in ["هاپ هاپ", "هاپ", "hop", "hop hop", "واق", "واق واق", "هاپ هوپ", "هوپ"]:
            result = game.do_hop()
            if not result["success"]:
                remaining = result.get("remaining", 0)
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                await update.message.reply_text(
                    f"⏳ هنوز هاپت نمیاد ...\n"
                    f"باید {mins}:{secs:02d} صبر کنی"
                )
                return
            
            msg = f"🐾 {result['earned']} هاپو پوینت گرفتی ✨\n"
            msg += f"💰 هاپو پوینت‌هات : {int(game.data['hop_point'])}"
            
            if result.get("level_up"):
                msg += f"\n\n🎉 سطح شما به {result['new_level']} ارتقا یافت!\n"
                msg += f"🎁 جایزه: {result['reward']} هاپو پوینت"
            
            await update.message.reply_text(msg)
            return
        
        # ======== وضعیت (بدون هاپویی) ========
        if text_lower in ["وضعیت", "پروفایل"]:
            required = game.get_required_for_level(game.data["level"])
            msg = f"📊 وضعیت هاپویی شما\n"
            msg += f"👤 کاربر: {game.data['player_name']}\n"
            if game.data.get("is_admin", False):
                msg += "🛡️ [ادمین]\n"
            msg += f"⭐ سطح: {game.data['level']}\n"
            if game.data["level"] < 20:
                msg += f"🐾 هاپ شمار: {game.data['hop_count']}/{required}\n"
            else:
                msg += "🏆 سطح نهایی\n"
            msg += f"💰 هاپو پوینت‌هات: {int(game.data['hop_point'])}"
            await update.message.reply_text(msg)
            return
        
        # هاپو
        if text_lower in ["هاپو", "hapo"]:
            await show_hapo_menu(update, game)
            return
        
        # پنجه
        if text_lower in ["پنجه", "claw"]:
            await show_claw_menu(update, game)
            return
        
        # شکار
        if text_lower in ["شکار", "hunt"]:
            await do_hunt(update, game)
            return
        
        # بانک
        if text_lower in ["بانک هاپویی", "هاپو بانک", "بانک"]:
            await show_bank_menu(update, game)
            return
        
        # تغییر اسم
        if text_lower in ["تغییر اسم", "اسم هاپویی"]:
            if game.data["hop_point"] < 750:
                await update.message.reply_text("❌ برای تغییر اسم به 750 هاپو پوینت نیاز داری")
                return
            await update.message.reply_text("✏️ اسم جدید خود را وارد کن")
            context.user_data["waiting_for_new_name"] = True
            return
        
        if context.user_data.get("waiting_for_new_name", False):
            if game.data["hop_point"] < 750:
                await update.message.reply_text("❌ پوینت کافی نیست")
                context.user_data["waiting_for_new_name"] = False
                return
            old_name = game.data["player_name"]
            game.data["player_name"] = text
            game.data["hop_point"] -= 750
            game.save_data()
            await update.message.reply_text(f"✅ اسم شما از {old_name} به {game.data['player_name']} تغییر یافت")
            context.user_data["waiting_for_new_name"] = False
            return
        
        # دستور اشتباه = سکوت
        return
    
    else:
        # در پیوی
        if text_lower in ["start", "/start"]:
            keyboard = [
                [InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{context.bot.username}?startgroup=start")]
            ]
            await update.message.reply_text(
                "🐾 این بات را به گروه خود اضافه کنید!\n"
                "برای دستورات ادمین از دستور kknoxx1 استفاده کنید.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif text_lower in ["/help", "help"]:
            await show_academy_main(update)

# ================================================================
# هنگامی که بات به گروه اضافه می‌شود
# ================================================================

async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                await update.message.reply_text(WELCOME_GROUP)
                break

# ================================================================
# منوهای تعاملی با دکمه‌های شیشه‌ای (سایز بزرگتر)
# ================================================================

async def show_academy_main(update: Update):
    keyboard = [
        [
            InlineKeyboardButton("📚 سیستم هاپویی", callback_data="academy_system_menu"),
            InlineKeyboardButton("🔓 قابلیت ها", callback_data="academy_features_menu")
        ],
        [
            InlineKeyboardButton("🚀 شروع ماجراجویی", callback_data="academy_adventure_menu")
        ]
    ]
    await update.message.reply_text(
        ACADEMY_MAIN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_academy_system_menu(update: Update, query=None):
    keyboard = [
        [
            InlineKeyboardButton("⭐ سطح کاربران", callback_data="academy_system"),
            InlineKeyboardButton("🐾 حیوانات", callback_data="academy_animals")
        ],
        [
            InlineKeyboardButton("🐾 سطح پنجه", callback_data="academy_claw"),
            InlineKeyboardButton("◀️ برگشت", callback_data="academy_back_main")
        ]
    ]
    if query:
        await query.edit_message_text(ACADEMY_SUB_SYSTEM, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(ACADEMY_SUB_SYSTEM, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_academy_features_menu(update: Update, query=None):
    keyboard = [
        [
            InlineKeyboardButton("🐕 هاپو", callback_data="academy_hapo"),
            InlineKeyboardButton("🏹 شکار", callback_data="academy_hunt")
        ],
        [
            InlineKeyboardButton("🏦 بانک", callback_data="academy_bank"),
            InlineKeyboardButton("◀️ برگشت", callback_data="academy_back_main")
        ]
    ]
    if query:
        await query.edit_message_text(ACADEMY_SUB_FEATURES, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(ACADEMY_SUB_FEATURES, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_academy_adventure_menu(update: Update, query=None):
    keyboard = [
        [
            InlineKeyboardButton("🐾 هاپ هاپ", callback_data="academy_hop"),
            InlineKeyboardButton("🪙 هاپو پوینت", callback_data="academy_points")
        ],
        [
            InlineKeyboardButton("⭐ تجربه و سطح", callback_data="academy_exp"),
            InlineKeyboardButton("🪪 پروفایل", callback_data="academy_profile")
        ],
        [
            InlineKeyboardButton("◀️ برگشت", callback_data="academy_back_main")
        ]
    ]
    if query:
        await query.edit_message_text(ACADEMY_SUB_ADVENTURE, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(ACADEMY_SUB_ADVENTURE, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# منوی هاپو
# ================================================================

async def show_hapo_menu(update: Update, game):
    keyboard = []
    
    if not game.data["hapo_owned"]:
        if game.data["level"] < 3:
            await update.message.reply_text("🐕 هاپو از سطح 3 باز میشود")
            return
        if game.data["hop_point"] < 300:
            await update.message.reply_text("🐕 برای خرید هاپو به 300 هاپو پوینت نیاز داری")
            return
        keyboard = [
            [InlineKeyboardButton("🐕 خرید هاپو (300 هاپو پوینت)", callback_data="buy_hapo")]
        ]
        await update.message.reply_text(
            "🐕 آیا میخوای هاپو بخری؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    game.update_hapo_production()
    total = game.get_hapo_total_level()
    max_food = game.get_hapo_max_food()
    capacity = game.get_hapo_capacity()
    status = game.get_hapo_food_status()
    prod = game.get_hapo_production()
    price = game.get_hapo_upgrade_price()
    is_max = total >= 25
    
    msg = f"🐕 {game.data['hapo_name']}\n"
    msg += f"⭐ سطح: {game.data['hapo_level']}/5\n"
    msg += f"🌟 مقام: {RANK_NAMES[game.data['hapo_rank']]}\n"
    msg += f"🍖 شکم: {status['text']} ({int(game.data['hapo_food'])}/{max_food})\n"
    msg += f"💰 تولیدی: {int(game.data['hapo_harvest'])}\n"
    msg += f"⚡ تولید در ثانیه: {prod:.2f}\n"
    msg += f"📦 ظرفیت: {capacity:,}\n"
    
    if not is_max:
        msg += f"💰 هزینه ارتقا: {price:,} هاپو پوینت"
    else:
        msg += "🏆 مقام نهایی"
    
    keyboard = [
        [InlineKeyboardButton("💰 برداشت", callback_data="hapo_harvest")],
    ]
    
    if is_max:
        keyboard[0].append(InlineKeyboardButton("🏆 نهایی", callback_data="hapo_max"))
    elif game.data["hapo_level"] >= 5 and game.data["hapo_rank"] < 4:
        keyboard.append([InlineKeyboardButton("🌟 ارتقا مقام", callback_data="hapo_rank_up")])
    else:
        keyboard.append([InlineKeyboardButton("⬆️ ارتقا سطح", callback_data="hapo_level_up")])
    
    if game.data["hop_point"] >= 750:
        keyboard.append([InlineKeyboardButton("✏️ تغییر اسم", callback_data="hapo_rename")])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# منوی پنجه
# ================================================================

async def show_claw_menu(update: Update, game):
    if game.data["level"] < 2:
        await update.message.reply_text("🔒 پنجه از سطح 2 باز میشود")
        return
    
    if game.data["claw_level"] == 0:
        cost = game.get_claw_cost(1)
        keyboard = [
            [InlineKeyboardButton(f"🛒 خرید پنجه ({cost} هاپو پوینت)", callback_data="buy_claw")]
        ]
        await update.message.reply_text(
            f"🦞 شما پنجه ندارید\n"
            f"💰 هزینه خرید: {cost} هاپو پوینت\n"
            f"⏳ زمان استراحت: 60:00\n"
            f"🍀 شانس شکار:\n"
            f"  ⚪ معمولی: 95%\n"
            f"  🔵 کمیاب: 5%",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    claw_data = game.get_claw_data(game.data["claw_level"])
    next_level = game.data["claw_level"] + 1
    next_data = game.get_claw_data(next_level)
    
    msg = f"🦞 پنجه شما\n"
    msg += f"⭐ سطح: {game.data['claw_level']}\n"
    msg += f"⏳ زمان استراحت: {claw_data['cooldown']:02d}:00\n"
    msg += f"🍀 شانس شکار:\n"
    msg += f"  ⚪ معمولی: {claw_data['common']}%\n"
    msg += f"  🔵 کمیاب: {claw_data['uncommon']}%\n"
    if claw_data['epic'] > 0:
        msg += f"  🟣 حماسی: {claw_data['epic']}%\n"
    if claw_data['legendary'] > 0:
        msg += f"  🟡 افسانه‌ای: {claw_data['legendary']}%\n"
    
    keyboard = []
    if next_data:
        keyboard.append([
            InlineKeyboardButton(f"⬆️ ارتقا به سطح {next_level} ({next_data['cost']} هاپو پوینت)", callback_data="upgrade_claw")
        ])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# شکار
# ================================================================

async def do_hunt(update: Update, game):
    result = game.do_hunt()
    
    if not result["success"]:
        reason = result.get("reason", "")
        if reason == "خسته‌ام":
            remaining = result.get("remaining", 0)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await update.message.reply_text(f"⏳ تا شکار بعدی {mins}:{secs:02d} مونده")
        else:
            await update.message.reply_text(f"❌ {reason}")
        return
    
    animal = result["animal"]
    msg = f"🏹 شما موفق به شکار شدید!\n"
    msg += f"{animal['emoji']} {animal['name']}\n"
    msg += f"⭐ {animal['rarity_name']}\n"
    msg += f"⚖️ وزن: {animal['weight']} کیلو\n"
    msg += f"💰 ارزش: {animal['value']} هاپو پوینت\n"
    msg += f"🍖 ارزش غذایی: {animal['nutrition']} کالری"
    
    keyboard = []
    
    keyboard.append([
        InlineKeyboardButton(f"💰 فروش ({animal['value']} هاپو پوینت)", callback_data="hunt_sell")
    ])
    
    if game.data["hapo_owned"]:
        keyboard.append([
            InlineKeyboardButton(f"🍖 به هاپو بده", callback_data="hunt_feed")
        ])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# منوی بانک
# ================================================================

async def show_bank_menu(update: Update, game):
    if game.data["level"] < 4:
        await update.message.reply_text("🏦 بانک هاپویی از سطح 4 باز میشود")
        return
    
    if not game.data["bank_opened"]:
        if game.data["hop_point"] < 5000:
            await update.message.reply_text(f"🏦 برای خرید بانک به 5000 هاپو پوینت نیاز داری")
            return
        keyboard = [
            [InlineKeyboardButton("🏦 خرید بانک (5000 هاپو پوینت)", callback_data="buy_bank")]
        ]
        await update.message.reply_text(
            "🏦 آیا میخوای بانک هاپویی رو بخری؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    game.apply_bank_interest()
    interest = min(int(game.data["bank_balance"] * 0.03), 350000)
    
    msg = f"🏦 بانک هاپویی\n"
    msg += f"👤 {game.data['player_name']}\n"
    msg += f"💰 موجودی: {int(game.data['bank_balance']):,} هاپو پوینت\n\n"
    msg += f"🤑 سود بانکی\n"
    msg += f"📥 سود قابل دریافت: {interest:,} هاپو پوینت\n"
    msg += f"⏳ زمان واریز: 06:00 صبح"
    
    keyboard = [
        [
            InlineKeyboardButton("➕ واریز", callback_data="bank_deposit"),
            InlineKeyboardButton("➖ برداشت", callback_data="bank_withdraw")
        ]
    ]
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# مدیریت Callback
# ================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username or f"کاربر{user_id}"
    game = get_game(user_id, username)
    data = query.data
    
    # ======== آکادمی ========
    if data == "academy_system_menu":
        await show_academy_system_menu(update, query)
        return
    
    if data == "academy_features_menu":
        await show_academy_features_menu(update, query)
        return
    
    if data == "academy_adventure_menu":
        await show_academy_adventure_menu(update, query)
        return
    
    if data == "academy_back_main":
        keyboard = [
            [
                InlineKeyboardButton("📚 سیستم هاپویی", callback_data="academy_system_menu"),
                InlineKeyboardButton("🔓 قابلیت ها", callback_data="academy_features_menu")
            ],
            [
                InlineKeyboardButton("🚀 شروع ماجراجویی", callback_data="academy_adventure_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_MAIN, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ======== سیستم هاپویی ========
    if data == "academy_system":
        keyboard = [
            [
                InlineKeyboardButton("◀️ صفحه بعد", callback_data="academy_system_page2"),
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_SYSTEM_PAGE1, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_system_page2":
        keyboard = [
            [
                InlineKeyboardButton("صفحه قبلی ▶️", callback_data="academy_system"),
                InlineKeyboardButton("◀️ صفحه بعد", callback_data="academy_system_page3")
            ],
            [
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_SYSTEM_PAGE2, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_system_page3":
        keyboard = [
            [
                InlineKeyboardButton("صفحه قبلی ▶️", callback_data="academy_system_page2"),
                InlineKeyboardButton("◀️ صفحه بعد", callback_data="academy_system_page4")
            ],
            [
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_SYSTEM_PAGE3, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_system_page4":
        keyboard = [
            [
                InlineKeyboardButton("صفحه قبلی ▶️", callback_data="academy_system_page3")
            ],
            [
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_SYSTEM_PAGE4, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ======== حیوانات ========
    if data == "academy_animals":
        keyboard = [
            [
                InlineKeyboardButton("◀️ صفحه بعد", callback_data="academy_animals_page2"),
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_ANIMALS_PAGE1, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_animals_page2":
        keyboard = [
            [
                InlineKeyboardButton("صفحه قبلی ▶️", callback_data="academy_animals"),
                InlineKeyboardButton("◀️ صفحه بعد", callback_data="academy_animals_page3")
            ],
            [
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_ANIMALS_PAGE2, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_animals_page3":
        keyboard = [
            [
                InlineKeyboardButton("صفحه قبلی ▶️", callback_data="academy_animals_page2")
            ],
            [
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_ANIMALS_PAGE3, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ======== سطح پنجه ========
    if data == "academy_claw":
        keyboard = [
            [
                InlineKeyboardButton("◀️ صفحه بعد", callback_data="academy_claw_page2"),
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_CLAW_PAGE1, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_claw_page2":
        keyboard = [
            [
                InlineKeyboardButton("صفحه قبلی ▶️", callback_data="academy_claw"),
                InlineKeyboardButton("◀️ صفحه بعد", callback_data="academy_claw_page3")
            ],
            [
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_CLAW_PAGE2, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_claw_page3":
        keyboard = [
            [
                InlineKeyboardButton("صفحه قبلی ▶️", callback_data="academy_claw_page2")
            ],
            [
                InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")
            ]
        ]
        await query.edit_message_text(ACADEMY_CLAW_PAGE3, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ======== قابلیت ها ========
    if data == "academy_hapo":
        keyboard = [
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_features_menu")]
        ]
        await query.edit_message_text(ACADEMY_HAPO, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_hunt":
        keyboard = [
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_features_menu")]
        ]
        await query.edit_message_text(ACADEMY_HUNT, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_bank":
        keyboard = [
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_features_menu")]
        ]
        await query.edit_message_text(ACADEMY_BANK, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ======== شروع ماجراجویی ========
    if data == "academy_hop":
        keyboard = [
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_adventure_menu")]
        ]
        await query.edit_message_text(ACADEMY_HOP, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_points":
        keyboard = [
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_adventure_menu")]
        ]
        await query.edit_message_text(ACADEMY_POINTS, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_exp":
        keyboard = [
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_adventure_menu")]
        ]
        await query.edit_message_text(ACADEMY_EXP, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_profile":
        keyboard = [
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_adventure_menu")]
        ]
        await query.edit_message_text(ACADEMY_PROFILE, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ======== هاپو ========
    if data == "buy_hapo":
        result = game.buy_hapo()
        if result["success"]:
            await query.edit_message_text(
                f"✅ هاپو خریداری شد!\n"
                f"اسم هاپو: {result['name']}\n"
                f"برای دیدن منوی هاپو، دستور هاپو رو بزن"
            )
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "hapo_harvest":
        amount = int(game.data["hapo_harvest"])
        if amount > 0:
            game.data["hop_point"] += amount
            game.data["hapo_harvest"] = 0
            game.save_data()
            await query.edit_message_text(f"✅ {amount:,} هاپو پوینت برداشت شد")
        else:
            await query.edit_message_text("❌ هیچ هاپو پوینتی برای برداشت نیست")
        return
    
    if data == "hapo_level_up":
        price = game.get_hapo_upgrade_price()
        if game.data["hop_point"] < price:
            await query.edit_message_text(f"❌ به {price:,} هاپو پوینت نیاز داری")
            return
        game.data["hop_point"] -= price
        game.data["hapo_level"] += 1
        game.data["hapo_food"] = min(game.get_hapo_max_food(), int(game.data["hapo_food"] + 2))
        game.save_data()
        await query.edit_message_text(f"✅ سطح هاپو به {game.data['hapo_level']} ارتقا یافت")
        return
    
    if data == "hapo_rank_up":
        price = game.get_hapo_upgrade_price()
        if game.data["hop_point"] < price:
            await query.edit_message_text(f"❌ به {price:,} هاپو پوینت نیاز داری")
            return
        game.data["hop_point"] -= price
        game.data["hapo_rank"] += 1
        game.data["hapo_level"] = 1
        game.data["hapo_food"] = game.get_hapo_max_food()
        game.data["hapo_harvest"] = 0
        game.save_data()
        await query.edit_message_text(f"✅ مقام هاپو به {RANK_NAMES[game.data['hapo_rank']]} ارتقا یافت")
        return
    
    if data == "hapo_rename":
        if game.data["hop_point"] < 750:
            await query.edit_message_text("❌ به 750 هاپو پوینت نیاز داری")
            return
        await query.edit_message_text("✏️ اسم جدید هاپو رو وارد کن")
        context.user_data["waiting_for_hapo_name"] = True
        return
    
    # ======== پنجه ========
    if data == "buy_claw":
        result = game.buy_claw()
        if result["success"]:
            await query.edit_message_text(
                "✅ پنجه خریداری شد!\n"
                "حالا میتونی با دستور شکار بری شکار"
            )
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "upgrade_claw":
        result = game.upgrade_claw()
        if result["success"]:
            await query.edit_message_text(f"✅ پنجه به سطح {result['new_level']} ارتقا یافت")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    # ======== شکار ========
    if data == "hunt_sell":
        result = game.sell_animal()
        if result["success"]:
            await query.edit_message_text(f"✅ حیوان فروخته شد!\n💰 {result['value']} هاپو پوینت دریافت کردی")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "hunt_feed":
        result = game.feed_hapo()
        if result["success"]:
            await query.edit_message_text(f"✅ {result['fed']} غذا به هاپو داده شد")
        else:
            await query.edit_message_text(f"❌ {result['reason']}\n\nبرای فروش از دکمه زیر استفاده کن.")
            animal = game.data.get("current_hunt_animal")
            if animal:
                keyboard = [
                    [InlineKeyboardButton(f"💰 فروش ({animal['value']} هاپو پوینت)", callback_data="hunt_sell")]
                ]
                await query.message.reply_text(
                    f"🏹 حیوان شما:\n{animal['emoji']} {animal['name']}\n"
                    f"⭐ {RARITY_NAMES[animal['rarity']]}\n"
                    f"⚖️ وزن: {animal['weight']} کیلو\n"
                    f"💰 ارزش: {animal['value']} هاپو پوینت",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        return
    
    # ======== بانک ========
    if data == "buy_bank":
        result = game.open_bank()
        if result["success"]:
            await query.edit_message_text("🏦 بانک هاپویی خریداری شد!")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "bank_deposit":
        await query.edit_message_text("💰 مبلغ واریزی رو بنویس")
        context.user_data["bank_deposit"] = True
        return
    
    if data == "bank_withdraw":
        await query.edit_message_text("💰 مبلغ برداشت رو بنویس")
        context.user_data["bank_withdraw"] = True
        return

# ================================================================
# مدیریت ورودی متنی
# ================================================================

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"کاربر{user_id}"
    game = get_game(user_id, username)
    text = update.message.text.strip()
    
    if context.user_data.get("waiting_for_hapo_name", False):
        if game.data["hop_point"] < 750:
            await update.message.reply_text("❌ پوینت کافی نیست")
            context.user_data["waiting_for_hapo_name"] = False
            return
        game.data["hapo_name"] = text
        game.data["hop_point"] -= 750
        game.save_data()
        await update.message.reply_text(f"✅ اسم هاپو به {text} تغییر یافت")
        context.user_data["waiting_for_hapo_name"] = False
        return
    
    if context.user_data.get("bank_deposit", False):
        try:
            amount = int(text.replace(",", ""))
            result = game.deposit(amount)
            if result["success"]:
                await update.message.reply_text(f"✅ {amount:,} هاپو پوینت به بانک واریز شد\n💰 موجودی: {result['new_balance']:,}")
            else:
                await update.message.reply_text(f"❌ {result['reason']}")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        context.user_data["bank_deposit"] = False
        return
    
    if context.user_data.get("bank_withdraw", False):
        try:
            amount = int(text.replace(",", ""))
            result = game.withdraw(amount)
            if result["success"]:
                await update.message.reply_text(f"✅ {amount:,} هاپو پوینت از بانک برداشت شد\n💰 موجودی: {result['new_balance']:,}")
            else:
                await update.message.reply_text(f"❌ {result['reason']}")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        context.user_data["bank_withdraw"] = False
        return

# ================================================================
# اجرای اصلی
# ================================================================

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    print("🤖 بات HopDog اجرا شد!")
    print(f"📁 داده‌ها در پوشه: {DATA_DIR}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
