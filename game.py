# game.py - کلاس اصلی بازی (توابع پایه)

import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union

from config import *
from database import get_user_data, save_user_data, get_user_by_card, is_card_unique

logger = logging.getLogger(__name__)


class HopDogGame:
    def __init__(self, user_id, username=""):
        self.user_id = str(user_id)
        self.username = username
        self.data = self.load_data()
        if not self.data:
            self.reset_data()

    # ============================================================
    # توابع کمکی تبدیل
    # ============================================================

    def _to_int(self, value) -> int:
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

    def _to_float(self, value) -> float:
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

    def _to_str(self, value) -> str:
        if value is None:
            return "0"
        return str(value)

    def _to_bool(self, value) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["true", "1", "yes", "on"]
        return bool(value)

    # ============================================================
    # متدهای اصلی بارگذاری و ذخیره
    # ============================================================

    def load_data(self):
        try:
            data = get_user_data(self.user_id)
            if data:
                # تبدیل فیلدهای JSON
                if "current_hunt_animal" in data and data["current_hunt_animal"]:
                    try:
                        data["current_hunt_animal"] = json.loads(data["current_hunt_animal"])
                    except:
                        data["current_hunt_animal"] = None
                else:
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
                
                if "fridge_items" in data and data["fridge_items"]:
                    try:
                        if isinstance(data["fridge_items"], str):
                            data["fridge_items"] = json.loads(data["fridge_items"])
                        elif not isinstance(data["fridge_items"], list):
                            data["fridge_items"] = []
                    except:
                        data["fridge_items"] = []
                else:
                    data["fridge_items"] = []
                
                # فیلدهای پیش‌فرض
                defaults = {
                    "bank_card_number": "",
                    "jail_admin_id": None,
                    "hunt_time": "0",
                    "is_transferring": False,
                    "profile_hidden": False,
                    "profile_locked": False,
                    "street_hapo_rescued": "0",
                    "fridge_owned": False,
                    "fridge_level": "1",
                    "smuggling": False,
                    "smuggle_count": "0",
                    "smuggle_start": "0",
                    "smuggle_duration": "0",
                    "smuggle_success_chance": "0",
                    "smuggle_used_hapo": "0",
                    "total_hunts": "0",
                    "last_transfer_time": "0",
                    "_hapo_stopped_message": False
                }
                for key, default in defaults.items():
                    if key not in data:
                        data[key] = default
                
                # چک خودکار آزادی از زندان
                if data.get("jailed", False):
                    now = datetime.now().timestamp()
                    jail_until = self._to_float(data.get("jail_until", 0))
                    if now >= jail_until and jail_until > 0:
                        data["jailed"] = False
                        data["jail_reason"] = ""
                        data["jail_until"] = "0"
                        data["jail_fine"] = "0"
                        data["jail_arrest_time"] = "0"
                        data["jail_admin_id"] = None
                        save_user_data(self.user_id, data)
                return data
            return None
        except Exception as e:
            logger.error(f"Error loading data: {e}")
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
            "fridge_owned": False,
            "fridge_level": "1",
            "fridge_items": [],
            "smuggling": False,
            "smuggle_count": "0",
            "smuggle_start": "0",
            "smuggle_duration": "0",
            "smuggle_success_chance": "0",
            "smuggle_used_hapo": "0",
            "total_hunts": "0",
            "_hapo_stopped_message": False,
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
            new_level = level + 1
            self.data["level"] = self._to_str(new_level)
            reward = self.get_level_data(new_level)["reward"]
            hop_point = self._to_int(self.data["hop_point"])
            self.data["hop_point"] = self._to_str(hop_point + reward)
            self.save_data()
            
            return {
                "success": True, 
                "earned": earned, 
                "level_up": True, 
                "new_level": new_level,
                "reward": reward,
                "old_level": level,
                "features": self.get_level_data(new_level)["features"],
                "hop_point": self._to_int(self.data["hop_point"])
            }
        
        self.save_data()
        return {
            "success": True, 
            "earned": earned, 
            "level_up": False,
            "hop_point": self._to_int(self.data["hop_point"])
        }

    # ============================================================
    # متدهای بانک
    # ============================================================

    def generate_card_number(self):
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
        """اعمال سود بانکی برای روزهای گذشته (حداکثر ۳۰ روز)"""
        if not self.data["bank_opened"]:
            return
        
        now = datetime.now().timestamp()
        last_time = self._to_float(self.data.get("bank_last_interest_at", 0))
        
        if last_time == 0:
            self.data["bank_last_interest_at"] = self._to_str(now)
            self.save_data()
            return
        
        elapsed = now - last_time
        days_passed = int(elapsed // (24 * 3600))
        
        if days_passed > 30:
            days_passed = 30
            self.data["bank_last_interest_at"] = self._to_str(now - 30 * 24 * 3600)
        
        if days_passed > 0:
            bank_balance = self._to_int(self.data["bank_balance"])
            
            for _ in range(days_passed):
                interest = min(
                    int(bank_balance * BANK_INTEREST_RATE),
                    BANK_MAX_DAILY_INTEREST
                )
                if interest > 0:
                    bank_balance += interest
                    self.add_bank_transaction(
                        "سود بانکی", 
                        interest, 
                        f"سود روزانه {int(BANK_INTEREST_RATE*100)}%"
                    )
            
            self.data["bank_balance"] = self._to_str(bank_balance)
            self.data["bank_last_interest_at"] = self._to_str(now)
            self.save_data()
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
            return {
                "success": False, 
                "reason": "⏳ شما در حال حاضر در حال انتقال هستید. لطفاً صبر کنید."
            }
        if self._to_int(self.data["level"]) < TRANSFER_MIN_LEVEL_SENDER:
            return {
                "success": False, 
                "reason": f"❌ برای انتقال هاپو پوینت باید سطح {TRANSFER_MIN_LEVEL_SENDER} باشی"
            }
        if self.data.get("profile_locked", False):
            return {
                "success": False, 
                "reason": "🔒 پروفایل شما قفل است. ابتدا آن را باز کن"
            }
        now = datetime.now().timestamp()
        last_transfer = self._to_float(self.data.get("last_transfer_time", 0))
        if last_transfer > 0 and (now - last_transfer) < TRANSFER_COOLDOWN:
            remaining = TRANSFER_COOLDOWN - (now - last_transfer)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            return {
                "success": False, 
                "reason": f"⏳ *به جیبت استراحت بده!*\n\n💤 {minutes} دقیقه و {seconds} ثانیه دیگه میتونی انتقال بدی"
            }
        return {"success": True}

    def transfer_points(self, target_user_id, amount):
        can = self.can_transfer()
        if not can["success"]:
            return can
        if amount < TRANSFER_MIN_AMOUNT:
            return {"success": False, "reason": f"❌ حداقل مبلغ انتقال {TRANSFER_MIN_AMOUNT} هاپو پوینت است"}
        if amount > TRANSFER_MAX_AMOUNT:
            return {"success": False, "reason": f"❌ حداکثر مبلغ انتقال {TRANSFER_MAX_AMOUNT:,} هاپو پوینت است"}
        hop_point = self._to_int(self.data["hop_point"])
        if hop_point < amount:
            return {"success": False, "reason": f"❌ موجودی کافی نیست. شما {hop_point:,} هاپو پوینت داری"}
        target_game = HopDogGame(int(target_user_id))
        target_data = target_game.data
        if self._to_int(target_data["level"]) < TRANSFER_MIN_LEVEL_RECEIVER:
            return {"success": False, "reason": f"❌ کاربر مقصد باید حداقل سطح {TRANSFER_MIN_LEVEL_RECEIVER} داشته باشد"}
        if target_data.get("profile_locked", False):
            return {"success": False, "reason": "🔒 پروفایل کاربر مقصد قفل است"}
        
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
        if now >= jail_until and jail_until > 0:
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
            return {"success": False, "reason": f"پوینت کافی نیست. نیاز به {fine:,} هاپو پوینت داری و {hop_point:,} داری"}
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
        if str(voter_id) not in votes:
            votes.append(str(voter_id))
            self.data["jail_voted"] = votes
            self.save_data()
            return True
        return False

    def get_meow_votes(self):
        return self.data.get("jail_voted", [])
