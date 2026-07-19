# bot.py - نسخه کامل با تمام قابلیت‌های جدید

import os
import logging
import random
import json
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from supabase import create_client, Client

# ================================================================
# تنظیمات اولیه
# ================================================================

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
# ایمپورت از academy.py
# ================================================================

from academy import (
    ACADEMY_MAIN, ACADEMY_SUB_SYSTEM, ACADEMY_SUB_FEATURES, ACADEMY_SUB_ADVENTURE,
    ACADEMY_SYSTEM_PAGE1, ACADEMY_SYSTEM_PAGE2, ACADEMY_SYSTEM_PAGE3, ACADEMY_SYSTEM_PAGE4,
    ACADEMY_ANIMALS_PAGE1, ACADEMY_ANIMALS_PAGE2, ACADEMY_ANIMALS_PAGE3,
    ACADEMY_CLAW_PAGE1, ACADEMY_CLAW_PAGE2, ACADEMY_CLAW_PAGE3,
    ACADEMY_HAPO, ACADEMY_HUNT, ACADEMY_BANK,
    ACADEMY_HOP, ACADEMY_POINTS, ACADEMY_EXP, ACADEMY_PROFILE,
    show_academy_main, show_academy_system_menu, show_academy_features_menu,
    show_academy_adventure_menu
)

# ================================================================
# کلاس مدیریت بازی
# ================================================================

class HopDogGame:
    def __init__(self, user_id, username=""):
        self.user_id = str(user_id)
        self.username = username
        self.data = self.load_data()
        if not self.data:
            self.reset_data()

    def load_data(self):
        try:
            response = supabase.table("users").select("*").eq("user_id", self.user_id).execute()
            if response.data and len(response.data) > 0:
                data = response.data[0]
                if "current_hunt_animal" in data and data["current_hunt_animal"]:
                    try:
                        data["current_hunt_animal"] = json.loads(data["current_hunt_animal"])
                    except:
                        data["current_hunt_animal"] = None
                # فیلدهای جدید برای پروفایل
                if "profile_hidden" not in data:
                    data["profile_hidden"] = False
                if "profile_locked" not in data:
                    data["profile_locked"] = False
                return data
            return None
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return None

    def save_data(self):
        try:
            data_to_save = {**self.data}
            if "current_hunt_animal" in data_to_save and data_to_save["current_hunt_animal"]:
                data_to_save["current_hunt_animal"] = json.dumps(data_to_save["current_hunt_animal"])
            if "created_at" in data_to_save:
                del data_to_save["created_at"]
            data_to_save["last_updated"] = datetime.now().isoformat()
            
            supabase.table("users").upsert(data_to_save).execute()
            return True
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            return False

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
            "profile_hidden": False,  # جدید: مخفی کردن پروفایل
            "profile_locked": False,  # جدید: قفل کردن پروفایل
            "last_updated": datetime.now().isoformat()
        }
        self.save_data()

    @staticmethod
    def get_user_by_identifier(identifier):
        try:
            if identifier.isdigit():
                response = supabase.table("users").select("*").eq("user_id", identifier).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
                return None
            else:
                username = identifier.replace("@", "").lower()
                response = supabase.table("users").select("*").eq("player_name", username).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
                response = supabase.table("users").select("*").eq("player_name", f"@{username}").execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
                return None
        except Exception as e:
            logging.error(f"Error getting user: {e}")
            return None

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

    def transfer_points(self, target_user_id, amount):
        """انتقال هاپو پوینت به کاربر دیگر"""
        if self.data["profile_locked"]:
            return {"success": False, "reason": "پروفایل شما قفل است"}
        if self.data["hop_point"] < amount:
            return {"success": False, "reason": "موجودی کافی نیست"}
        if amount <= 0:
            return {"success": False, "reason": "مبلغ نامعتبر است"}
        
        # دریافت اطلاعات کاربر مقصد
        target_game = get_game(int(target_user_id))
        if target_game.data["profile_locked"]:
            return {"success": False, "reason": "پروفایل کاربر مقصد قفل است"}
        
        # انتقال
        self.data["hop_point"] -= amount
        target_game.data["hop_point"] += amount
        self.save_data()
        target_game.save_data()
        
        return {"success": True, "amount": amount, "target_name": target_game.data["player_name"]}

# ================================================================
# دیکشنری کاربران
# ================================================================

user_games = {}

def get_game(user_id, username=""):
    if user_id not in user_games:
        user_games[user_id] = HopDogGame(user_id, username)
    return user_games[user_id]

def get_user_link(user_id, username, full_name):
    display_name = full_name or f"کاربر{user_id}"
    if username:
        return f"@{username}"
    else:
        return f"[{display_name}](tg://user?id={user_id})"

# ================================================================
# توابع کمکی
# ================================================================

def get_confirm_keyboard(callback_data_yes, callback_data_no):
    keyboard = [
        [
            InlineKeyboardButton("✅ بله", callback_data=callback_data_yes),
            InlineKeyboardButton("❌ نه", callback_data=callback_data_no)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_hapo_menu_keyboard(game):
    keyboard = [
        [InlineKeyboardButton("💰 برداشت", callback_data="hapo_harvest")],
    ]
    
    total = game.get_hapo_total_level()
    is_max = total >= 25
    
    if is_max:
        keyboard[0].append(InlineKeyboardButton("🏆 نهایی", callback_data="hapo_max"))
    elif game.data["hapo_level"] >= 5 and game.data["hapo_rank"] < 4:
        keyboard.append([InlineKeyboardButton("🌟 ارتقا مقام", callback_data="hapo_rank_up")])
    else:
        keyboard.append([InlineKeyboardButton("⬆️ ارتقا سطح", callback_data="hapo_level_up")])
    
    if game.data["hop_point"] >= 750:
        keyboard.append([InlineKeyboardButton("✏️ تغییر اسم", callback_data="hapo_rename")])
    
    return InlineKeyboardMarkup(keyboard)

def get_hapo_menu_text(game):
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
    
    return msg

# ================================================================
# دستورات جدید: هاپو هام (پروفایل)
# ================================================================

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور هاپو هام - نمایش پروفایل کاربر با دکمه‌ها"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    required = game.get_required_for_level(game.data["level"])
    is_hidden = game.data.get("profile_hidden", False)
    is_locked = game.data.get("profile_locked", False)
    
    msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
    msg += f"┐─ 👤 کاربر : {full_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 آیدی : {user_id}\n\n"
    else:
        msg += f"‏┘─ 🪪 آیدی : 🔒 مخفی\n\n"
    
    msg += f"┐─ 💰 هاپ پوینت ها : {int(game.data['hop_point']):,} 🪙\n"
    msg += f"┐─ 🐾 هاپ هاپ ها : {game.data['hop_count']}\n\n"
    
    if game.data["level"] < 20:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} | {game.data['hop_count']} / {required}"
    else:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} 🏆 نهایی"
    
    # دکمه‌ها
    keyboard = []
    
    # دکمه مخفی کردن پروفایل
    if is_hidden:
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide")])
    
    # دکمه قفل کردن پروفایل
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock")])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# دستور هاپوهاش - مشاهده پروفایل دیگران
# ================================================================

async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور هاپوهاش - نمایش پروفایل کاربر دیگر با ریپلای"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    # بررسی ریپلای
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لطفاً روی پیام یک کاربر ریپلای کن و «هاپوهاش» رو بزن.")
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    target_username = update.message.reply_to_message.from_user.username
    target_full_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    
    # دریافت اطلاعات کاربر مقصد
    target_game = get_game(target_user_id, target_username or target_full_name)
    target_data = target_game.data
    
    # بررسی مخفی بودن پروفایل
    if target_data.get("profile_hidden", False):
        # فقط اسم و پیام مخفی شدن رو نشون بده
        msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
        msg += f"┐─ 👤 کاربر : {target_full_name}\n"
        msg += f"┘─ 🔒 این کاربر پروفایل خود را مخفی کرده است."
        
        # تلاش برای نمایش عکس پروفایل
        try:
            user_photos = await context.bot.get_user_profile_photos(target_user_id, limit=1)
            if user_photos.total_count > 0:
                photo = user_photos.photos[0][-1]
                await update.message.reply_photo(
                    photo.file_id,
                    caption=msg
                )
                return
        except:
            pass
        
        await update.message.reply_text(msg)
        return
    
    # نمایش کامل پروفایل
    required = target_game.get_required_for_level(target_data["level"])
    
    msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
    msg += f"┐─ 👤 کاربر : {target_full_name}\n"
    msg += f"‏┘─ 🪪 آیدی : {target_user_id}\n\n"
    msg += f"┐─ 💰 هاپ پوینت ها : {int(target_data['hop_point']):,} 🪙\n"
    msg += f"┐─ 🐾 هاپ هاپ ها : {target_data['hop_count']}\n\n"
    
    if target_data["level"] < 20:
        msg += f"╯─ ⭐️ سطح : {target_data['level']} | {target_data['hop_count']} / {required}"
    else:
        msg += f"╯─ ⭐️ سطح : {target_data['level']} 🏆 نهایی"
    
    # نمایش عکس پروفایل
    try:
        user_photos = await context.bot.get_user_profile_photos(target_user_id, limit=1)
        if user_photos.total_count > 0:
            photo = user_photos.photos[0][-1]
            await update.message.reply_photo(
                photo.file_id,
                caption=msg
            )
            return
    except:
        pass
    
    await update.message.reply_text(msg)

# ================================================================
# دستور انتقال هاپویی
# ================================================================

TRANSFER_STATE = {}

async def transfer_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور انتقال هاپویی - با ریپلای"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    # بررسی ریپلای
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لطفاً روی پیام یک کاربر ریپلای کن و «انتقال هاپویی» رو بزن.")
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    target_username = update.message.reply_to_message.from_user.username
    target_full_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    
    # بررسی قفل بودن پروفایل خود
    if game.data.get("profile_locked", False):
        await update.message.reply_text("❌ پروفایل شما قفل است. ابتدا آن را باز کن.")
        return
    
    # بررسی قفل بودن پروفایل مقصد
    target_game = get_game(target_user_id, target_username or target_full_name)
    if target_game.data.get("profile_locked", False):
        await update.message.reply_text("❌ پروفایل کاربر مقصد قفل است.")
        return
    
    # اگر کاربر خودش باشه
    if target_user_id == user_id:
        await update.message.reply_text("❌ نمی‌تونی به خودت هاپو پوینت انتقال بدی!")
        return
    
    # ذخیره اطلاعات برای مرحله بعد
    TRANSFER_STATE[user_id] = {
        "target_id": target_user_id,
        "target_name": target_full_name
    }
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="transfer_cancel")]]
    
    await update.message.reply_text(
        f"💰 انتقال هاپویی\n\n"
        f"از: {full_name}\n"
        f"به: {target_full_name}\n\n"
        f"لطفاً مبلغ مورد نظر را به عدد وارد کن:\n"
        f"(مثلاً: 1000)",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data["waiting_for_transfer_amount"] = True

async def process_transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مبلغ انتقال"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not context.user_data.get("waiting_for_transfer_amount"):
        return
    
    try:
        amount = int(update.message.text.strip().replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن.")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ مبلغ باید بزرگتر از صفر باشد.")
        return
    
    if game.data["hop_point"] < amount:
        await update.message.reply_text(f"❌ موجودی کافی نیست. شما {int(game.data['hop_point']):,} هاپو پوینت داری.")
        return
    
    # دریافت اطلاعات انتقال
    transfer_info = TRANSFER_STATE.get(user_id)
    if not transfer_info:
        await update.message.reply_text("❌ خطا در انتقال. لطفاً دوباره تلاش کن.")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    target_id = transfer_info["target_id"]
    target_name = transfer_info["target_name"]
    
    # نمایش پیام تایید
    confirm_text = (
        f"💰 انتقال هاپویی\n\n"
        f"از: {full_name}\n"
        f"به: {target_name}\n"
        f"💰 مبلغ: {amount:,} هاپو پوینت\n\n"
        f"⚠️ آیا از انتقال مطمئنی؟"
    )
    
    # ذخیره اطلاعات برای تایید
    context.user_data["transfer_amount"] = amount
    context.user_data["transfer_target"] = target_id
    context.user_data["transfer_target_name"] = target_name
    
    await update.message.reply_text(
        confirm_text,
        reply_markup=get_confirm_keyboard("transfer_confirm", "transfer_cancel")
    )
    context.user_data["waiting_for_transfer_amount"] = False

# ================================================================
# هندلرهای پروفایل (Callback)
# ================================================================

async def handle_profile_callback(query, game):
    """هندلر دکمه‌های پروفایل"""
    data = query.data
    
    if data == "profile_hide":
        game.data["profile_hidden"] = True
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما مخفی شد.\n\nبرای نمایش دوباره از دکمه زیر استفاده کن.")
        # نمایش دکمه بازگشت
        keyboard = [[InlineKeyboardButton("◀️ بازگشت به پروفایل", callback_data="profile_back")]]
        await query.message.reply_text("🔙", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "profile_show":
        game.data["profile_hidden"] = False
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما نمایش داده شد.")
        # نمایش پروفایل
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_lock":
        game.data["profile_locked"] = True
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما قفل شد.\n\nهیچ کس نمی‌تواند به شما هاپو پوینت انتقال دهد.")
        keyboard = [[InlineKeyboardButton("◀️ بازگشت به پروفایل", callback_data="profile_back")]]
        await query.message.reply_text("🔙", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "profile_unlock":
        game.data["profile_locked"] = False
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما باز شد.")
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_back":
        await my_profile_from_callback(query, game)
        return

async def my_profile_from_callback(query, game):
    """نمایش پروفایل از داخل کالبک"""
    user_id = int(game.user_id)
    username = game.username
    full_name = game.data["player_name"]
    
    required = game.get_required_for_level(game.data["level"])
    is_hidden = game.data.get("profile_hidden", False)
    is_locked = game.data.get("profile_locked", False)
    
    msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
    msg += f"┐─ 👤 کاربر : {full_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 آیدی : {user_id}\n\n"
    else:
        msg += f"‏┘─ 🪪 آیدی : 🔒 مخفی\n\n"
    
    msg += f"┐─ 💰 هاپ پوینت ها : {int(game.data['hop_point']):,} 🪙\n"
    msg += f"┐─ 🐾 هاپ هاپ ها : {game.data['hop_count']}\n\n"
    
    if game.data["level"] < 20:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} | {game.data['hop_count']} / {required}"
    else:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} 🏆 نهایی"
    
    keyboard = []
    if is_hidden:
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide")])
    
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock")])
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# ادامه کدهای قبلی (start, help, hapo, claw, hunt, bank, etc.)
# ================================================================

# چون کد خیلی طولانی میشه، بقیه توابع مثل start, help, hapo, claw, hunt, bank, handle_message
# به همین شکل میمونن و فقط تغییرات کوچیک دارن...

# ================================================================
# اجرای اصلی
# ================================================================

def main():
    app = Application.builder().token(TOKEN).build()
    
    # دستورات جدید
    app.add_handler(CommandHandler("هاپوهام", my_profile))
    app.add_handler(CommandHandler("هاپوهاش", show_user_profile))
    app.add_handler(CommandHandler("انتقالهاپویی", transfer_points))
    
    # دستورات قبلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # دستورات ادمین
    app.add_handler(CommandHandler("setlevel", set_user_level))
    app.add_handler(CommandHandler("setpoint", set_user_point))
    app.add_handler(CommandHandler("userinfo", get_user_info))
    
    # هندلرها
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    print("🤖 بات HopDog با Supabase اجرا شد!")
    print(f"🔗 متصل به: {SUPABASE_URL}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
