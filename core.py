# core.py - منطق اصلی بازی

import random
import json
from datetime import datetime
from data import *

class HopDogGame:
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self.load_data()
        if not self.data:
            self.reset_data()

    def reset_data(self):
        self.data = {
            "player_name": "",
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
            "bank_last_interest_amount": 0,
            "waiting_for_name": True,
        }
        self.save_data()

    def load_data(self):
        try:
            with open(f"data/{self.user_id}.json", "r") as f:
                return json.load(f)
        except:
            return None

    def save_data(self):
        import os
        os.makedirs("data", exist_ok=True)
        with open(f"data/{self.user_id}.json", "w") as f:
            json.dump(self.data, f)

    # ----- سطح و هاپ -----
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
        
        # بررسی ارتقا سطح
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

    # ----- هاپو -----
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

    # ----- پنجه و شکار -----
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
        self.save_data()
        return {"success": True, "animal": animal}

    def sell_animal(self, value):
        self.data["hop_point"] += value
        self.save_data()
        return {"success": True, "new_balance": self.data["hop_point"]}

    def feed_hapo(self, nutrition):
        if not self.data["hapo_owned"]:
            return {"success": False, "reason": "شما هاپو ندارید"}
        
        max_food = self.get_hapo_max_food()
        if self.data["hapo_food"] >= max_food:
            return {"success": False, "reason": "هاپو سیر است"}
        
        new_food = min(max_food, int(self.data["hapo_food"] + nutrition))
        actual = new_food - int(self.data["hapo_food"])
        self.data["hapo_food"] = new_food
        self.save_data()
        return {"success": True, "fed": actual}

    # ----- بانک -----
    def apply_bank_interest(self):
        if not self.data["bank_opened"]:
            return
        
        now = datetime.now().timestamp()
        if self.data["bank_last_interest_at"] == 0:
            self.data["bank_last_interest_at"] = now
            return
        
        # محاسبه سود بر اساس موجودی فعلی
        interest = min(int(self.data["bank_balance"] * BANK_INTEREST_RATE), BANK_MAX_DAILY_INTEREST)
        if interest > 0:
            self.data["bank_balance"] += interest
            self.data["bank_last_interest_amount"] = interest
        
        self.data["bank_last_interest_at"] = now
        self.save_data()

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
