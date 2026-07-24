# game_hapo_extras.py - توابع هاپو، پنجه، شکار، یخچال، قاچاق

import random
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from config import *
from game import HopDogGame

logger = logging.getLogger(__name__)


# ============================================================
# متدهای هاپو (اضافه به کلاس HopDogGame)
# ============================================================

def get_hapo_total_level(self):
    hapo_rank = self._to_int(self.data["hapo_rank"])
    hapo_level = self._to_int(self.data["hapo_level"])
    return hapo_rank * 5 + hapo_level


def get_hapo_max_level_for_rank(self, rank):
    return (rank + 1) * 5


def get_hapo_max_food(self):
    hapo_rank = self._to_int(self.data["hapo_rank"])
    return (hapo_rank + 1) * 4


def get_hapo_capacity(self):
    total = self.get_hapo_total_level()
    if total in HAPO_CAPACITY:
        return HAPO_CAPACITY[total]
    keys = sorted(HAPO_CAPACITY.keys())
    for k in keys:
        if k >= total:
            return HAPO_CAPACITY[k]
    return HAPO_CAPACITY[keys[-1]]


def get_hapo_production(self):
    total = self.get_hapo_total_level()
    if total in HAPO_PRODUCTION:
        return HAPO_PRODUCTION[total]
    keys = sorted(HAPO_PRODUCTION.keys())
    for k in keys:
        if k >= total:
            return HAPO_PRODUCTION[k]
    return HAPO_PRODUCTION[keys[-1]]


def get_hapo_upgrade_price(self):
    total = self.get_hapo_total_level()
    if total >= 20:
        return float('inf')
    next_level = total + 1
    if next_level in HAPO_LEVEL_PRICES:
        return HAPO_LEVEL_PRICES[next_level]
    keys = sorted(HAPO_LEVEL_PRICES.keys())
    for k in keys:
        if k >= next_level:
            return HAPO_LEVEL_PRICES[k]
    return HAPO_LEVEL_PRICES[keys[-1]]


def get_hapo_rank_up_price(self):
    current_rank = self._to_int(self.data["hapo_rank"])
    if current_rank >= 4:
        return float('inf')
    return RANK_UP_PRICES[current_rank] if current_rank < len(RANK_UP_PRICES) else float('inf')


def get_hapo_food_status(self):
    """دریافت وضعیت غذا - اگر ۰ باشد «کار نمیکنم» نمایش داده می‌شود"""
    max_food = self.get_hapo_max_food()
    hapo_food = self._to_int(self.data["hapo_food"])
    
    if hapo_food == 0:
        return {"text": "😢 کار نمیکنم...", "speed": 0}
    if hapo_food / max_food < 0.25:
        return {"text": "🍽️ من گشنمه!", "speed": 0.5}
    if hapo_food / max_food < 0.75:
        return {"text": "😋 شکمم پره", "speed": 1.0}
    return {"text": "❤️ عاشقتم!", "speed": 1.5}


def update_hapo_production(self):
    """به‌روزرسانی تولید هاپو - اگر غذا ۰ باشد تولید متوقف می‌شود"""
    now = datetime.now().timestamp()
    hapo_last_update = self._to_float(self.data["hapo_last_update"])
    elapsed = now - hapo_last_update
    MAX_ELAPSED = 24 * 3600
    if elapsed > MAX_ELAPSED:
        elapsed = MAX_ELAPSED
    
    capacity = self.get_hapo_capacity()
    hapo_food = self._to_int(self.data["hapo_food"])
    hapo_harvest = self._to_int(self.data["hapo_harvest"])
    
    if hapo_food > 0 and hapo_harvest < capacity:
        status = self.get_hapo_food_status()
        gained = self.get_hapo_production() * status["speed"] * elapsed
        self.data["hapo_harvest"] = self._to_str(min(capacity, hapo_harvest + gained))
    
    if hapo_food > 0:
        decay = int((elapsed / (12 * 3600)) * 6)
        if decay > 0:
            new_food = max(0, hapo_food - decay)
            if new_food == 0 and hapo_food > 0:
                self.data["_hapo_stopped_message"] = True
            self.data["hapo_food"] = self._to_str(new_food)
    
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
    name = random.choice(HAPO_NAMES)
    self.data["hapo_name"] = name.strip()
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
    if hapo_rank >= 4:
        return {"success": False, "reason": "هاپو در بالاترین مقام قرار دارد"}
    max_level = self.get_hapo_max_level_for_rank(hapo_rank)
    if hapo_level < max_level:
        return {"success": False, "reason": f"هاپو باید به سطح {max_level} برسد تا بتواند مقام خود را ارتقا دهد"}
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
    
    new_rank = self._to_int(self.data["hapo_rank"])
    new_max_level = self.get_hapo_max_level_for_rank(new_rank)
    return {
        "success": True,
        "new_rank": new_rank,
        "new_rank_name": RANK_NAMES[new_rank],
        "new_max_level": new_max_level
    }


def can_upgrade_level(self):
    hapo_rank = self._to_int(self.data["hapo_rank"])
    hapo_level = self._to_int(self.data["hapo_level"])
    total = self.get_hapo_total_level()
    if total >= 20:
        return {"success": False, "reason": "هاپو در بالاترین سطح است"}
    max_level = self.get_hapo_max_level_for_rank(hapo_rank)
    if hapo_level >= max_level:
        return {"success": False, "reason": f"هاپو به سطح {max_level} رسیده. برای ادامه باید مقام خود را ارتقا دهد"}
    return {"success": True}


def upgrade_hapo_level(self):
    total = self.get_hapo_total_level()
    hapo_rank = self._to_int(self.data["hapo_rank"])
    hapo_level = self._to_int(self.data["hapo_level"])
    if total >= 20:
        return {"success": False, "reason": "هاپو در بالاترین سطح است"}
    max_level = self.get_hapo_max_level_for_rank(hapo_rank)
    if hapo_level >= max_level:
        return {"success": False, "reason": f"هاپو به سطح {max_level} رسیده. برای ادامه باید مقام خود را ارتقا دهد"}
    price = self.get_hapo_upgrade_price()
    hop_point = self._to_int(self.data["hop_point"])
    if hop_point < price:
        return {"success": False, "reason": f"به {price:,} هاپو پوینت نیاز داری"}
    
    self.data["hop_point"] = self._to_str(hop_point - price)
    self.data["hapo_level"] = self._to_str(hapo_level + 1)
    hapo_food = self._to_int(self.data["hapo_food"])
    max_food = self.get_hapo_max_food()
    self.data["hapo_food"] = self._to_str(min(max_food, hapo_food + 2))
    self.save_data()
    
    new_level = self._to_int(self.data["hapo_level"])
    return {
        "success": True,
        "new_level": new_level,
        "max_level": self.get_hapo_max_level_for_rank(hapo_rank)
    }


def feed_hapo(self):
    """تغذیه هاپو با حیوان شکار شده"""
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
            return {"success": False, "reason": f"🦌 {animal_name} فرار کرد!"}
    
    max_food = self.get_hapo_max_food()
    hapo_food = self._to_int(self.data["hapo_food"])
    
    if hapo_food >= max_food:
        return {"success": False, "reason": "هاپو سیر است"}
    
    nutrition = animal["nutrition"]
    new_food = min(max_food, hapo_food + nutrition)
    actual = new_food - hapo_food
    
    self.data["hapo_food"] = self._to_str(new_food)
    if hapo_food == 0 and new_food > 0:
        self.data["_hapo_stopped_message"] = False
    self.data["current_hunt_animal"] = None
    self.data["hunt_time"] = "0"
    self.save_data()
    
    return {
        "success": True, 
        "fed": actual,
        "new_food": new_food,
        "max_food": max_food
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
    
    total_hunts = self._to_int(self.data.get("total_hunts", 0))
    self.data["total_hunts"] = self._to_str(total_hunts + 1)
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


# ============================================================
# متدهای یخچال هاپویی
# ============================================================

def get_fridge_items(self):
    items = self.data.get("fridge_items", [])
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except:
            items = []
    if not isinstance(items, list):
        items = []
    return items


def save_fridge_items(self, items):
    if not isinstance(items, list):
        items = []
    self.data["fridge_items"] = items
    self.save_data()
    return True


def get_fridge_capacity(self):
    level = self._to_int(self.data.get("fridge_level", 1))
    return FRIDGE_CAPACITY.get(level, 1)


def get_fridge_upgrade_cost(self):
    level = self._to_int(self.data.get("fridge_level", 1))
    next_level = level + 1
    if next_level > FRIDGE_MAX_LEVEL:
        return None
    return FRIDGE_UPGRADE_COSTS.get(next_level, None)


def buy_fridge(self):
    if self._to_int(self.data["level"]) < FRIDGE_REQUIRED_LEVEL:
        return {"success": False, "reason": f"یخچال هاپویی از سطح {FRIDGE_REQUIRED_LEVEL} باز میشود"}
    if self.data.get("fridge_owned", False):
        return {"success": False, "reason": "شما قبلاً یخچال هاپویی دارید"}
    hop_point = self._to_int(self.data.get("hop_point", 0))
    if hop_point < FRIDGE_PURCHASE_COST:
        return {"success": False, "reason": f"برای خرید یخچال به {FRIDGE_PURCHASE_COST:,} هاپو پوینت نیاز داری"}
    self.data["hop_point"] = self._to_str(hop_point - FRIDGE_PURCHASE_COST)
    self.data["fridge_owned"] = True
    self.data["fridge_level"] = "1"
    self.data["fridge_items"] = []
    self.save_data()
    return {"success": True}


def upgrade_fridge(self):
    if not self.data.get("fridge_owned", False):
        return {"success": False, "reason": "شما یخچال هاپویی ندارید"}
    current_level = self._to_int(self.data.get("fridge_level", 1))
    if current_level >= FRIDGE_MAX_LEVEL:
        return {"success": False, "reason": "یخچال شما در بالاترین سطح است"}
    cost = FRIDGE_UPGRADE_COSTS.get(current_level + 1)
    if cost is None:
        return {"success": False, "reason": "خطا در محاسبه هزینه"}
    hop_point = self._to_int(self.data.get("hop_point", 0))
    if hop_point < cost:
        return {"success": False, "reason": f"برای ارتقا به {cost:,} هاپو پوینت نیاز داری"}
    self.data["hop_point"] = self._to_str(hop_point - cost)
    self.data["fridge_level"] = self._to_str(current_level + 1)
    self.save_data()
    return {"success": True, "new_level": current_level + 1}


def add_to_fridge(self, animal):
    if not self.data.get("fridge_owned", False):
        return {"success": False, "reason": "شما یخچال هاپویی ندارید"}
    if not animal:
        return {"success": False, "reason": "هیچ حیوانی برای ذخیره وجود ندارد"}
    items = self.get_fridge_items()
    capacity = self.get_fridge_capacity()
    if len(items) >= capacity:
        return {"success": False, "reason": f"یخچال پر است! ظرفیت: {capacity}"}
    
    animal_name = animal.get("name")
    for item in items:
        if item.get("name") == animal_name:
            return {"success": False, "reason": f"شما قبلاً یک {animal_name} در یخچال دارید"}
    
    animal_copy = animal.copy()
    animal_copy["cooked"] = False
    animal_copy["cooking"] = False
    items.append(animal_copy)
    self.save_fridge_items(items)
    return {"success": True, "item": animal_copy}


def remove_from_fridge(self, index):
    items = self.get_fridge_items()
    if index < 0 or index >= len(items):
        return {"success": False, "reason": "حیوان مورد نظر یافت نشد"}
    removed = items.pop(index)
    self.save_fridge_items(items)
    return {"success": True, "item": removed}


def cook_item(self, index):
    from datetime import datetime
    items = self.get_fridge_items()
    if index < 0 or index >= len(items):
        return {"success": False, "reason": "حیوان مورد نظر یافت نشد"}
    item = items[index]
    if item.get("cooked", False):
        return {"success": False, "reason": "این حیوان قبلاً پخته شده است"}
    if item.get("cooking", False):
        return {"success": False, "reason": "این حیوان در حال پخت است"}
    weight = item.get("weight", 1.0)
    cook_time = int(weight * 100)
    cook_time = max(30, cook_time)
    item["cooking"] = True
    item["cook_time"] = cook_time
    item["cook_start"] = datetime.now().timestamp()
    self.save_fridge_items(items)
    logger.info(f"🔥 شروع پخت {item['name']} - زمان: {cook_time} ثانیه")
    return {
        "success": True,
        "cook_time": cook_time,
        "item": item
    }


def check_cooking_status(self):
    from datetime import datetime
    items = self.get_fridge_items()
    now = datetime.now().timestamp()
    changed = False
    for item in items:
        if item.get("cooking", False):
            cook_start = item.get("cook_start", 0)
            cook_time = item.get("cook_time", 0)
            elapsed = now - cook_start
            if elapsed >= cook_time:
                item["cooked"] = True
                item["cooking"] = False
                item["original_value"] = item.get("value", 0)
                item["original_nutrition"] = item.get("nutrition", 1)
                item["value"] = int(item["value"] * FRIDGE_COOK_MULTIPLIER_SELL)
                item["nutrition"] = item["nutrition"] * FRIDGE_COOK_MULTIPLIER_FOOD
                changed = True
                logger.info(f"✅ پخت {item['name']} کامل شد")
    if changed:
        self.save_fridge_items(items)
    return items


def get_fridge_item_cook_progress(self, index):
    from datetime import datetime
    items = self.get_fridge_items()
    if index < 0 or index >= len(items):
        return None
    item = items[index]
    if not item.get("cooking", False):
        return None
    now = datetime.now().timestamp()
    cook_start = item.get("cook_start", 0)
    cook_time = item.get("cook_time", 0)
    elapsed = now - cook_start
    progress = min(100, int((elapsed / cook_time) * 100))
    remaining = max(0, int(cook_time - elapsed))
    return {
        "progress": progress,
        "remaining": remaining,
        "total": cook_time
    }


def sell_from_fridge(self, index):
    if not self.data.get("fridge_owned", False):
        return {"success": False, "reason": "شما یخچال هاپویی ندارید"}
    items = self.get_fridge_items()
    if index < 0 or index >= len(items):
        return {"success": False, "reason": "حیوان مورد نظر یافت نشد"}
    item = items[index]
    if item.get("cooking", False):
        return {"success": False, "reason": "این حیوان در حال پخت است"}
    value = item.get("value", 0)
    hop_point = self._to_int(self.data.get("hop_point", 0))
    self.data["hop_point"] = self._to_str(hop_point + value)
    removed = items.pop(index)
    self.save_fridge_items(items)
    return {
        "success": True,
        "value": value,
        "item": removed
    }


def feed_hapo_from_fridge(self, index):
    """تغذیه هاپو از یخچال"""
    if not self.data.get("fridge_owned", False):
        return {"success": False, "reason": "شما یخچال هاپویی ندارید"}
    
    if not self.data.get("hapo_owned", False):
        return {"success": False, "reason": "شما هاپو ندارید"}
    
    items = self.get_fridge_items()
    if index < 0 or index >= len(items):
        return {"success": False, "reason": "حیوان مورد نظر یافت نشد"}
    
    item = items[index]
    if item.get("cooking", False):
        return {"success": False, "reason": "این حیوان در حال پخت است"}
    
    nutrition = item.get("nutrition", 1)
    
    max_food = self.get_hapo_max_food()
    hapo_food = self._to_int(self.data.get("hapo_food", 0))
    
    if hapo_food >= max_food:
        return {"success": False, "reason": "هاپو سیر است"}
    
    new_food = min(max_food, hapo_food + nutrition)
    actual = new_food - hapo_food
    
    self.data["hapo_food"] = self._to_str(new_food)
    if hapo_food == 0 and new_food > 0:
        self.data["_hapo_stopped_message"] = False
    
    removed = items.pop(index)
    self.save_fridge_items(items)
    self.save_data()
    
    logger.info(f"🍖 تغذیه هاپو از یخچال: {removed['name']} - {actual} کالری")
    
    return {
        "success": True,
        "fed": actual,
        "item": removed,
        "new_food": new_food,
        "max_food": max_food,
        "old_food": hapo_food
    }


# ============================================================
# متدهای قاچاق هاپویی
# ============================================================

def start_smuggle(self, count):
    from datetime import datetime
    import random
    
    level = self._to_int(self.data.get("level", 1))
    if level < SMUGGLE_REQUIRED_LEVEL:
        return {"success": False, "reason": f"قاچاق هاپویی از سطح {SMUGGLE_REQUIRED_LEVEL} باز میشود"}
    street_hapo = self._to_int(self.data.get("street_hapo_rescued", 0))
    if street_hapo < SMUGGLE_MIN_HAPO:
        return {"success": False, "reason": f"برای قاچاق به حداقل {SMUGGLE_MIN_HAPO} هاپوی خیابونی نیاز داری. شما {street_hapo} داری"}
    if count < SMUGGLE_MIN_HAPO or count > SMUGGLE_MAX_HAPO:
        return {"success": False, "reason": f"تعداد هاپوها باید بین {SMUGGLE_MIN_HAPO} تا {SMUGGLE_MAX_HAPO} باشد"}
    if count > street_hapo:
        return {"success": False, "reason": f"شما فقط {street_hapo} هاپوی خیابونی داری"}
    if self.data.get("smuggling", False):
        return {"success": False, "reason": "شما در حال حاضر در حال قاچاق هستید"}
    cook_time = count * SMUGGLE_TIME_PER_HAPO
    success_chance = SMUGGLE_SUCCESS_CHANCE - (count - SMUGGLE_MIN_HAPO) * 0.02
    success_chance = max(0.30, success_chance)
    now = datetime.now().timestamp()
    self.data["smuggling"] = True
    self.data["smuggle_count"] = str(count)
    self.data["smuggle_start"] = str(now)
    self.data["smuggle_duration"] = str(cook_time)
    self.data["smuggle_success_chance"] = str(success_chance)
    self.data["smuggle_used_hapo"] = str(count)
    self.data["street_hapo_rescued"] = self._to_str(street_hapo - count)
    self.save_data()
    return {
        "success": True,
        "count": count,
        "duration": cook_time,
        "success_chance": int(success_chance * 100)
    }


def check_smuggle_status(self):
    from config import SMUGGLE_JAIL_DURATION, SMUGGLE_JAIL_FINE, SMUGGLE_REWARD_MIN, SMUGGLE_REWARD_MAX
    from datetime import datetime
    import random
    
    if not self.data.get("smuggling", False):
        return None
    now = datetime.now().timestamp()
    start = self.data.get("smuggle_start", 0)
    duration = self.data.get("smuggle_duration", 0)
    if isinstance(start, str):
        try:
            start = float(start)
        except:
            start = 0
    if isinstance(duration, str):
        try:
            duration = float(duration)
        except:
            duration = 0
    elapsed = now - start
    if elapsed < duration:
        remaining = int(duration - elapsed)
        return {
            "status": "in_progress",
            "remaining": remaining,
            "progress": int((elapsed / duration) * 100) if duration > 0 else 0,
            "count": self._to_int(self.data.get("smuggle_count", 0))
        }
    success_chance = self.data.get("smuggle_success_chance", 0.60)
    if isinstance(success_chance, str):
        try:
            success_chance = float(success_chance)
        except:
            success_chance = 0.60
    count = self._to_int(self.data.get("smuggle_count", 0))
    self.data["smuggling"] = False
    self.data["smuggle_count"] = "0"
    self.data["smuggle_start"] = "0"
    self.data["smuggle_duration"] = "0"
    self.data["smuggle_success_chance"] = "0"
    if random.random() < success_chance:
        reward_per_hapo = random.randint(SMUGGLE_REWARD_MIN, SMUGGLE_REWARD_MAX)
        total_reward = reward_per_hapo * count
        hop_point = self._to_int(self.data.get("hop_point", 0))
        self.data["hop_point"] = self._to_str(hop_point + total_reward)
        self.save_data()
        return {
            "status": "success",
            "count": count,
            "reward": total_reward,
            "per_hapo": reward_per_hapo
        }
    else:
        self.jail_user(JAIL_REASON_SMUGGLE, SMUGGLE_JAIL_DURATION, SMUGGLE_JAIL_FINE)
        self.save_data()
        return {
            "status": "failed",
            "count": count,
            "jail_duration": SMUGGLE_JAIL_DURATION // 60,
            "jail_fine": SMUGGLE_JAIL_FINE
        }


def get_smuggle_info(self):
    from datetime import datetime
    if not self.data.get("smuggling", False):
        return None
    now = datetime.now().timestamp()
    start = self.data.get("smuggle_start", 0)
    duration = self.data.get("smuggle_duration", 0)
    if isinstance(start, str):
        try:
            start = float(start)
        except:
            start = 0
    if isinstance(duration, str):
        try:
            duration = float(duration)
        except:
            duration = 0
    elapsed = now - start
    remaining = int(duration - elapsed)
    return {
        "count": self._to_int(self.data.get("smuggle_count", 0)),
        "remaining": remaining,
        "progress": int((elapsed / duration) * 100) if duration > 0 else 0
    }


# ============================================================
# اضافه کردن متدها به کلاس HopDogGame
# ============================================================

# متدهای هاپو
HopDogGame.get_hapo_total_level = get_hapo_total_level
HopDogGame.get_hapo_max_level_for_rank = get_hapo_max_level_for_rank
HopDogGame.get_hapo_max_food = get_hapo_max_food
HopDogGame.get_hapo_capacity = get_hapo_capacity
HopDogGame.get_hapo_production = get_hapo_production
HopDogGame.get_hapo_upgrade_price = get_hapo_upgrade_price
HopDogGame.get_hapo_rank_up_price = get_hapo_rank_up_price
HopDogGame.get_hapo_food_status = get_hapo_food_status
HopDogGame.update_hapo_production = update_hapo_production
HopDogGame.buy_hapo = buy_hapo
HopDogGame.can_rank_up = can_rank_up
HopDogGame.confirm_rank_up = confirm_rank_up
HopDogGame.can_upgrade_level = can_upgrade_level
HopDogGame.upgrade_hapo_level = upgrade_hapo_level
HopDogGame.feed_hapo = feed_hapo

# متدهای پنجه و شکار
HopDogGame.get_claw_data = get_claw_data
HopDogGame.get_claw_cost = get_claw_cost
HopDogGame.get_claw_cooldown = get_claw_cooldown
HopDogGame.buy_claw = buy_claw
HopDogGame.upgrade_claw = upgrade_claw
HopDogGame.get_random_animal = get_random_animal
HopDogGame.do_hunt = do_hunt
HopDogGame.sell_animal = sell_animal

# متدهای یخچال
HopDogGame.get_fridge_items = get_fridge_items
HopDogGame.save_fridge_items = save_fridge_items
HopDogGame.get_fridge_capacity = get_fridge_capacity
HopDogGame.get_fridge_upgrade_cost = get_fridge_upgrade_cost
HopDogGame.buy_fridge = buy_fridge
HopDogGame.upgrade_fridge = upgrade_fridge
HopDogGame.add_to_fridge = add_to_fridge
HopDogGame.remove_from_fridge = remove_from_fridge
HopDogGame.cook_item = cook_item
HopDogGame.check_cooking_status = check_cooking_status
HopDogGame.get_fridge_item_cook_progress = get_fridge_item_cook_progress
HopDogGame.sell_from_fridge = sell_from_fridge
HopDogGame.feed_hapo_from_fridge = feed_hapo_from_fridge

# متدهای قاچاق
HopDogGame.start_smuggle = start_smuggle
HopDogGame.check_smuggle_status = check_smuggle_status
HopDogGame.get_smuggle_info = get_smuggle_info
