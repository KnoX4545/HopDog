# database.py - نسخه اصلاح شده با رفع مشکلات تبدیل داده

import json
import logging
from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================================================
# توابع اصلی کاربر
# ================================================================

def get_user_data(user_id):
    try:
        response = supabase.table("users").select("*").eq("user_id", str(user_id)).execute()
        if response.data and len(response.data) > 0:
            data = response.data[0]
            
            # تبدیل JSON فیلدها با try/except
            json_fields = [
                "current_hunt_animal", 
                "bank_transactions", 
                "jail_voted", 
                "fridge_items"
            ]
            
            for field in json_fields:
                if field in data and data[field]:
                    try:
                        if isinstance(data[field], str):
                            data[field] = json.loads(data[field])
                        # اگر قبلاً دیکشنری یا لیست بود، همان را نگه دار
                    except:
                        if field in ["bank_transactions", "jail_voted", "fridge_items"]:
                            data[field] = []
                        else:
                            data[field] = None
                elif field in ["bank_transactions", "jail_voted", "fridge_items"]:
                    data[field] = []
            
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
                "total_hunts": "0"
            }
            
            for key, default in defaults.items():
                if key not in data:
                    data[key] = default
            
            # چک کردن خودکار آزادی از زندان
            if data.get("jailed", False):
                now = datetime.now().timestamp()
                try:
                    jail_until = float(data.get("jail_until", 0))
                except:
                    jail_until = 0
                
                if now >= jail_until and jail_until > 0:
                    data["jailed"] = False
                    data["jail_reason"] = ""
                    data["jail_until"] = "0"
                    data["jail_fine"] = "0"
                    data["jail_arrest_time"] = "0"
                    data["jail_admin_id"] = None
                    save_user_data(user_id, data)
            
            return data
        return None
    except Exception as e:
        logging.error(f"Error loading data for {user_id}: {e}")
        return None


def save_user_data(user_id, data):
    try:
        data_to_save = {**data}
        
        # حذف فیلدهای اضافی
        if "created_at" in data_to_save:
            del data_to_save["created_at"]
        if "last_updated" in data_to_save:
            del data_to_save["last_updated"]
        
        # تبدیل JSON فیلدها به string
        json_fields = ["current_hunt_animal", "bank_transactions", "jail_voted", "fridge_items"]
        for field in json_fields:
            if field in data_to_save:
                if data_to_save[field] is None:
                    if field == "current_hunt_animal":
                        data_to_save[field] = None
                    else:
                        data_to_save[field] = "[]"
                elif isinstance(data_to_save[field], (dict, list)):
                    data_to_save[field] = json.dumps(data_to_save[field])
                elif isinstance(data_to_save[field], str):
                    # اگر قبلاً string بود، همان را نگه دار
                    pass
                else:
                    if field == "current_hunt_animal":
                        data_to_save[field] = None
                    else:
                        data_to_save[field] = "[]"
        
        # ======== تبدیل همه اعداد به String ========
        string_fields = [
            "hop_point", "last_hop_time", "level", "hop_count",
            "claw_level", "last_hunt_time", "hunt_time",
            "hapo_rank", "hapo_level", "hapo_food", "hapo_harvest", "hapo_last_update",
            "bank_balance", "bank_last_interest_at",
            "street_hapo_rescued",
            "jail_until", "jail_fine", "jail_arrest_time",
            "fridge_level", "smuggle_count", "smuggle_start", 
            "smuggle_duration", "smuggle_success_chance", "smuggle_used_hapo",
            "total_hunts", "last_transfer_time"
        ]
        
        for field in string_fields:
            if field in data_to_save and data_to_save[field] is not None:
                if not isinstance(data_to_save[field], str):
                    data_to_save[field] = str(data_to_save[field])
        
        # ======== تبدیل boolean ها ========
        bool_fields = [
            "is_admin", "hunt_active", "hapo_owned", "bank_opened", 
            "has_seen_welcome", "profile_hidden", "profile_locked", 
            "is_transferring", "jailed", "fridge_owned", "smuggling"
        ]
        
        for field in bool_fields:
            if field in data_to_save:
                if isinstance(data_to_save[field], bool):
                    pass
                elif isinstance(data_to_save[field], str):
                    data_to_save[field] = data_to_save[field].lower() == "true"
                else:
                    data_to_save[field] = bool(data_to_save[field])
        
        # ======== اضافه کردن زمان ========
        data_to_save["last_updated"] = datetime.now().isoformat()
        data_to_save["user_id"] = str(user_id)
        
        logging.info(f"💾 Saving user {user_id}")
        
        response = supabase.table("users").upsert(data_to_save).execute()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error saving user {user_id}: {e}")
        return False


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


def get_user_by_card(card_number):
    try:
        response = supabase.table("users").select("*").eq("bank_card_number", card_number).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logging.error(f"Error getting user by card: {e}")
        return None


def is_card_unique(card_number):
    try:
        response = supabase.table("users").select("user_id").eq("bank_card_number", card_number).execute()
        return len(response.data) == 0
    except Exception as e:
        logging.error(f"Error checking card uniqueness: {e}")
        return False


# ================================================================
# توابع گروه
# ================================================================

def add_group(chat_id, title):
    try:
        supabase.table("groups").upsert({
            "chat_id": str(chat_id),
            "title": title,
            "added_at": datetime.now().isoformat(),
            "is_active": True,
            "last_activity": datetime.now().isoformat(),
            "total_hops": "0",
            "total_hapo_points": "0",
            "total_hunts": "0",
            "member_count": "0"
        }).execute()
        return True
    except Exception as e:
        logging.error(f"Error adding group: {e}")
        return False


def get_all_groups():
    try:
        response = supabase.table("groups").select("chat_id").eq("is_active", True).execute()
        if response.data:
            return [row["chat_id"] for row in response.data]
        return []
    except Exception as e:
        logging.error(f"Error getting groups: {e}")
        return []


def update_group_activity(chat_id):
    try:
        supabase.table("groups").update({
            "last_activity": datetime.now().isoformat()
        }).eq("chat_id", str(chat_id)).execute()
        return True
    except Exception as e:
        logging.error(f"Error updating group activity: {e}")
        return False


def remove_group(chat_id):
    try:
        supabase.table("groups").update({
            "is_active": False
        }).eq("chat_id", str(chat_id)).execute()
        return True
    except Exception as e:
        logging.error(f"Error removing group: {e}")
        return False


# ================================================================
# توابع هاپوی خیابونی
# ================================================================

def reset_street_hapo_global():
    try:
        supabase.table("settings").upsert({
            "key": "street_hapo_active",
            "value": "false",
            "data": {},
            "updated_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        logging.error(f"Error resetting street hapo: {e}")
        return False


def get_street_hapo_status():
    try:
        response = supabase.table("settings").select("*").eq("key", "street_hapo_active").execute()
        if response.data and len(response.data) > 0:
            data = response.data[0]
            # تبدیل data به دیکشنری اگر string باشه
            data_value = data.get("data", {})
            if isinstance(data_value, str):
                try:
                    data_value = json.loads(data_value)
                except:
                    data_value = {}
            return {
                "active": data.get("value") == "true",
                "data": data_value
            }
        return {"active": False, "data": {}}
    except Exception as e:
        logging.error(f"Error getting street hapo status: {e}")
        return {"active": False, "data": {}}


def set_street_hapo_status(active, data=None):
    try:
        supabase.table("settings").upsert({
            "key": "street_hapo_active",
            "value": "true" if active else "false",
            "data": data or {},
            "updated_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        logging.error(f"Error setting street hapo status: {e}")
        return False
