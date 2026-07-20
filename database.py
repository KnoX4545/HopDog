# database.py - عملیات دیتابیس Supabase (نسخه درست)

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
            # فیلدهای جدید
            if "bank_card_number" not in data:
                data["bank_card_number"] = ""
            if "jail_admin_id" not in data:
                data["jail_admin_id"] = None
            if "hunt_time" not in data:
                data["hunt_time"] = 0
            if "is_transferring" not in data:
                data["is_transferring"] = False
            if "profile_hidden" not in data:
                data["profile_hidden"] = False
            if "profile_locked" not in data:
                data["profile_locked"] = False
            if "street_hapo_rescued" not in data:
                data["street_hapo_rescued"] = 0
            # چک کردن خودکار آزادی
            if data.get("jailed", False):
                now = datetime.now().timestamp()
                if now >= data.get("jail_until", 0):
                    data["jailed"] = False
                    data["jail_reason"] = ""
                    data["jail_until"] = 0
                    data["jail_fine"] = 0
                    data["jail_arrest_time"] = 0
                    data["jail_admin_id"] = None
                    save_user_data(self.user_id, data)
            return data
        return None
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return None

def save_user_data(user_id, data):
    try:
        data_to_save = {**data}
        if "current_hunt_animal" in data_to_save and data_to_save["current_hunt_animal"]:
            data_to_save["current_hunt_animal"] = json.dumps(data_to_save["current_hunt_animal"])
        if "bank_transactions" in data_to_save and data_to_save["bank_transactions"]:
            data_to_save["bank_transactions"] = json.dumps(data_to_save["bank_transactions"])
        if "jail_voted" in data_to_save and data_to_save["jail_voted"]:
            data_to_save["jail_voted"] = json.dumps(data_to_save["jail_voted"])
        if "created_at" in data_to_save:
            del data_to_save["created_at"]
        data_to_save["last_updated"] = datetime.now().isoformat()
        
        supabase.table("users").upsert(data_to_save).execute()
        return True
    except Exception as e:
        logging.error(f"Error saving data: {e}")
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
            return {
                "active": data.get("value") == "true",
                "data": data.get("data", {})
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
