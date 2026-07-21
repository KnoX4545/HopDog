# game.py - کلاس اصلی بازی (نسخه نهایی با تبدیل در کد)

import random
import json
from datetime import datetime, timedelta
from config import *
from database import get_user_data, save_user_data, get_user_by_card, is_card_unique


class HopDogGame:
    def __init__(self, user_id, username=""):
        self.user_id = str(user_id)
        self.username = username
        self.data = self.load_data()
        if not self.data:
            self.reset_data()

    # ============================================================
    # توابع کمکی تبدیل (مهم!)
    # ============================================================

    def _to_int(self, value):
        """تبدیل مطمئن به int (حتی اگر string با اعشار باشه)"""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value))
            except:
                return 0
        return 0

    def _to_float(self, value):
        """تبدیل مطمئن به float"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except:
                return 0.0
        return 0.0

    def _to_str(self, value):
        """تبدیل به string"""
        if value is None:
            return "0"
        return str(value)

    # ============================================================
    # متدهای اصلی
    # ============================================================

    def load_data(self):
        data = get_user_data(self.user_id)
        if data:
            if "current_hunt_animal" in data and data["current_hunt_animal"]:
                try:
                    data["current_hunt_animal"] = json.loads(data["current_hunt_animal"])
                except:
                    data["current_hunt_animal"] = None
            if "bank_transactions" in data and data["bank_transactions"]:
                try:
                    data["bank_transactions"] = json.loads(data["bank_transactions"])
                except:
                    data["bank_transactions"] = []
            else:
                data["bank_transactions"] = []
            if "jail_voted" in data and data["jail_voted"]:
                try:
                    data["jail_voted"] = json.loads(data["jail_voted"])
                except:
                    data["jail_voted"] = []
            else:
                data["jail_voted"] = []
            # فیلدهای جدید - اطمینان از وجود
            if "bank_card_number" not in data:
                data["bank_card_number"] = ""
            if "jail_admin_id" not in data:
                data["jail_admin_id"] = None
            if "hunt_time" not in data:
                data["hunt_time"] = "0"
            if "is_transferring" not in data:
                data["is_transferring"] = False
            if "profile_hidden" not in data:
                data["profile_hidden"] = False
            if "profile_locked" not in data:
                data["profile_locked"] = False
            if "street_hapo_rescued" not in data:
                data["street_hapo_rescued"] = "0"
            # چک کردن خودکار آزادی
            if data.get("jailed", False):
                now = datetime.now().timestamp()
                jail_until = self._to_float(data.get("jail_until", 0))
                if now >= jail_until:
                    data["jailed"] = False
                    data["jail_reason"] = ""
                    data["jail_until"] = "0"
                    data["jail_fine"] = "0"
                    data["jail_arrest_time"] = "0"
                    data["jail_admin_id"] = None
                    save_user_data(self.user_id, data)
            return data
        return None

    def save_data(self):
        return save_user_data(self.user_id, self.data)

    def reset_data(self):
        self.data = {
            "user_id": self.user_id,
            "player_name": self.username or f"کاربر{self.user_id}",
            "hop_point": "0",
            "last_hop_time": "0",
            "level": "1",
            "hop_count": "0",
            "is_admin": False,
            "claw_level": "0",
            "last_hunt_time": "0",
            "hunt_active": False,
            "hapo_owned": False,
            "hapo_name": "",
            "hapo_rank": "0",
            "hapo_level": "1",
            "hapo_food": "4",
            "hapo_harvest": "0",
            "hapo_last_update": str(datetime.now().timestamp()),
            "bank_opened": False,
            "bank_balance": "0",
            "bank_last_interest_at": "0",
            "has_seen_welcome": False,
            "current_hunt_animal": None,
            "profile_hidden": False,
            "profile_locked": False,
            "hunt_time": "0",
            "last_transfer_time": "0",
            "is_transferring": False,
            "bank_card_number": "",
            "bank_transactions": [],
            "jailed": False,
            "jail_reason": "",
            "jail_until": "0",
            "jail_fine": "0",
            "jail_arrest_time": "0",
            "jail_voted": [],
            "jail_admin_id": None,
            "street_hapo_rescued": "0",
            "last_updated": datetime.now().isoformat()
        }
        self.save_data()

    # ============================================================
    # متدهای سطح و هاپ
    # ============================================================

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
        cooldown = self.get_cooldown_for_level(self._to_int(self.data["level"]))
        
        last_hop_time = self._to_float(self.data["last_hop_time"])
        
        if last_hop_time > 0 and (now - last_hop_time) < cooldown:
            remaining = cooldown - (now - last_hop_time)
            return {"success": False, "remaining": remaining}
        
        level_data = self.get_level_data(self._to_int(self.data["level"]))
        earned = random.randint(level_data["minPoints"], level_data["maxPoints"])
        
        hop_point = self._to_int(self.data["hop_point"])
        self.data["hop_point"] = self._to_str(hop_point + earned)
        self.data["last_hop_time"] = self._to_str(now)
        
        hop_count = self._to_int(self.data["hop_count"])
        self.data["hop_count"] = self._to_str(hop_count + 1)
        
        level = self._to_int(self.data["level"])
        required = self.get_required_for_level(level)
        if level < MAX_LEVEL and hop_count + 1 >= required:
            self.data["hop_count"] = "0"
            self.data["level"] = self._to_str(level + 1)
            reward = self.get_level_data(level + 1)["reward"]
            hop_point = self._to_int(self.data["hop_point"])
            self.data["hop_point"] = self._to_str(hop_point + reward)
            self.save_data()
            return {
                "success": True, 
                "earned": earned, 
                "level_up": True, 
                "new_level": level + 1,
                "reward": reward
            }
        
        self.save_data()
        return {"success": True, "earned": earned, "level_up": False}

    # ============================================================
    # متدهای هاپو
    # ============================================================

    def get_hapo_total_level(self):
        hapo_rank = self._to_int(self.data["hapo_rank"])
        hapo_level = self._to_int(self.data["hapo_level"])
        return hapo_rank * 5 + hapo_level

    def get_hapo_max_food(self):
        hapo_rank = self._to_int(self.data["hapo_rank"])
        return (hapo_rank + 1) * 4

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
        current_rank = self._to_int(self.data["hapo_rank"])
        if current_rank >= 4:
            return float('inf')
        return RANK_UP_PRICES[current_rank] if current_rank < len(RANK_UP_PRICES) else float('inf')

    def get_hapo_food_status(self):
        max_food = self.get_hapo_max_food()
        hapo_food = self._to_int(self.data["hapo_food"])
        if hapo_food == 0:
            return {"text": "دیگه کار نمیکنم", "speed": 0}
        if hapo_food / max_food < 0.25:
            return {"text": "من گشنمه", "speed": 0.5}
        if hapo_food / max_food < 0.75:
            return {"text": "شکمم پره", "speed": 1.0}
        return {"text": "عاشقتم", "speed": 1.5}

    def update_hapo_production(self):
        now = datetime.now().timestamp()
        
        hapo_last_update = self._to_float(self.data["hapo_last_update"])
        elapsed = now - hapo_last_update
        
        MAX_ELAPSED = 24 * 3600
        if elapsed > MAX_ELAPSED:
            elapsed = MAX_ELAPSED
        
        capacity = self.get_hapo_capacity()
        status = self.get_hapo_food_status()
        
        hapo_food = self._to_int(self.data["hapo_food"])
        hapo_harvest = self._to_int(self.data["hapo_harvest"])
        
        if hapo_food > 0 and hapo_harvest < capacity:
            gained = self.get_hapo_production() * status["speed"] * elapsed
            self.data["hapo_harvest"] = self._to_str(min(capacity, hapo_harvest + gained))
        
        if hapo_food > 0:
            decay = int((elapsed / (12 * 3600)) * 6)
            if decay > 0:
                self.data["hapo_food"] = self._to_str(max(0, hapo_food - decay))
        
        self.data["hapo_last_update"] = self._to_str(now)
        self.save_data()

    def buy_hapo(self):
        if self._to_int(self.data["level"]) < 3:
            return {"success": False, "reason": "سطح 3 لازم است"}
        
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < 300:
            return {"success": False, "reason": "300 هاپو پوینت لازم است"}
        if self.data["hapo_owned"]:
            return {"success": False, "reason": "شما قبلاً هاپو دارید"}
        
        self.data["hop_point"] = self._to_str(hop_point - 300)
        self.data["hapo_owned"] = True
        self.data["hapo_name"] = random.choice(HAPO_NAMES)
        self.data["hapo_rank"] = "0"
        self.data["hapo_level"] = "1"
        self.data["hapo_food"] = self._to_str(self.get_hapo_max_food())
        self.data["hapo_harvest"] = "0"
        self.data["hapo_last_update"] = self._to_str(datetime.now().timestamp())
        self.save_data()
        return {"success": True, "name": self.data["hapo_name"]}

    def can_rank_up(self):
        hapo_level = self._to_int(self.data["hapo_level"])
        hapo_rank = self._to_int(self.data["hapo_rank"])
        if hapo_level < 5:
            return {"success": False, "reason": "هاپو باید سطح 5 باشد تا بتواند مقام خود را ارتقا دهد"}
        if hapo_rank >= 4:
            return {"success": False, "reason": "هاپو در بالاترین مقام قرار دارد"}
        return {"success": True}

    def confirm_rank_up(self):
        hapo_rank = self._to_int(self.data["hapo_rank"])
        if hapo_rank >= 4:
            return {"success": False, "reason": "هاپو در بالاترین مقام قرار دارد"}
        
        price = self.get_hapo_rank_up_price()
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < price:
            return {"success": False, "reason": f"به {price:,} هاپو پوینت نیاز داری"}
        
        self.data["hop_point"] = self._to_str(hop_point - price)
        self.data["hapo_rank"] = self._to_str(hapo_rank + 1)
        self.data["hapo_level"] = "1"
        self.data["hapo_food"] = self._to_str(self.get_hapo_max_food())
        self.data["hapo_harvest"] = "0"
        self.data["hapo_last_update"] = self._to_str(datetime.now().timestamp())
        self.save_data()
        
        return {
            "success": True, 
            "new_rank": self._to_int(self.data["hapo_rank"]),
            "new_rank_name": RANK_NAMES[self._to_int(self.data["hapo_rank"])]
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
        if self._to_int(self.data["level"]) < 2:
            return {"success": False, "reason": "سطح 2 لازم است"}
        if self._to_int(self.data["claw_level"]) >= 1:
            return {"success": False, "reason": "شما قبلاً پنجه دارید"}
        
        cost = self.get_claw_cost(1)
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < cost:
            return {"success": False, "reason": f"{cost} هاپو پوینت لازم است"}
        
        self.data["hop_point"] = self._to_str(hop_point - cost)
        self.data["claw_level"] = "1"
        self.save_data()
        return {"success": True}

    def upgrade_claw(self):
        current = self._to_int(self.data["claw_level"])
        if current >= MAX_CLAW_LEVEL:
            return {"success": False, "reason": "پنجه در بالاترین سطح است"}
        
        next_level = current + 1
        cost = self.get_claw_cost(next_level)
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < cost:
            return {"success": False, "reason": f"{cost} هاپو پوینت لازم است"}
        
        self.data["hop_point"] = self._to_str(hop_point - cost)
        self.data["claw_level"] = self._to_str(next_level)
        self.save_data()
        return {"success": True, "new_level": next_level}

    def get_random_animal(self):
        if self._to_int(self.data["claw_level"]) == 0:
            return None
        
        claw_data = self.get_claw_data(self._to_int(self.data["claw_level"]))
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
        if self._to_int(self.data["level"]) < 2:
            return {"success": False, "reason": "سطح 2 لازم است"}
        if self._to_int(self.data["claw_level"]) == 0:
            return {"success": False, "reason": "شما پنجه ندارید"}
        if self.data.get("hunt_active", False):
            return {"success": False, "reason": "در حال شکار هستید"}
        
        if self.data.get("current_hunt_animal") and self._to_float(self.data.get("hunt_time", 0)) > 0:
            now = datetime.now().timestamp()
            hunt_time = self._to_float(self.data["hunt_time"])
            elapsed = now - hunt_time
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
                self.data["hunt_time"] = "0"
                self.save_data()
                return {"success": False, "reason": f"🦌 {animal_name} فرار کرد! وقتت تموم شد."}
        
        cooldown = self.get_claw_cooldown(self._to_int(self.data["claw_level"])) * 60
        now = datetime.now().timestamp()
        last_hunt_time = self._to_float(self.data["last_hunt_time"])
        
        if last_hunt_time > 0 and (now - last_hunt_time) < cooldown:
            remaining = cooldown - (now - last_hunt_time)
            return {"success": False, "reason": "خسته‌ام", "remaining": remaining}
        
        self.data["last_hunt_time"] = self._to_str(now)
        self.data["hunt_active"] = True
        self.save_data()
        
        animal = self.get_random_animal()
        if not animal:
            self.data["hunt_active"] = False
            self.save_data()
            return {"success": False, "reason": "خطا در شکار"}
        
        self.data["hunt_active"] = False
        self.data["current_hunt_animal"] = animal
        self.data["hunt_time"] = self._to_str(datetime.now().timestamp())
        self.save_data()
        return {"success": True, "animal": animal}

    def sell_animal(self):
        animal = self.data.get("current_hunt_animal")
        if not animal:
            return {"success": False, "reason": "هیچ حیوانی برای فروش وجود ندارد"}
        
        if self._to_float(self.data.get("hunt_time", 0)) > 0:
            now = datetime.now().timestamp()
            hunt_time = self._to_float(self.data["hunt_time"])
            if (now - hunt_time) > HUNT_DECISION_TIMER:
                animal_name = animal.get("name", "حیوان")
                self.data["current_hunt_animal"] = None
                self.data["hunt_time"] = "0"
                self.save_data()
                return {"success": False, "reason": f"🦌 {animal_name} فرار کرد! وقتت تموم شد."}
        
        value = animal["value"]
        hop_point = self._to_int(self.data["hop_point"])
        self.data["hop_point"] = self._to_str(hop_point + value)
        self.data["current_hunt_animal"] = None
        self.data["hunt_time"] = "0"
        self.save_data()
        return {"success": True, "value": value}

    def feed_hapo(self):
        animal = self.data.get("current_hunt_animal")
        if not animal:
            return {"success": False, "reason": "هیچ حیوانی برای غذا دادن وجود ندارد"}
        if not self.data["hapo_owned"]:
            return {"success": False, "reason": "شما هاپو ندارید"}
        
        if self._to_float(self.data.get("hunt_time", 0)) > 0:
            now = datetime.now().timestamp()
            hunt_time = self._to_float(self.data["hunt_time"])
            if (now - hunt_time) > HUNT_DECISION_TIMER:
                animal_name = animal.get("name", "حیوان")
                self.data["current_hunt_animal"] = None
                self.data["hunt_time"] = "0"
                self.save_data()
                return {"success": False, "reason": f"🦌 {animal_name} فرار کرد! وقتت تموم شد."}
        
        max_food = self.get_hapo_max_food()
        hapo_food = self._to_int(self.data["hapo_food"])
        if hapo_food >= max_food:
            return {"success": False, "reason": "هاپو سیر است"}
        
        nutrition = animal["nutrition"]
        new_food = min(max_food, hapo_food + nutrition)
        actual = new_food - hapo_food
        self.data["hapo_food"] = self._to_str(new_food)
        self.data["current_hunt_animal"] = None
        self.data["hunt_time"] = "0"
        self.save_data()
        return {"success": True, "fed": actual}

    # ============================================================
    # متدهای بانک
    # ============================================================

    def generate_card_number(self):
        import random
        from database import is_card_unique
        
        for _ in range(100):
            first = str(random.randint(1000, 9999))
            second = str(random.randint(1000, 9999))
            third = str(random.randint(1000, 9999))
            fourth = str(random.randint(1000, 9999))
            card = first + second + third + fourth
            if is_card_unique(card):
                return card
        
        import time
        return str(int(time.time() * 1000))[:16].zfill(16)

    def open_bank(self):
        if self._to_int(self.data["level"]) < BANK_REQUIRED_LEVEL:
            return {"success": False, "reason": f"سطح {BANK_REQUIRED_LEVEL} لازم است"}
        if self.data["bank_opened"]:
            return {"success": False, "reason": "بانک قبلاً باز شده است"}
        
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < BANK_PURCHASE_COST:
            return {"success": False, "reason": f"{BANK_PURCHASE_COST} هاپو پوینت لازم است"}
        
        self.data["hop_point"] = self._to_str(hop_point - BANK_PURCHASE_COST)
        self.data["bank_opened"] = True
        self.data["bank_balance"] = "0"
        self.data["bank_last_interest_at"] = self._to_str(datetime.now().timestamp())
        self.data["bank_card_number"] = self.generate_card_number()
        self.data["bank_transactions"] = []
        self.save_data()
        
        self.add_bank_transaction("افتتاح حساب", 0, f"شماره کارت: {self.data['bank_card_number']}")
        
        return {"success": True, "card_number": self.data["bank_card_number"]}

    def add_bank_transaction(self, type, amount, detail=""):
        transactions = self.data.get("bank_transactions", [])
        now = datetime.now()
        transaction = {
            "type": type,
            "amount": amount,
            "detail": detail,
            "date": now.strftime("%H:%M %Y/%m/%d")
        }
        transactions.insert(0, transaction)
        self.data["bank_transactions"] = transactions[:3]
        self.save_data()

    def apply_bank_interest(self):
        if not self.data["bank_opened"]:
            return
        
        now = datetime.now().timestamp()
        
        if self._to_float(self.data["bank_last_interest_at"]) == 0:
            self.data["bank_last_interest_at"] = self._to_str(now)
            self.save_data()
            return
        
        bank_last_interest_at = self._to_float(self.data["bank_last_interest_at"])
        elapsed = now - bank_last_interest_at
        
        if elapsed >= 24 * 3600:
            bank_balance = self._to_int(self.data["bank_balance"])
            interest = min(int(bank_balance * BANK_INTEREST_RATE), BANK_MAX_DAILY_INTEREST)
            if interest > 0:
                self.data["bank_balance"] = self._to_str(bank_balance + interest)
                self.add_bank_transaction("سود بانکی", interest, f"سود روزانه {int(BANK_INTEREST_RATE*100)}%")
            
            self.data["bank_last_interest_at"] = self._to_str(now)
            self.save_data()
            return
        
        return

    def get_next_interest_time(self):
        from datetime import timedelta
        last_time = self._to_float(self.data.get("bank_last_interest_at", 0))
        if last_time == 0:
            return datetime.now()
        next_time = datetime.fromtimestamp(last_time) + timedelta(days=1)
        return next_time

    def deposit(self, amount):
        if not self.data["bank_opened"]:
            return {"success": False, "reason": "بانک باز نشده است"}
        
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < amount:
            return {"success": False, "reason": "موجودی قابل استفاده کافی نیست"}
        if amount <= 0:
            return {"success": False, "reason": "مبلغ نامعتبر است"}
        
        self.data["hop_point"] = self._to_str(hop_point - amount)
        bank_balance = self._to_int(self.data["bank_balance"])
        self.data["bank_balance"] = self._to_str(bank_balance + amount)
        
        self.add_bank_transaction("واریز به حساب بانکی", amount, f"واریز {amount:,}")
        self.save_data()
        return {"success": True, "new_balance": self._to_int(self.data["bank_balance"])}

    def withdraw(self, amount):
        if not self.data["bank_opened"]:
            return {"success": False, "reason": "بانک باز نشده است"}
        
        bank_balance = self._to_int(self.data["bank_balance"])
        if bank_balance < amount:
            return {"success": False, "reason": "موجودی بانک کافی نیست"}
        if amount <= 0:
            return {"success": False, "reason": "مبلغ نامعتبر است"}
        
        self.data["bank_balance"] = self._to_str(bank_balance - amount)
        hop_point = self._to_int(self.data["hop_point"])
        self.data["hop_point"] = self._to_str(hop_point + amount)
        
        self.add_bank_transaction("برداشت از حساب بانکی", -amount, f"برداشت {amount:,}")
        self.save_data()
        return {"success": True, "new_balance": self._to_int(self.data["bank_balance"])}

    def change_card_number(self):
        if not self.data["bank_opened"]:
            return {"success": False, "reason": "بانک باز نشده است"}
        
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < BANK_ACCOUNT_CHANGE_COST:
            return {"success": False, "reason": f"به {BANK_ACCOUNT_CHANGE_COST:,} هاپو پوینت نیاز داری"}
        
        self.data["hop_point"] = self._to_str(hop_point - BANK_ACCOUNT_CHANGE_COST)
        old_card = self.data["bank_card_number"]
        self.data["bank_card_number"] = self.generate_card_number()
        self.add_bank_transaction("تغییر شماره حساب", -BANK_ACCOUNT_CHANGE_COST, f"شماره جدید: {self.data['bank_card_number']}")
        self.save_data()
        return {
            "success": True, 
            "old_card": old_card, 
            "new_card": self.data["bank_card_number"]
        }

    def card_to_card(self, amount, target_card):
        if not self.data["bank_opened"]:
            return {"success": False, "reason": "بانک باز نشده است"}
        
        bank_balance = self._to_int(self.data["bank_balance"])
        if bank_balance < amount:
            return {"success": False, "reason": "موجودی بانک کافی نیست"}
        if amount <= 0:
            return {"success": False, "reason": "مبلغ نامعتبر است"}
        if len(target_card) != 16 or not target_card.isdigit():
            return {"success": False, "reason": "❌ شماره کارت باید ۱۶ رقم باشد"}
        if target_card == self.data["bank_card_number"]:
            return {"success": False, "reason": "❌ نمی‌تونی به کارت خودت انتقال بدی"}
        
        from database import get_user_by_card
        target_user = get_user_by_card(target_card)
        if not target_user:
            return {"success": False, "reason": "❌ کارت مقصد در سیستم ثبت نشده است"}
        if str(target_user['user_id']) == self.user_id:
            return {"success": False, "reason": "❌ نمی‌تونی به کارت خودت انتقال بدی"}
        
        self.data["bank_balance"] = self._to_str(bank_balance - amount)
        
        target_user_id = target_user['user_id']
        target_game = HopDogGame(int(target_user_id))
        
        target_bank_balance = self._to_int(target_game.data["bank_balance"])
        target_game.data["bank_balance"] = self._to_str(target_bank_balance + amount)
        target_game.add_bank_transaction("دریافت کارت به کارت", amount, f"از {self.data['bank_card_number']}")
        target_game.save_data()
        
        self.add_bank_transaction("کارت به کارت هاپویی", -amount, f"به {target_card}")
        self.save_data()
        
        return {
            "success": True, 
            "amount": amount, 
            "target_card": target_card,
            "target_name": target_user.get('player_name', 'کاربر')
        }

    def get_bank_transactions(self):
        return self.data.get("bank_transactions", [])

    # ============================================================
    # متدهای انتقال هاپویی
    # ============================================================

    def can_transfer(self):
        if self.data.get("is_transferring", False):
            return {"success": False, "reason": "⏳ شما در حال حاضر در حال انتقال هستید. لطفاً صبر کنید."}
        if self._to_int(self.data["level"]) < TRANSFER_MIN_LEVEL_SENDER:
            return {"success": False, "reason": f"برای انتقال هاپو پوینت باید سطح {TRANSFER_MIN_LEVEL_SENDER} باشی"}
        if self.data.get("profile_locked", False):
            return {"success": False, "reason": "پروفایل شما قفل است. ابتدا آن را باز کن"}
        
        now = datetime.now().timestamp()
        last_transfer = self._to_float(self.data.get("last_transfer_time", 0))
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
        
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < amount:
            return {"success": False, "reason": f"موجودی کافی نیست. شما {hop_point:,} هاپو پوینت داری"}
        
        target_game = HopDogGame(int(target_user_id))
        target_data = target_game.data
        
        if self._to_int(target_data["level"]) < TRANSFER_MIN_LEVEL_RECEIVER:
            return {"success": False, "reason": f"کاربر مقصد باید حداقل سطح {TRANSFER_MIN_LEVEL_RECEIVER} داشته باشد"}
        if target_data.get("profile_locked", False):
            return {"success": False, "reason": "پروفایل کاربر مقصد قفل است"}
        
        self.data["is_transferring"] = True
        target_game.data["is_transferring"] = True
        self.save_data()
        target_game.save_data()
        
        try:
            self.data["hop_point"] = self._to_str(hop_point - amount)
            
            target_hop_point = self._to_int(target_game.data["hop_point"])
            target_game.data["hop_point"] = self._to_str(target_hop_point + amount)
            
            self.data["last_transfer_time"] = self._to_str(datetime.now().timestamp())
            
            self.save_data()
            target_game.save_data()
            
            return {
                "success": True, 
                "amount": amount, 
                "target_name": target_data["player_name"],
                "target_id": target_user_id
            }
        finally:
            self.data["is_transferring"] = False
            target_game.data["is_transferring"] = False
            self.save_data()
            target_game.save_data()

    # ============================================================
    # متدهای زندان
    # ============================================================

    def is_jailed(self):
        if not self.data.get("jailed", False):
            return False
        now = datetime.now().timestamp()
        jail_until = self._to_float(self.data.get("jail_until", 0))
        if now >= jail_until:
            self.data["jailed"] = False
            self.data["jail_reason"] = ""
            self.data["jail_until"] = "0"
            self.data["jail_fine"] = "0"
            self.data["jail_arrest_time"] = "0"
            self.data["jail_admin_id"] = None
            self.save_data()
            return False
        return True

    def get_jail_remaining(self):
        if not self.data.get("jailed", False):
            return 0
        now = datetime.now().timestamp()
        jail_until = self._to_float(self.data.get("jail_until", 0))
        remaining = jail_until - now
        return max(0, int(remaining))

    def jail_user(self, reason, duration, fine):
        now = datetime.now().timestamp()
        self.data["jailed"] = True
        self.data["jail_reason"] = reason
        self.data["jail_until"] = self._to_str(now + duration)
        self.data["jail_fine"] = self._to_str(fine)
        self.data["jail_arrest_time"] = self._to_str(now)
        self.data["jail_admin_id"] = None
        self.save_data()
        return {"success": True}

    def jail_user_with_admin(self, reason, duration, fine, admin_id):
        now = datetime.now().timestamp()
        self.data["jailed"] = True
        self.data["jail_reason"] = reason
        self.data["jail_until"] = self._to_str(now + duration)
        self.data["jail_fine"] = self._to_str(fine)
        self.data["jail_arrest_time"] = self._to_str(now)
        self.data["jail_admin_id"] = admin_id
        self.save_data()
        return {"success": True}

    def pay_jail_fine(self):
        if not self.data.get("jailed", False):
            return {"success": False, "reason": "شما در زندان نیستید"}
        
        fine = self._to_int(self.data.get("jail_fine", 0))
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < fine:
            return {"success": False, "reason": f"پوینت کافی نیست. نیاز به {fine:,} هاپو پوینت"}
        
        self.data["hop_point"] = self._to_str(hop_point - fine)
        self.data["jailed"] = False
        self.data["jail_reason"] = ""
        self.data["jail_until"] = "0"
        self.data["jail_fine"] = "0"
        self.data["jail_arrest_time"] = "0"
        self.data["jail_admin_id"] = None
        self.save_data()
        return {"success": True}

    def get_jail_info(self):
        if not self.data.get("jailed", False):
            return None
        
        remaining = self.get_jail_remaining()
        if remaining <= 0:
            self.data["jailed"] = False
            self.save_data()
            return None
        
        return {
            "reason": self.data.get("jail_reason", "نامشخص"),
            "remaining": remaining,
            "fine": self._to_int(self.data.get("jail_fine", 0)),
            "arrest_time": self._to_float(self.data.get("jail_arrest_time", 0)),
            "admin_id": self.data.get("jail_admin_id", None)
        }

    def add_meow_vote(self, voter_id):
        votes = self.data.get("jail_voted", [])
        if voter_id not in votes:
            votes.append(voter_id)
            self.data["jail_voted"] = votes
            self.save_data()
            return True
        return False

    def get_meow_votes(self):
        return self.data.get("jail_voted", [])


# ================================================================
# کلاس هاپوی خیابونی
# ================================================================

class StreetHapo:
    """مدیریت هاپوی خیابونی"""
    
    def __init__(self, context=None):
        self.context = context
        self.active = False
        self.data = {}
        self.load_status()
    
    def load_status(self):
        from database import get_street_hapo_status
        status = get_street_hapo_status()
        self.active = status.get("active", False)
        self.data = status.get("data", {})
        
        if "attempts" not in self.data:
            self.data["attempts"] = 0
        if "failed_attempts" not in self.data:
            self.data["failed_attempts"] = []
        if "rescued" not in self.data:
            self.data["rescued"] = False
        if "status" not in self.data:
            self.data["status"] = "waiting"
    
    def save_status(self):
        from database import set_street_hapo_status
        return set_street_hapo_status(self.active, self.data)
    
    def start_event(self, chat_id):
        if self.active:
            return False, "هم اکنون یک هاپوی خیابونی در حال نجات است!"
        
        self.active = True
        self.data = {
            "chat_id": chat_id,
            "started_at": datetime.now().timestamp(),
            "expires_at": datetime.now().timestamp() + STREET_HAPO_DECISION_TIME,
            "attempts": 0,
            "rescued": False,
            "failed_attempts": [],
            "rescued_by": None,
            "rescued_by_name": None,
            "reward": 0,
            "message_id": None,
            "status": "waiting"
        }
        self.save_status()
        return True, "هاپوی خیابونی پیدا شد!"
    
    def is_expired(self):
        if not self.active:
            return True
        if self.data.get("rescued", False):
            return False
        now = datetime.now().timestamp()
        expires_at = self.data.get("expires_at", 0)
        return now >= expires_at
    
    def get_attempt_cost(self):
        attempts = self.data.get("attempts", 0)
        if attempts >= STREET_HAPO_MAX_ATTEMPTS:
            return None
        return STREET_HAPO_COSTS[attempts]
    
    def get_remaining_time(self):
        if not self.active or self.data.get("rescued", False):
            return 0
        now = datetime.now().timestamp()
        expires_at = self.data.get("expires_at", 0)
        remaining = expires_at - now
        return max(0, int(remaining))
    
    def _to_int(self, value):
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value))
            except:
                return 0
        return 0
    
    def attempt_rescue(self, user_id, user_name, game):
        if not self.active:
            return {"success": False, "reason": "هیچ هاپوی خیابونی در دسترس نیست!"}
        
        if self.data.get("rescued", False):
            return {"success": False, "reason": "این هاپوی خیابونی قبلاً نجات پیدا کرده!"}
        
        if self.is_expired():
            self.active = False
            self.save_status()
            return {"success": False, "reason": "⏰ هاپوی خیابونی فرار کرد!"}
        
        attempts = self.data.get("attempts", 0)
        if attempts >= STREET_HAPO_MAX_ATTEMPTS:
            return {"success": False, "reason": "همه شانس‌ها از دست رفته!"}
        
        cost = STREET_HAPO_COSTS[attempts]
        hop_point = game._to_int(game.data["hop_point"])
        if hop_point < cost:
            return {"success": False, "reason": f"پوینت کافی نیست! نیاز به {cost} 🪙"}
        
        game.data["hop_point"] = game._to_str(hop_point - cost)
        game.save_data()
        
        current_attempt = attempts + 1
        self.data["attempts"] = current_attempt
        
        if "failed_attempts" not in self.data:
            self.data["failed_attempts"] = []
        
        self.data["failed_attempts"].append({
            "user_id": user_id,
            "user_name": user_name,
            "attempt": current_attempt,
            "cost": cost,
            "time": datetime.now().timestamp(),
            "success": False
        })
        
        if random.random() < STREET_HAPO_SUCCESS_CHANCE:
            reward = random.randint(STREET_HAPO_REWARD_MIN, STREET_HAPO_REWARD_MAX)
            self.data["rescued"] = True
            self.data["rescued_by"] = user_id
            self.data["rescued_by_name"] = user_name
            self.data["reward"] = reward
            self.data["status"] = "rescued"
            
            if self.data["failed_attempts"]:
                self.data["failed_attempts"][-1]["success"] = True
            
            game.data["hop_point"] = game._to_str(game._to_int(game.data["hop_point"]) + reward)
            
            street_rescued = game._to_int(game.data.get("street_hapo_rescued", 0))
            game.data["street_hapo_rescued"] = game._to_str(street_rescued + 1)
            
            game.save_data()
            
            self.active = False
            self.save_status()
            
            return {
                "success": True,
                "rescued": True,
                "reward": reward,
                "attempt": current_attempt,
                "cost": cost,
                "message": f"🎉 {user_name} هاپوی خیابونی رو نجات داد و {reward} 🪙 جایزه گرفت!"
            }
        else:
            fail_msg = random.choice(STREET_HAPO_FAIL_MESSAGES).format(name=user_name)
            
            if current_attempt >= STREET_HAPO_MAX_ATTEMPTS:
                self.data["status"] = "died"
                self.active = False
                self.save_status()
                return {
                    "success": False,
                    "rescued": False,
                    "died": True,
                    "message": f"💀 {fail_msg}\n\nهاپوی خیابونی مرد... 😢",
                    "attempt": current_attempt,
                    "cost": cost,
                    "remaining_attempts": 0
                }
            
            self.save_status()
            return {
                "success": False,
                "rescued": False,
                "died": False,
                "message": fail_msg,
                "attempt": current_attempt,
                "cost": cost,
                "remaining_attempts": STREET_HAPO_MAX_ATTEMPTS - current_attempt
            }
    
    def get_status_text(self):
        if not self.active:
            if self.data.get("rescued", False):
                return f"🎉 هاپوی خیابونی توسط {self.data.get('rescued_by_name', 'نامشخص')} نجات پیدا کرد!"
            elif self.data.get("status") == "died":
                return "💀 هاپوی خیابونی مرد... 😢"
            elif self.data.get("status") == "expired":
                return "⏰ هاپوی خیابونی فرار کرد!"
            else:
                return "🐶 هیچ هاپوی خیابونی در دسترس نیست."
        
        if self.is_expired():
            self.active = False
            self.save_status()
            return "⏰ هاپوی خیابونی فرار کرد!"
        
        remaining = self.get_remaining_time()
        attempts = self.data.get("attempts", 0)
        cost = self.get_attempt_cost()
        
        msg = f"🐶 یک هاپوی خیابونی پیدا شده!\n\n"
        msg += f"⏳ زمان باقی‌مونده: {remaining} ثانیه\n"
        msg += f"🔄 تلاش‌های انجام شده: {attempts}/{STREET_HAPO_MAX_ATTEMPTS}\n"
        if cost is not None:
            msg += f"💰 هزینه تلاش بعدی: {cost} 🪙\n"
        else:
            msg += f"❌ همه شانس‌ها از دست رفته!\n"
        
        msg += f"\n🍀 شانس موفقیت: {int(STREET_HAPO_SUCCESS_CHANCE * 100)}%\n"
        msg += f"🎁 جایزه: {STREET_HAPO_REWARD_MIN} تا {STREET_HAPO_REWARD_MAX} 🪙"
        
        return msg
