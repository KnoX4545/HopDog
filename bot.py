# bot.py - نسخه نهایی کامل با تمام اصلاحات

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
# داده‌های ثابت - از کد اصلی
# ================================================================

LEVEL_DATA = {
    1: {"required": 0, "minPoints": 5, "maxPoints": 15, "cooldown": 300, "reward": 0, "features": ["شروع ماجراجویی"]},
    2: {"required": 5, "minPoints": 10, "maxPoints": 20, "cooldown": 300, "reward": 50, "features": ["پنجه", "شکار", "دریافت هاپو پوینت"]},
    3: {"required": 15, "minPoints": 15, "maxPoints": 25, "cooldown": 300, "reward": 225, "features": ["هاپو", "انتقال هاپویی"]},
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

# قیمت‌های اصلی هاپو - از کد اصلی
HAPO_LEVEL_PRICES = {
    1: 250, 2: 500, 3: 5000, 4: 7500, 5: 15000,
    6: 25000, 7: 50000, 8: 75000, 9: 150000, 10: 300000,
    11: 500000, 12: 750000, 13: 1000000, 14: 1500000, 15: 2500000,
    16: 5000000, 17: 7500000, 18: 10000000, 19: 15000000, 20: 20000000,
    21: 25000000, 22: 30000000, 23: 35000000, 24: 40000000, 25: 50000000
}

# قیمت‌های ارتقا مقام
RANK_UP_PRICES = [15000, 150000, 1500000, 15000000]  # رنک 0→1, 1→2, 2→3, 3→4

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

# محدودیت‌های انتقال
TRANSFER_MIN_AMOUNT = 50
TRANSFER_MAX_AMOUNT = 500000
TRANSFER_COOLDOWN = 30
TRANSFER_MIN_LEVEL_SENDER = 3
TRANSFER_MIN_LEVEL_RECEIVER = 2

# تایمر شکار
HUNT_DECISION_TIMER = 60

# ================================================================
# ایمپورت از academy.py
# ================================================================

from academy import (
    ACADEMY_MAIN, ACADEMY_SUB_SYSTEM, ACADEMY_SUB_FEATURES, ACADEMY_SUB_ADVENTURE,
    ACADEMY_SYSTEM_PAGE1, ACADEMY_SYSTEM_PAGE2, ACADEMY_SYSTEM_PAGE3, ACADEMY_SYSTEM_PAGE4,
    ACADEMY_ANIMALS_PAGE1, ACADEMY_ANIMALS_PAGE2, ACADEMY_ANIMALS_PAGE3,
    ACADEMY_CLAW_PAGE1, ACADEMY_CLAW_PAGE2, ACADEMY_CLAW_PAGE3,
    ACADEMY_HAPO, ACADEMY_HUNT, ACADEMY_BANK, ACADEMY_TRANSFER,
    ACADEMY_HOP, ACADEMY_POINTS, ACADEMY_EXP, ACADEMY_PROFILE,
    show_academy_main, show_academy_system_menu, show_academy_features_menu,
    show_academy_adventure_menu,
    show_academy_system_pages, show_academy_animals_pages, show_academy_claw_pages,
    show_feature_page, show_adventure_page
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
                if "profile_hidden" not in data:
                    data["profile_hidden"] = False
                if "profile_locked" not in data:
                    data["profile_locked"] = False
                if "last_transfer_time" not in data:
                    data["last_transfer_time"] = 0
                if "hunt_time" not in data:
                    data["hunt_time"] = 0
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
            "profile_hidden": False,
            "profile_locked": False,
            "last_transfer_time": 0,
            "hunt_time": 0,
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

    # ============================================================
    # متدهای هاپو - اصلاح شده
    # ============================================================

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

    def get_hapo_rank_up_price(self):
        current_rank = self.data["hapo_rank"]
        if current_rank >= 4:
            return float('inf')
        return RANK_UP_PRICES[current_rank] if current_rank < len(RANK_UP_PRICES) else float('inf')

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

    def can_rank_up(self):
        if self.data["hapo_level"] < 5:
            return {"success": False, "reason": "هاپو باید سطح 5 باشد تا بتواند مقام خود را ارتقا دهد"}
        if self.data["hapo_rank"] >= 4:
            return {"success": False, "reason": "هاپو در بالاترین مقام قرار دارد"}
        return {"success": True}

    def confirm_rank_up(self):
        if self.data["hapo_rank"] >= 4:
            return {"success": False, "reason": "هاپو در بالاترین مقام قرار دارد"}
        
        price = self.get_hapo_rank_up_price()
        if self.data["hop_point"] < price:
            return {"success": False, "reason": f"به {price:,} هاپو پوینت نیاز داری"}
        
        self.data["hop_point"] -= price
        self.data["hapo_rank"] += 1
        self.data["hapo_level"] = 1
        self.data["hapo_food"] = self.get_hapo_max_food()
        self.data["hapo_harvest"] = 0
        self.data["hapo_last_update"] = datetime.now().timestamp()
        self.save_data()
        
        return {
            "success": True, 
            "new_rank": self.data["hapo_rank"],
            "new_rank_name": RANK_NAMES[self.data["hapo_rank"]]
        }

    # ============================================================
    # متدهای پنجه و شکار
    # ============================================================

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
        
        # بررسی تایمر 60 ثانیه برای حیوان قبلی
        if self.data.get("current_hunt_animal") and self.data.get("hunt_time", 0) > 0:
            now = datetime.now().timestamp()
            elapsed = now - self.data["hunt_time"]
            if elapsed < HUNT_DECISION_TIMER:
                remaining = HUNT_DECISION_TIMER - elapsed
                return {
                    "success": False, 
                    "reason": f"⏳ هنوز حیوان قبلی رو تصمیم نگرفتی! {int(remaining)} ثانیه مونده",
                    "hunt_active": True,
                    "remaining": remaining
                }
            else:
                animal_name = self.data["current_hunt_animal"].get("name", "حیوان")
                self.data["current_hunt_animal"] = None
                self.data["hunt_time"] = 0
                self.save_data()
                return {"success": False, "reason": f"🦌 {animal_name} فرار کرد! وقتت تموم شد."}
        
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
        self.data["hunt_time"] = datetime.now().timestamp()
        self.save_data()
        return {"success": True, "animal": animal}

    def sell_animal(self):
        animal = self.data.get("current_hunt_animal")
        if not animal:
            return {"success": False, "reason": "هیچ حیوانی برای فروش وجود ندارد"}
        
        if self.data.get("hunt_time", 0) > 0:
            now = datetime.now().timestamp()
            if (now - self.data["hunt_time"]) > HUNT_DECISION_TIMER:
                animal_name = animal.get("name", "حیوان")
                self.data["current_hunt_animal"] = None
                self.data["hunt_time"] = 0
                self.save_data()
                return {"success": False, "reason": f"🦌 {animal_name} فرار کرد! وقتت تموم شد."}
        
        value = animal["value"]
        self.data["hop_point"] += value
        self.data["current_hunt_animal"] = None
        self.data["hunt_time"] = 0
        self.save_data()
        return {"success": True, "value": value}

    def feed_hapo(self):
        animal = self.data.get("current_hunt_animal")
        if not animal:
            return {"success": False, "reason": "هیچ حیوانی برای غذا دادن وجود ندارد"}
        if not self.data["hapo_owned"]:
            return {"success": False, "reason": "شما هاپو ندارید"}
        
        if self.data.get("hunt_time", 0) > 0:
            now = datetime.now().timestamp()
            if (now - self.data["hunt_time"]) > HUNT_DECISION_TIMER:
                animal_name = animal.get("name", "حیوان")
                self.data["current_hunt_animal"] = None
                self.data["hunt_time"] = 0
                self.save_data()
                return {"success": False, "reason": f"🦌 {animal_name} فرار کرد! وقتت تموم شد."}
        
        max_food = self.get_hapo_max_food()
        if self.data["hapo_food"] >= max_food:
            return {"success": False, "reason": "هاپو سیر است"}
        
        nutrition = animal["nutrition"]
        new_food = min(max_food, int(self.data["hapo_food"] + nutrition))
        actual = new_food - int(self.data["hapo_food"])
        self.data["hapo_food"] = new_food
        self.data["current_hunt_animal"] = None
        self.data["hunt_time"] = 0
        self.save_data()
        return {"success": True, "fed": actual}

    # ============================================================
    # متدهای بانک
    # ============================================================

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

    # ============================================================
    # متدهای انتقال
    # ============================================================

    def can_transfer(self):
        if self.data["level"] < TRANSFER_MIN_LEVEL_SENDER:
            return {"success": False, "reason": f"برای انتقال هاپو پوینت باید سطح {TRANSFER_MIN_LEVEL_SENDER} باشی"}
        
        if self.data.get("profile_locked", False):
            return {"success": False, "reason": "پروفایل شما قفل است. ابتدا آن را باز کن"}
        
        now = datetime.now().timestamp()
        last_transfer = self.data.get("last_transfer_time", 0)
        if last_transfer > 0 and (now - last_transfer) < TRANSFER_COOLDOWN:
            remaining = TRANSFER_COOLDOWN - (now - last_transfer)
            return {"success": False, "reason": f"بین انتقال‌ها باید {TRANSFER_COOLDOWN} ثانیه صبر کنی. {int(remaining)} ثانیه مونده"}
        
        return {"success": True}

    def transfer_points(self, target_user_id, amount):
        can = self.can_transfer()
        if not can["success"]:
            return can
        
        if amount < TRANSFER_MIN_AMOUNT:
            return {"success": False, "reason": f"حداقل مبلغ انتقال {TRANSFER_MIN_AMOUNT} هاپو پوینت است"}
        
        if amount > TRANSFER_MAX_AMOUNT:
            return {"success": False, "reason": f"حداکثر مبلغ انتقال {TRANSFER_MAX_AMOUNT:,} هاپو پوینت است"}
        
        if self.data["hop_point"] < amount:
            return {"success": False, "reason": f"موجودی کافی نیست. شما {int(self.data['hop_point']):,} هاپو پوینت داری"}
        
        target_game = get_game(int(target_user_id))
        target_data = target_game.data
        
        if target_data["level"] < TRANSFER_MIN_LEVEL_RECEIVER:
            return {"success": False, "reason": f"کاربر مقصد باید حداقل سطح {TRANSFER_MIN_LEVEL_RECEIVER} داشته باشد"}
        
        if target_data.get("profile_locked", False):
            return {"success": False, "reason": "پروفایل کاربر مقصد قفل است"}
        
        self.data["hop_point"] -= amount
        target_game.data["hop_point"] += amount
        self.data["last_transfer_time"] = datetime.now().timestamp()
        
        self.save_data()
        target_game.save_data()
        
        return {
            "success": True, 
            "amount": amount, 
            "target_name": target_data["player_name"],
            "target_id": target_user_id
        }

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
        price = game.get_hapo_rank_up_price()
        if price != float('inf'):
            keyboard.append([InlineKeyboardButton(f"🌟 ارتقا مقام ({price:,})", callback_data="hapo_rank_up_confirm")])
    else:
        price = game.get_hapo_upgrade_price()
        if price != float('inf'):
            keyboard.append([InlineKeyboardButton(f"⬆️ ارتقا سطح ({price:,})", callback_data="hapo_level_up")])
    
    if game.data["hop_point"] >= 750:
        keyboard.append([InlineKeyboardButton("✏️ تغییر اسم هاپو", callback_data="hapo_rename")])
    
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
        if game.data["hapo_level"] >= 5 and game.data["hapo_rank"] < 4:
            rank_price = game.get_hapo_rank_up_price()
            msg += f"💰 هزینه ارتقا مقام: {rank_price:,} هاپو پوینت"
        else:
            msg += f"💰 هزینه ارتقا سطح: {price:,} هاپو پوینت"
    else:
        msg += "🏆 مقام نهایی"
    
    return msg

# ================================================================
# ================================================================
# دستورات جدید (فارسی)
# ================================================================

TRANSFER_STATE = {}

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور هاپوهام - نمایش پروفایل خود"""
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
    
    keyboard = []
    if is_hidden:
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show_confirm")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide_confirm")])
    
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock_confirm")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock_confirm")])
    
    try:
        user_photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if user_photos.total_count > 0:
            photo = user_photos.photos[0][-1]
            await update.message.reply_photo(
                photo.file_id,
                caption=msg,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    except:
        pass
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور هاپوهاش - نمایش پروفایل کاربر دیگر با ریپلای"""
    user_id = update.effective_user.id
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لطفاً روی پیام یک کاربر ریپلای کن و «هاپوهاش» رو بزن.")
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    target_username = update.message.reply_to_message.from_user.username
    target_full_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    
    target_game = get_game(target_user_id, target_username or target_full_name)
    target_data = target_game.data
    
    if target_data.get("profile_hidden", False):
        msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
        msg += f"┐─ 👤 کاربر : {target_full_name}\n"
        msg += f"┘─ 🔒 این کاربر پروفایل خود را مخفی کرده است."
        
        await update.message.reply_text(msg)
        return
    
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

async def transfer_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور انتقال هاپویی - با ریپلای یا یوزرنیم"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if game.data["level"] < TRANSFER_MIN_LEVEL_SENDER:
        await update.message.reply_text(f"❌ برای انتقال هاپو پوینت باید سطح {TRANSFER_MIN_LEVEL_SENDER} باشی.")
        return
    
    if game.data.get("profile_locked", False):
        await update.message.reply_text("❌ پروفایل شما قفل است. ابتدا آن را باز کن.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ لطفاً روی پیام یک کاربر ریپلای کن و «انتقال هاپویی» رو بزن.\n\n"
            "یا از این فرمت استفاده کن:\n"
            "`انتقال هاپویی @username 1000`\n"
            "`انتقال هاپویی 123456789 1000`",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    target_full_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    
    if target_user_id == user_id:
        await update.message.reply_text("❌ نمی‌تونی به خودت هاپو پوینت انتقال بدی!")
        return
    
    target_game = get_game(target_user_id)
    if target_game.data["level"] < TRANSFER_MIN_LEVEL_RECEIVER:
        await update.message.reply_text(f"❌ کاربر مقصد باید حداقل سطح {TRANSFER_MIN_LEVEL_RECEIVER} داشته باشد.")
        return
    
    if target_game.data.get("profile_locked", False):
        await update.message.reply_text("❌ پروفایل کاربر مقصد قفل است.")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "💰 مبلغ مورد نظر را به عدد وارد کن:\n"
            f"(حداقل: {TRANSFER_MIN_AMOUNT} - حداکثر: {TRANSFER_MAX_AMOUNT:,})"
        )
        context.user_data["waiting_for_transfer_amount"] = True
        TRANSFER_STATE[user_id] = {
            "target_id": target_user_id,
            "target_name": target_full_name
        }
        return
    
    try:
        amount = int(parts[-1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر برای مبلغ وارد کن.")
        return
    
    result = game.transfer_points(target_user_id, amount)
    if result["success"]:
        await update.message.reply_text(
            f"✅ انتقال موفقیت‌آمیز بود!\n\n"
            f"💰 {amount:,} هاپو پوینت به {target_full_name} انتقال یافت."
        )
        try:
            await context.bot.send_message(
                target_user_id,
                f"💰 {full_name} مبلغ {amount:,} هاپو پوینت به شما انتقال داد!"
            )
        except:
            pass
    else:
        await update.message.reply_text(f"❌ {result['reason']}")

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
    
    transfer_info = TRANSFER_STATE.get(user_id)
    if not transfer_info:
        await update.message.reply_text("❌ خطا در انتقال. لطفاً دوباره تلاش کن.")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    target_id = transfer_info["target_id"]
    target_name = transfer_info["target_name"]
    
    result = game.transfer_points(target_id, amount)
    if result["success"]:
        await update.message.reply_text(
            f"✅ انتقال موفقیت‌آمیز بود!\n\n"
            f"💰 {amount:,} هاپو پوینت به {target_name} انتقال یافت."
        )
        try:
            await context.bot.send_message(
                target_id,
                f"💰 {full_name} مبلغ {amount:,} هاپو پوینت به شما انتقال داد!"
            )
        except:
            pass
    else:
        await update.message.reply_text(f"❌ {result['reason']}")
    
    context.user_data["waiting_for_transfer_amount"] = False
    if user_id in TRANSFER_STATE:
        del TRANSFER_STATE[user_id]

# ================================================================
# دستورات ادمین
# ================================================================

async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید. فقط ادمین‌ها میتونن استفاده کنن.")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ لطفاً شناسه کاربر را وارد کن.\n\n"
            "📌 مثال:\n"
            "🔹 با آیدی عددی: `userinfo 123456789`\n"
            "🔹 با یوزرنیم: `userinfo @username`",
            parse_mode="Markdown"
        )
        return
    
    identifier = parts[1]
    user_data = HopDogGame.get_user_by_identifier(identifier)
    
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    msg = f"📊 اطلاعات کاربر:\n\n"
    msg += f"🆔 آیدی: `{user_data['user_id']}`\n"
    msg += f"👤 نام: {user_data['player_name']}\n"
    msg += f"⭐ سطح: {user_data['level']}\n"
    msg += f"💰 هاپو پوینت: {user_data['hop_point']:,}\n"
    msg += f"🐾 تعداد هاپ: {user_data['hop_count']}\n"
    
    if user_data.get('hapo_owned', False):
        msg += f"\n🐕 هاپو:\n"
        msg += f"  📛 نام: {user_data['hapo_name']}\n"
        msg += f"  ⭐ سطح: {user_data['hapo_level']}/5\n"
        msg += f"  🌟 مقام: {RANK_NAMES[user_data['hapo_rank']]}\n"
    
    if user_data.get('bank_opened', False):
        msg += f"\n🏦 بانک:\n"
        msg += f"  💰 موجودی: {user_data['bank_balance']:,}\n"
    
    msg += f"\n📅 آخرین بروزرسانی: {user_data.get('last_updated', 'نامشخص')}"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def set_user_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ فرمت: setlevel [آیدی/یوزرنیم] [عدد]\nمثال: setlevel @username 5")
        return
    
    identifier = parts[1]
    try:
        new_level = int(parts[2])
        if not 1 <= new_level <= 20:
            await update.message.reply_text("❌ سطح باید بین 1 تا 20 باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        return
    
    user_data = HopDogGame.get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    old_level = target_game.data["level"]
    target_game.data["level"] = new_level
    target_game.data["hop_count"] = 0
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ سطح کاربر `{user_data['player_name']}` از {old_level} به {new_level} تغییر یافت.",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"⭐ سطح هاپویی شما به {new_level} تغییر یافت!"
        )
    except:
        pass

async def add_user_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن به سطح کاربر"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ فرمت: addlevel [آیدی/یوزرنیم] [عدد]\nمثال: addlevel @username 5")
        return
    
    identifier = parts[1]
    try:
        add_amount = int(parts[2])
        if add_amount <= 0:
            await update.message.reply_text("❌ مقدار باید مثبت باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        return
    
    user_data = HopDogGame.get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    old_level = target_game.data["level"]
    new_level = min(old_level + add_amount, 20)
    target_game.data["level"] = new_level
    target_game.data["hop_count"] = 0
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ {add_amount} سطح به کاربر `{user_data['player_name']}` اضافه شد.\n"
        f"سطح جدید: {new_level}",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"⭐ {add_amount} سطح به هاپوهای شما اضافه شد!\nسطح جدید: {new_level}"
        )
    except:
        pass

async def set_user_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ فرمت: setpoint [آیدی/یوزرنیم] [عدد]\nمثال: setpoint @username 1000")
        return
    
    identifier = parts[1]
    try:
        new_point = int(parts[2])
        if new_point < 0:
            await update.message.reply_text("❌ پوینت نمی‌تواند منفی باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        return
    
    user_data = HopDogGame.get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    old_point = target_game.data["hop_point"]
    target_game.data["hop_point"] = new_point
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ پوینت کاربر `{user_data['player_name']}` از {old_point:,} به {new_point:,} تغییر یافت.",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"💰 هاپو پوینت‌های شما به {new_point:,} تغییر یافت!"
        )
    except:
        pass

async def add_user_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن به پوینت کاربر"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ فرمت: addpoint [آیدی/یوزرنیم] [عدد]\nمثال: addpoint @username 1000")
        return
    
    identifier = parts[1]
    try:
        add_amount = int(parts[2])
        if add_amount <= 0:
            await update.message.reply_text("❌ مقدار باید مثبت باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        return
    
    user_data = HopDogGame.get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    old_point = target_game.data["hop_point"]
    new_point = old_point + add_amount
    target_game.data["hop_point"] = new_point
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ {add_amount:,} هاپو پوینت به کاربر `{user_data['player_name']}` اضافه شد.\n"
        f"پوینت جدید: {new_point:,}",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"💰 {add_amount:,} هاپو پوینت به حساب شما اضافه شد!\nموجودی جدید: {new_point:,}"
        )
    except:
        pass

# ================================================================
# توابع اصلی
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    
    display_name = get_user_link(user_id, username, full_name)
    game = get_game(user_id, username or full_name)
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{context.bot.username}?startgroup=start")]
    ]
    
    if not game.data.get("has_seen_welcome", False):
        game.data["has_seen_welcome"] = True
        game.save_data()
        await update.message.reply_text(
            "🐾 ربات سرگرمی هاپویی 🐶\n\n"
            "🐕 یه هاپوی بامزه برای گروهت…\n"
            "کافیه توی گروه هاپ هاپ کنی تا هاپ پوینت بگیری 🐶\n\n"
            "⭐️ هاپ پوینت جمع کن و با بقیه رقابت کن\n"
            "🏆 لیدربرد هاپویی رو فتح کن و پادشاه هاپو ها شو\n\n"
            "✨ چرا هاپویی ؟\n\n"
            "⚡ پاسخگویی فوق‌العاده سریع\n"
            "🛠️ عملکرد پایدار و بدون باگ\n"
            "🔄 آپدیت‌های هفتگی\n"
            "👥 کامیونیتی فعال و پرانرژی\n"
            "🚨 پشتیبانی ۲۴ ساعته\n"
            "🪙 کاملاً رایگان برای همه\n\n"
            "🐶 کافیه ربات رو به گروهت اضافه کنی…\n"
            "بعدش شروع کنی به هاپ هاپ کردن",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🐾 سلام {display_name}!\n"
            "به هاپ داگ خوش اومدی 🐕\n\n"
            "دستورات:\n"
            "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
            "📊 هاپوهام - مشاهده پروفایل خودت\n"
            "📚 آکادمی - راهنمای کامل\n"
            "💰 انتقال هاپویی - انتقال هاپو پوینت به دیگران\n"
            "🔒 برای دستورات ادمین، از پیوی بات استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_academy_main(update)

async def show_hapo_menu(update: Update, game):
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
    
    msg = get_hapo_menu_text(game)
    keyboard = get_hapo_menu_keyboard(game)
    await update.message.reply_text(msg, reply_markup=keyboard)

async def edit_to_hapo_menu(query, game, message_text=None):
    msg = get_hapo_menu_text(game)
    keyboard = get_hapo_menu_keyboard(game)
    if message_text:
        await query.edit_message_text(message_text + "\n\n" + msg, reply_markup=keyboard)
    else:
        await query.edit_message_text(msg, reply_markup=keyboard)

async def show_claw_menu(update: Update, game):
    if game.data["level"] < 2:
        await update.message.reply_text("🔒 پنجه از سطح 2 باز میشود")
        return
    
    if game.data["claw_level"] == 0:
        cost = game.get_claw_cost(1)
        keyboard = [
            [InlineKeyboardButton(f"🛒 خرید پنجه ({cost})", callback_data="buy_claw")]
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
            InlineKeyboardButton(f"⬆️ سطح {next_level} ({next_data['cost']})", callback_data="upgrade_claw")
        ])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def do_hunt(update: Update, game):
    result = game.do_hunt()
    
    if not result["success"]:
        reason = result.get("reason", "")
        if "فرار کرد" in reason:
            await update.message.reply_text(f"❌ {reason}")
        elif reason == "خسته‌ام":
            remaining = result.get("remaining", 0)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await update.message.reply_text(f"⏳ تا شکار بعدی {mins}:{secs:02d} مونده")
        elif "ثانیه مونده" in reason:
            remaining = result.get("remaining", 0)
            await update.message.reply_text(f"⏳ {reason}")
        else:
            await update.message.reply_text(f"❌ {reason}")
        return
    
    animal = result["animal"]
    msg = f"🏹 شما موفق به شکار شدید!\n"
    msg += f"{animal['emoji']} {animal['name']}\n"
    msg += f"⭐ {animal['rarity_name']}\n"
    msg += f"⚖️ وزن: {animal['weight']} کیلو\n"
    msg += f"💰 ارزش: {animal['value']} هاپو پوینت\n"
    msg += f"🍖 ارزش غذایی: {animal['nutrition']} کالری\n\n"
    msg += f"⏳ شما {HUNT_DECISION_TIMER} ثانیه فرصت دارید تا تصمیم بگیرید!"
    
    keyboard = []
    keyboard.append([
        InlineKeyboardButton(f"💰 فروش ({animal['value']})", callback_data="hunt_sell")
    ])
    if game.data["hapo_owned"]:
        keyboard.append([
            InlineKeyboardButton(f"🍖 به هاپو بده", callback_data="hunt_feed")
        ])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_bank_menu(update: Update, game):
    if game.data["level"] < 4:
        await update.message.reply_text("🏦 بانک هاپویی از سطح 4 باز میشود")
        return
    
    if not game.data["bank_opened"]:
        if game.data["hop_point"] < 5000:
            await update.message.reply_text(f"🏦 برای خرید بانک به 5000 هاپو پوینت نیاز داری")
            return
        keyboard = [
            [InlineKeyboardButton("🏦 خرید بانک (5000)", callback_data="buy_bank")]
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
    msg += f"💰 موجودی: {int(game.data['bank_balance']):,} هاپو پوینت\n"
    msg += f"💰 قابل استفاده: {int(game.data['hop_point']):,} هاپو پوینت\n\n"
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

async def show_bank_menu_callback(query, game):
    game.apply_bank_interest()
    interest = min(int(game.data["bank_balance"] * 0.03), 350000)
    
    msg = f"🏦 بانک هاپویی\n"
    msg += f"👤 {game.data['player_name']}\n"
    msg += f"💰 موجودی: {int(game.data['bank_balance']):,} هاپو پوینت\n"
    msg += f"💰 قابل استفاده: {int(game.data['hop_point']):,} هاپو پوینت\n\n"
    msg += f"🤑 سود بانکی\n"
    msg += f"📥 سود قابل دریافت: {interest:,} هاپو پوینت\n"
    msg += f"⏳ زمان واریز: 06:00 صبح"
    
    keyboard = [
        [
            InlineKeyboardButton("➕ واریز", callback_data="bank_deposit"),
            InlineKeyboardButton("➖ برداشت", callback_data="bank_withdraw")
        ]
    ]
    
    await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# هندلر پیام‌ها
# ================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    text = update.message.text.strip()
    text_lower = text.lower()
    is_private = update.message.chat.type == "private"
    is_group = update.message.chat.type in ["group", "supergroup"]
    
    if is_group:
        try:
            chat_id = update.message.chat.id
            chat_title = update.message.chat.title
            groups_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "groups.json")
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
    
    # ======== بررسی حالت‌های انتظار ========
    if context.user_data.get("waiting_for_hapo_name"):
        if game.data["hop_point"] < 750:
            await update.message.reply_text("❌ پوینت کافی نیست")
            context.user_data["waiting_for_hapo_name"] = False
            return
        
        if len(text) > 15:
            await update.message.reply_text("❌ اسم نباید بیشتر از 15 کاراکتر باشد")
            context.user_data["waiting_for_hapo_name"] = False
            return
        
        old_name = game.data["hapo_name"]
        context.user_data["new_hapo_name"] = text
        context.user_data["waiting_for_hapo_name"] = False
        
        confirm_text = f"⚠️ آیا از تغییر اسم هاپو از «{old_name}» به «{text}» مطمئنی؟\n💰 هزینه: 750 هاپو پوینت"
        await update.message.reply_text(
            confirm_text,
            reply_markup=get_confirm_keyboard("confirm_hapo_name", "cancel_hapo_name")
        )
        return
    
    if context.user_data.get("waiting_for_deposit"):
        try:
            amount = int(text.replace(",", ""))
            result = game.deposit(amount)
            if result["success"]:
                await update.message.reply_text(
                    f"✅ {amount:,} هاپو پوینت به بانک واریز شد\n"
                    f"💰 موجودی بانک: {result['new_balance']:,}\n"
                    f"💰 قابل استفاده: {int(game.data['hop_point']):,}"
                )
                await asyncio.sleep(2)
                await show_bank_menu(update, game)
            else:
                await update.message.reply_text(f"❌ {result['reason']}")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        context.user_data["waiting_for_deposit"] = False
        return
    
    if context.user_data.get("waiting_for_withdraw"):
        try:
            amount = int(text.replace(",", ""))
            result = game.withdraw(amount)
            if result["success"]:
                await update.message.reply_text(
                    f"✅ {amount:,} هاپو پوینت از بانک برداشت شد\n"
                    f"💰 موجودی بانک: {result['new_balance']:,}\n"
                    f"💰 قابل استفاده: {int(game.data['hop_point']):,}"
                )
                await asyncio.sleep(2)
                await show_bank_menu(update, game)
            else:
                await update.message.reply_text(f"❌ {result['reason']}")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        context.user_data["waiting_for_withdraw"] = False
        return
    
    if context.user_data.get("waiting_for_admin"):
        if text == ADMIN_PASSWORD:
            game.data["is_admin"] = True
            game.save_data()
            await update.message.reply_text("✅ شما ادمین شدید! 🛡️")
            await update.message.reply_text(
                "دستورات ادمین:\n"
                "userinfo [شناسه] - اطلاعات کاربر\n"
                "setlevel [شناسه] [عدد] - تنظیم سطح\n"
                "addlevel [شناسه] [عدد] - اضافه کردن سطح\n"
                "setpoint [شناسه] [عدد] - تنظیم پوینت\n"
                "addpoint [شناسه] [عدد] - اضافه کردن پوینت"
            )
        else:
            await update.message.reply_text("❌ رمز اشتباه است")
        context.user_data["waiting_for_admin"] = False
        return
    
    if context.user_data.get("waiting_for_transfer_amount"):
        await process_transfer_amount(update, context)
        return
    
    if is_private:
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
        elif text_lower == "kknoxx1":
            await update.message.reply_text("🔑 رمز ادمین را وارد کن:")
            context.user_data["waiting_for_admin"] = True
        return
    
    if is_group:
        # ======== دستورات جدید فارسی ========
        if text_lower in ["هاپوهام", "هاپو هام"]:
            await my_profile(update, context)
            return
        
        if text_lower in ["هاپوهاش", "هاپو هاش"]:
            await show_user_profile(update, context)
            return
        
        if text_lower in ["انتقال هاپویی", "انتقالهاپویی", "انتقال"]:
            await transfer_points_command(update, context)
            return
        
        # ======== دستورات هاپ ========
        if text_lower in ["هاپ هاپ", "هاپ", "hop", "hop hop", "واق", "واق واق", "هاپ هوپ", "هوپ", "hap", "hap hap"]:
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
        
        # ======== آکادمی ========
        if text_lower in ["آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی"]:
            await show_academy_main(update)
            return
        
        # ======== هاپو ========
        hapo_name_lower = game.data.get("hapo_name", "").lower()
        if text_lower in ["هاپو", "hapo"] or (hapo_name_lower and text_lower == hapo_name_lower):
            await show_hapo_menu(update, game)
            return
        
        # ======== پنجه ========
        if text_lower in ["پنجه", "claw"]:
            await show_claw_menu(update, game)
            return
        
        # ======== شکار ========
        if text_lower in ["شکار", "hunt"]:
            await do_hunt(update, game)
            return
        
        # ======== بانک ========
        if text_lower in ["بانک هاپویی", "هاپو بانک"]:
            await show_bank_menu(update, game)
            return

# ================================================================
# هندلر Callback
# ================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    data = query.data
    
    # ======== آکادمی ========
    if data == "academy_back_main":
        await show_academy_main(update, query)
        return
    
    if data == "academy_system_menu":
        await show_academy_system_menu(update, query)
        return
    
    if data == "academy_features_menu":
        await show_academy_features_menu(update, query)
        return
    
    if data == "academy_adventure_menu":
        await show_academy_adventure_menu(update, query)
        return
    
    if data.startswith("academy_system_page"):
        page = int(data.replace("academy_system_page", ""))
        await show_academy_system_pages(update, query, page)
        return
    
    if data.startswith("academy_animals_page"):
        page = int(data.replace("academy_animals_page", ""))
        await show_academy_animals_pages(update, query, page)
        return
    
    if data.startswith("academy_claw_page"):
        page = int(data.replace("academy_claw_page", ""))
        await show_academy_claw_pages(update, query, page)
        return
    
    if data == "academy_hapo":
        await show_feature_page(update, query, "hapo")
        return
    
    if data == "academy_hunt":
        await show_feature_page(update, query, "hunt")
        return
    
    if data == "academy_bank":
        await show_feature_page(update, query, "bank")
        return
    
    if data == "academy_transfer":
        await show_feature_page(update, query, "transfer")
        return
    
    if data == "academy_hop":
        await show_adventure_page(update, query, "hop")
        return
    
    if data == "academy_points":
        await show_adventure_page(update, query, "points")
        return
    
    if data == "academy_exp":
        await show_adventure_page(update, query, "exp")
        return
    
    if data == "academy_profile":
        await show_adventure_page(update, query, "profile")
        return
    
    # ======== تایید تغییر اسم هاپو ========
    if data == "confirm_hapo_name":
        new_name = context.user_data.get("new_hapo_name", "")
        if not new_name:
            await query.edit_message_text("❌ خطا در تغییر اسم")
            return
        
        if game.data["hop_point"] < 750:
            await query.edit_message_text("❌ پوینت کافی نیست")
            return
        
        old_name = game.data["hapo_name"]
        game.data["hapo_name"] = new_name
        game.data["hop_point"] -= 750
        game.save_data()
        
        await query.edit_message_text(f"✅ اسم هاپو از «{old_name}» به «{new_name}» تغییر یافت")
        context.user_data["new_hapo_name"] = None
        await asyncio.sleep(2)
        await edit_to_hapo_menu(query, game)
        return
    
    if data == "cancel_hapo_name":
        await query.edit_message_text("❌ تغییر اسم هاپو لغو شد")
        context.user_data["new_hapo_name"] = None
        return
    
    # ======== پروفایل ========
    if data == "profile_hide_confirm":
        keyboard = get_confirm_keyboard("profile_hide_yes", "profile_hide_no")
        await query.edit_message_text(
            "⚠️ آیا از مخفی کردن پروفایل خود مطمئنی؟\n\n"
            "با این کار:\n"
            "┘─ 👀 پروفایل شما برای دیگران مخفی میشود\n"
            "┘─ 🖼 عکس پروفایل شما نمایش داده نمیشود\n"
            "‏┘─ 🪪 آیدی شما در بخش های مختلف مخفی میشود",
            reply_markup=keyboard
        )
        return
    
    if data == "profile_hide_yes":
        game.data["profile_hidden"] = True
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما مخفی شد.")
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_hide_no":
        await query.edit_message_text("❌ مخفی کردن پروفایل لغو شد.")
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_show_confirm":
        keyboard = get_confirm_keyboard("profile_show_yes", "profile_show_no")
        await query.edit_message_text(
            "⚠️ آیا از نمایش پروفایل خود مطمئنی؟\n\n"
            "با این کار:\n"
            "┘─ 👀 پروفایل شما برای دیگران نمایش داده میشود\n"
            "┘─ 🖼 عکس پروفایل شما نمایش داده میشود\n"
            "‏┘─ 🪪 آیدی شما در بخش های مختلف نمایش داده میشود",
            reply_markup=keyboard
        )
        return
    
    if data == "profile_show_yes":
        game.data["profile_hidden"] = False
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما نمایش داده شد.")
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_show_no":
        await query.edit_message_text("❌ نمایش پروفایل لغو شد.")
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_lock_confirm":
        keyboard = get_confirm_keyboard("profile_lock_yes", "profile_lock_no")
        await query.edit_message_text(
            "⚠️ آیا از قفل کردن پروفایل خود مطمئنی؟\n\n"
            "با این کار:\n"
            "┘─ 🧲 جلوگیری از دریافت انتقال هاپویی\n"
            "┘─ هیچ کس نمی‌تواند به شما هاپو پوینت انتقال دهد",
            reply_markup=keyboard
        )
        return
    
    if data == "profile_lock_yes":
        game.data["profile_locked"] = True
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما قفل شد.")
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_lock_no":
        await query.edit_message_text("❌ قفل کردن پروفایل لغو شد.")
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_unlock_confirm":
        keyboard = get_confirm_keyboard("profile_unlock_yes", "profile_unlock_no")
        await query.edit_message_text(
            "⚠️ آیا از باز کردن پروفایل خود مطمئنی؟\n\n"
            "با این کار:\n"
            "┘─ 🧲 امکان دریافت انتقال هاپویی فعال میشود\n"
            "┘─ دیگران می‌توانند به شما هاپو پوینت انتقال دهند",
            reply_markup=keyboard
        )
        return
    
    if data == "profile_unlock_yes":
        game.data["profile_locked"] = False
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما باز شد.")
        await my_profile_from_callback(query, game)
        return
    
    if data == "profile_unlock_no":
        await query.edit_message_text("❌ باز کردن پروفایل لغو شد.")
        await my_profile_from_callback(query, game)
        return
    
    # ======== ارتقا مقام هاپو ========
    if data == "hapo_rank_up_confirm":
        check = game.can_rank_up()
        if not check["success"]:
            await query.edit_message_text(f"❌ {check['reason']}")
            return
        
        price = game.get_hapo_rank_up_price()
        if game.data["hop_point"] < price:
            await query.edit_message_text(f"❌ به {price:,} هاپو پوینت نیاز داری")
            return
        
        msg = f"⚠️ آیا از ارتقا مقام هاپو مطمئنی؟\n\n"
        msg += f"🌟 مقام فعلی: {RANK_NAMES[game.data['hapo_rank']]}\n"
        msg += f"🌟 مقام جدید: {RANK_NAMES[game.data['hapo_rank'] + 1]}\n"
        msg += f"💰 هزینه: {price:,} هاپو پوینت\n\n"
        msg += "❗️ با ارتقا مقام:\n"
        msg += "┘─ سطح هاپو به 1 ریست میشود\n"
        msg += "┘─ تولیدی هاپو صفر میشود\n"
        msg += "┘─ ظرفیت هاپو افزایش می‌یابد\n"
        
        keyboard = get_confirm_keyboard("hapo_rank_up_yes", "hapo_rank_up_no")
        await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "hapo_rank_up_yes":
        result = game.confirm_rank_up()
        if result["success"]:
            await query.edit_message_text(
                f"✅ مقام هاپو به {result['new_rank_name']} ارتقا یافت!\n\n"
                f"🌟 سطح هاپو به 1 ریست شد\n"
                f"💰 تولیدی هاپو صفر شد\n"
                f"📦 ظرفیت هاپو افزایش یافت"
            )
            await asyncio.sleep(2)
            await edit_to_hapo_menu(query, game)
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "hapo_rank_up_no":
        await query.edit_message_text("❌ ارتقا مقام لغو شد.")
        await asyncio.sleep(1)
        await edit_to_hapo_menu(query, game)
        return
    
    # ======== هاپو ========
    if data == "buy_hapo":
        result = game.buy_hapo()
        if result["success"]:
            await query.edit_message_text(
                f"✅ هاپو خریداری شد!\n"
                f"اسم هاپو: {result['name']}\n\n"
                f"💡 برای دیدن منوی هاپو، کلمه «هاپو» رو بزن"
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
            await asyncio.sleep(2)
            await edit_to_hapo_menu(query, game)
        else:
            await query.edit_message_text("❌ هیچ هاپو پوینتی برای برداشت نیست")
            await asyncio.sleep(2)
            await edit_to_hapo_menu(query, game)
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
        await asyncio.sleep(2)
        await edit_to_hapo_menu(query, game)
        return
    
    if data == "hapo_rename":
        if game.data["hop_point"] < 750:
            await query.edit_message_text("❌ به 750 هاپو پوینت نیاز داری")
            return
        await query.edit_message_text(
            "✏️ اسم جدید هاپو رو وارد کن:\n\n"
            "💡 فقط اسم جدید رو تایپ کن و ارسال کن."
        )
        context.user_data["waiting_for_hapo_name"] = True
        return
    
    # ======== پنجه ========
    if data == "buy_claw":
        result = game.buy_claw()
        if result["success"]:
            await query.edit_message_text("✅ پنجه خریداری شد!\nحالا میتونی با دستور شکار بری شکار")
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
            await query.edit_message_text(
                f"💰 حیوان فروخته شد!\n"
                f"✅ {result['value']} هاپو پوینت دریافت کردی"
            )
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "hunt_feed":
        result = game.feed_hapo()
        if result["success"]:
            await query.edit_message_text(
                f"🍖 {result['fed']} غذا به هاپو داده شد\n"
                f"✅ هاپو سیر شد!"
            )
        else:
            error_msg = result["reason"]
            animal = game.data.get("current_hunt_animal")
            if animal and "فرار کرد" in error_msg:
                await query.edit_message_text(f"❌ {error_msg}")
            elif animal and error_msg == "هاپو سیر است":
                await query.edit_message_text(
                    f"❌ هاپو سیر است!\n"
                    f"می‌تونی حیوان رو بفروشی یا بعداً به هاپو بدی.\n\n"
                    f"{animal['emoji']} {animal['name']}\n"
                    f"💰 ارزش: {animal['value']} هاپو پوینت"
                )
                keyboard = [
                    [InlineKeyboardButton(f"💰 فروش ({animal['value']})", callback_data="hunt_sell")]
                ]
                await query.message.reply_text(
                    "برای فروش کلیک کن:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.edit_message_text(f"❌ {error_msg}")
        return
    
    # ======== بانک ========
    if data == "buy_bank":
        result = game.open_bank()
        if result["success"]:
            await query.edit_message_text("🏦 بانک هاپویی خریداری شد!")
            await asyncio.sleep(2)
            await show_bank_menu_callback(query, game)
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "bank_deposit":
        await query.edit_message_text(
            "💰 مبلغ واریزی رو بنویس:\n\n"
            "💡 فقط عدد مبلغ رو تایپ کن و ارسال کن."
        )
        context.user_data["waiting_for_deposit"] = True
        return
    
    if data == "bank_withdraw":
        await query.edit_message_text(
            "💰 مبلغ برداشت رو بنویس:\n\n"
            "💡 فقط عدد مبلغ رو تایپ کن و ارسال کن."
        )
        context.user_data["waiting_for_withdraw"] = True
        return
    
    # ======== انتقال ========
    if data == "transfer_confirm":
        amount = context.user_data.get("transfer_amount")
        target_id = context.user_data.get("transfer_target")
        target_name = context.user_data.get("transfer_target_name")
        
        if not amount or not target_id:
            await query.edit_message_text("❌ خطا در انتقال. لطفاً دوباره تلاش کن.")
            return
        
        result = game.transfer_points(target_id, amount)
        if result["success"]:
            await query.edit_message_text(
                f"✅ انتقال موفقیت‌آمیز بود!\n\n"
                f"💰 {amount:,} هاپو پوینت به {target_name} انتقال یافت."
            )
            try:
                await context.bot.send_message(
                    target_id,
                    f"💰 {game.data['player_name']} مبلغ {amount:,} هاپو پوینت به شما انتقال داد!"
                )
            except:
                pass
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        
        context.user_data["transfer_amount"] = None
        context.user_data["transfer_target"] = None
        context.user_data["transfer_target_name"] = None
        return
    
    if data == "transfer_cancel":
        await query.edit_message_text("❌ انتقال لغو شد.")
        context.user_data["transfer_amount"] = None
        context.user_data["transfer_target"] = None
        context.user_data["transfer_target_name"] = None
        context.user_data["waiting_for_transfer_amount"] = False
        if user_id in TRANSFER_STATE:
            del TRANSFER_STATE[user_id]
        return

async def my_profile_from_callback(query, game):
    user_id = int(game.user_id)
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
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show_confirm")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide_confirm")])
    
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock_confirm")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock_confirm")])
    
    try:
        user_photos = await query.message.bot.get_user_profile_photos(user_id, limit=1)
        if user_photos.total_count > 0 and not is_hidden:
            photo = user_photos.photos[0][-1]
            await query.edit_message_media(
                InputMediaPhoto(media=photo.file_id, caption=msg),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    except:
        pass
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# هنگامی که بات به گروه اضافه می‌شود
# ================================================================

async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                await update.message.reply_text(
                    "🐕 یه هاپوی ناز اینجاست\n"
                    "...شروع کنید به هاپ هاپ 🐶\n\n"
                    "دستورات:\n"
                    "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
                    "📊 هاپوهام - مشاهده پروفایل خودت\n"
                    "💰 انتقال هاپویی - انتقال هاپو پوینت\n"
                    "📚 آکادمی - راهنمای کامل"
                )
                break

# ================================================================
# اجرای اصلی
# ================================================================

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    app.add_handler(CommandHandler("setlevel", set_user_level))
    app.add_handler(CommandHandler("addlevel", add_user_level))
    app.add_handler(CommandHandler("setpoint", set_user_point))
    app.add_handler(CommandHandler("addpoint", add_user_point))
    app.add_handler(CommandHandler("userinfo", get_user_info))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    print("🤖 بات HopDog با Supabase اجرا شد!")
    print(f"🔗 متصل به: {SUPABASE_URL}")
    print(f"💰 حداقل انتقال: {TRANSFER_MIN_AMOUNT}")
    print(f"💰 حداکثر انتقال: {TRANSFER_MAX_AMOUNT:,}")
    print(f"⏳ کولداون انتقال: {TRANSFER_COOLDOWN} ثانیه")
    print(f"⏳ تایمر تصمیم‌گیری شکار: {HUNT_DECISION_TIMER} ثانیه")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
