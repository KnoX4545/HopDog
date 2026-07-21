# database.py - نسخه نهایی با TEXT و فیلدهای جدید

import json
import logging
from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user_data(user_id):
    try:
        response = supabase.table("users").select("*").eq("user_id", str(user_id)).execute()
        if response.data and len(response.data) > 0:
            data = response.data[0]
            
            # تبدیل JSON فیلدها
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
            
            if "fridge_items" in data and data["fridge_items"]:
                try:
                    data["fridge_items"] = json.loads(data["fridge_items"])
                except:
                    data["fridge_items"] = []
            else:
                data["fridge_items"] = []
            
            # فیلدهای پیش‌فرض
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
            
            # فیلدهای یخچال
            if "fridge_owned" not in data:
                data["fridge_owned"] = False
            if "fridge_level" not in data:
                data["fridge_level"] = "1"
            
            # فیلدهای قاچاق
            if "smuggling" not in data:
                data["smuggling"] = False
            if "smuggle_count" not in data:
                data["smuggle_count"] = "0"
            if "smuggle_start" not in data:
                data["smuggle_start"] = "0"
            if "smuggle_duration" not in data:
                data["smuggle_duration"] = "0"
            if "smuggle_success_chance" not in data:
                data["smuggle_success_chance"] = "0"
            if "smuggle_used_hapo" not in data:
                data["smuggle_used_hapo"] = "0"
            
            # تبدیل String به عدد برای استفاده در کد
            if "hop_point" in data and isinstance(data["hop_point"], str):
                data["hop_point"] = int(float(data["hop_point"]))
            if "level" in data and isinstance(data["level"], str):
                data["level"] = int(data["level"])
            if "hop_count" in data and isinstance(data["hop_count"], str):
                data["hop_count"] = int(float(data["hop_count"]))
            if "last_hop_time" in data and isinstance(data["last_hop_time"], str):
                data["last_hop_time"] = float(data["last_hop_time"])
            
            # چک کردن زندان
            if data.get("jailed", False):
                now = datetime.now().timestamp()
                jail_until = float(data.get("jail_until", 0))
                if now >= jail_until:
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
        logging.error(f"Error loading data: {e}")
        return None


def save_user_data(user_id, data):
    try:
        data_to_save = {**data}
        
        # حذف فیلدهای اضافی
        if "created_at" in data_to_save:
            del data_to_save["created_at"]
        if "last_updated" in data_to_save:
            del data_to_save["last_updated"]
        
        # تبدیل JSON فیلدها
        if "current_hunt_animal" in data_to_save and data_to_save["current_hunt_animal"]:
            data_to_save["current_hunt_animal"] = json.dumps(data_to_save["current_hunt_animal"])
        else:
            data_to_save["current_hunt_animal"] = None
            
        if "bank_transactions" in data_to_save and data_to_save["bank_transactions"]:
            data_to_save["bank_transactions"] = json.dumps(data_to_save["bank_transactions"])
        else:
            data_to_save["bank_transactions"] = "[]"
            
        if "jail_voted" in data_to_save and data_to_save["jail_voted"]:
            data_to_save["jail_voted"] = json.dumps(data_to_save["jail_voted"])
        else:
            data_to_save["jail_voted"] = "[]"
        
        if "fridge_items" in data_to_save and data_to_save["fridge_items"]:
            data_to_save["fridge_items"] = json.dumps(data_to_save["fridge_items"])
        else:
            data_to_save["fridge_items"] = "[]"
        
        # ======== تبدیل همه اعداد به String ========
        string_fields = [
            "hop_point", "last_hop_time", "level", "hop_count",
            "claw_level", "last_hunt_time", "hunt_time",
            "hapo_rank", "hapo_level", "hapo_food", "hapo_harvest", "hapo_last_update",
            "bank_balance", "bank_last_interest_at",
            "street_hapo_rescued",
            "jail_until", "jail_fine", "jail_arrest_time",
            "fridge_level", "smuggle_count", "smuggle_start", 
            "smuggle_duration", "smuggle_success_chance", "smuggle_used_hapo"
        ]
        
        for field in string_fields:
            if field in data_to_save and data_to_save[field] is not None:
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
                    data_to_save[field] = data_to_save[field]
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
            "last_activity": datetime.now().isoformat()
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
