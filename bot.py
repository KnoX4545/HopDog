# bot.py - فایل اصلی بات

import os
import logging
import random
import json
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
# ایمپورت توابع آکادمی از فایل academy.py
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
            "🔹 با یوزرنیم: `userinfo @username`\n"
            "🔹 با یوزرنیم بدون @: `userinfo username`",
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
    target_game.data["level"] = new_level
    target_game.data["hop_count"] = 0
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ سطح کاربر `{user_data['player_name']}` به {new_level} تغییر یافت.",
        parse_mode="Markdown"
    )

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
    target_game.data["hop_point"] = new_point
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ پوینت کاربر `{user_data['player_name']}` به {new_point:,} تغییر یافت.",
        parse_mode="Markdown"
    )

# ================================================================
# دستورات اصلی بات
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
            "🐾 ربات سرگرمی هاپویی 🐶\n\n🐕 یه هاپوی بامزه برای گروهت…\nکافیه توی گروه هاپ هاپ کنی تا هاپ پوینت بگیری 🐶\n\n⭐️ هاپ پوینت جمع کن و با بقیه رقابت کن\n🏆 لیدربرد هاپویی رو فتح کن و پادشاه هاپو ها شو\n\n✨ چرا هاپویی ؟\n\n⚡ پاسخگویی فوق‌العاده سریع\n🛠️ عملکرد پایدار و بدون باگ\n🔄 آپدیت‌های هفتگی\n👥 کامیونیتی فعال و پرانرژی\n🚨 پشتیبانی ۲۴ ساعته\n🪙 کاملاً رایگان برای همه\n\n🐶 کافیه ربات رو به گروهت اضافه کنی…\nبعدش شروع کنی به هاپ هاپ کردن",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🐾 سلام {display_name}!\n"
            "به هاپ داگ خوش اومدی 🐕\n\n"
            "دستورات:\n"
            "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
            "📊 هاپویی - مشاهده وضعیت خودت\n"
            "📚 آکادمی - راهنمای کامل\n"
            "🔒 برای دستورات ادمین، از پیوی بات استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_academy_main(update)

# ================================================================
# توابع اصلی (hapo, claw, hunt, bank)
# ================================================================

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
    
    # ======== ذخیره اطلاعات گروه ========
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
    if context.user_data.get("waiting_for_name"):
        if game.data["hop_point"] < 750:
            await update.message.reply_text("❌ پوینت کافی نیست")
            context.user_data["waiting_for_name"] = False
            return
        
        if len(text) > 20:
            await update.message.reply_text("❌ اسم نباید بیشتر از 20 کاراکتر باشد")
            return
        
        old_name = game.data["player_name"]
        context.user_data["new_name"] = text
        context.user_data["waiting_for_name"] = False
        
        confirm_text = f"⚠️ آیا از تغییر اسم خود از «{old_name}» به «{text}» مطمئنی؟\n💰 هزینه: 750 هاپو پوینت"
        await update.message.reply_text(
            confirm_text,
            reply_markup=get_confirm_keyboard("confirm_name_change", "cancel_name_change")
        )
        return
    
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
                "setlevel [شناسه] [عدد] - تغییر سطح\n"
                "setpoint [شناسه] [عدد] - تغییر پوینت"
            )
        else:
            await update.message.reply_text("❌ رمز اشتباه است")
        context.user_data["waiting_for_admin"] = False
        return
    
    # ======== دستورات در پیوی ========
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
    
    # ======== دستورات در گروه ========
    if is_group:
        if text_lower in ["آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی"]:
            await show_academy_main(update)
            return
        
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
        
        if text_lower in ["هاپویی"]:
            required = game.get_required_for_level(game.data["level"])
            display_name = get_user_link(user_id, username, full_name)
            msg = f"📊 وضعیت هاپویی شما\n"
            msg += f"👤 کاربر: {display_name}\n"
            if game.data.get("is_admin", False):
                msg += "🛡️ [ادمین]\n"
            msg += f"⭐ سطح: {game.data['level']}\n"
            if game.data["level"] < 20:
                msg += f"🐾 هاپ شمار: {game.data['hop_count']}/{required}\n"
            else:
                msg += "🏆 سطح نهایی\n"
            msg += f"💰 هاپو پوینت‌هات: {int(game.data['hop_point'])}"
            await update.message.reply_text(msg, parse_mode="Markdown")
            return
        
        hapo_name_lower = game.data.get("hapo_name", "").lower()
        if text_lower in ["هاپو", "hapo"] or (hapo_name_lower and text_lower == hapo_name_lower):
            await show_hapo_menu(update, game)
            return
        
        if text_lower in ["پنجه", "claw"]:
            await show_claw_menu(update, game)
            return
        
        if text_lower in ["شکار", "hunt"]:
            await do_hunt(update, game)
            return
        
        if text_lower in ["بانک هاپویی", "هاپو بانک"]:
            await show_bank_menu(update, game)
            return
        
        if text_lower in ["تغییر اسم", "اسم هاپویی"]:
            if game.data["hop_point"] < 750:
                await update.message.reply_text("❌ برای تغییر اسم به 750 هاپو پوینت نیاز داری")
                return
            await update.message.reply_text(
                "✏️ اسم جدید خود را وارد کن:\n\n"
                "💡 فقط اسم جدید رو تایپ کن و ارسال کن."
            )
            context.user_data["waiting_for_name"] = True
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
    
    # ======== سیستم هاپویی ========
    if data == "academy_system_page1":
        keyboard = [
            [InlineKeyboardButton("▶️ صفحه بعد", callback_data="academy_system_page2")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_SYSTEM_PAGE1, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_system_page2":
        keyboard = [
            [InlineKeyboardButton("◀️ صفحه قبل", callback_data="academy_system_page1")],
            [InlineKeyboardButton("▶️ صفحه بعد", callback_data="academy_system_page3")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_SYSTEM_PAGE2, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_system_page3":
        keyboard = [
            [InlineKeyboardButton("◀️ صفحه قبل", callback_data="academy_system_page2")],
            [InlineKeyboardButton("▶️ صفحه بعد", callback_data="academy_system_page4")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_SYSTEM_PAGE3, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_system_page4":
        keyboard = [
            [InlineKeyboardButton("◀️ صفحه قبل", callback_data="academy_system_page3")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_SYSTEM_PAGE4, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ======== حیوانات ========
    if data == "academy_animals_page1":
        keyboard = [
            [InlineKeyboardButton("▶️ صفحه بعد", callback_data="academy_animals_page2")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_ANIMALS_PAGE1, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_animals_page2":
        keyboard = [
            [InlineKeyboardButton("◀️ صفحه قبل", callback_data="academy_animals_page1")],
            [InlineKeyboardButton("▶️ صفحه بعد", callback_data="academy_animals_page3")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_ANIMALS_PAGE2, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_animals_page3":
        keyboard = [
            [InlineKeyboardButton("◀️ صفحه قبل", callback_data="academy_animals_page2")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_ANIMALS_PAGE3, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ======== سطح پنجه ========
    if data == "academy_claw_page1":
        keyboard = [
            [InlineKeyboardButton("▶️ صفحه بعد", callback_data="academy_claw_page2")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_CLAW_PAGE1, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_claw_page2":
        keyboard = [
            [InlineKeyboardButton("◀️ صفحه قبل", callback_data="academy_claw_page1")],
            [InlineKeyboardButton("▶️ صفحه بعد", callback_data="academy_claw_page3")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
        ]
        await query.edit_message_text(ACADEMY_CLAW_PAGE2, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "academy_claw_page3":
        keyboard = [
            [InlineKeyboardButton("◀️ صفحه قبل", callback_data="academy_claw_page2")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu")]
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
    
    # ======== تایید تغییر اسم ========
    if data == "confirm_name_change":
        new_name = context.user_data.get("new_name", "")
        if not new_name:
            await query.edit_message_text("❌ خطا در تغییر اسم")
            return
        
        if game.data["hop_point"] < 750:
            await query.edit_message_text("❌ پوینت کافی نیست")
            return
        
        old_name = game.data["player_name"]
        game.data["player_name"] = new_name
        game.data["hop_point"] -= 750
        game.save_data()
        
        await query.edit_message_text(f"✅ اسم شما از «{old_name}» به «{new_name}» تغییر یافت")
        context.user_data["new_name"] = None
        return
    
    if data == "cancel_name_change":
        await query.edit_message_text("❌ تغییر اسم لغو شد")
        context.user_data["new_name"] = None
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
            if animal and error_msg == "هاپو سیر است":
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

# ================================================================
# هنگامی که بات به گروه اضافه می‌شود
# ================================================================

async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                await update.message.reply_text("🐕 یه هاپوی ناز اینجاست\n...شروع کنید به هاپ هاپ 🐶\n\nدستورات:\n🐾 هاپ هاپ - گرفتن هاپو پوینت\n📊 هاپویی - مشاهده وضعیت خودت\n📚 آکادمی - راهنمای کامل")
                break

# ================================================================
# اجرای اصلی
# ================================================================

def main():
    app = Application.builder().token(TOKEN).build()
    
    # دستورات
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
