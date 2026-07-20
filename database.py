# database.py - عملیات دیتابیس Supabase

import json
import logging
from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_data(user_id):
    """دریافت اطلاعات کاربر از دیتابیس"""
    try:
        response = supabase.table("users").select("*").eq("user_id", str(user_id)).execute()
        if response.data and len(response.data) > 0:
            data = response.data[0]
            # تبدیل فیلدهای JSON
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
            return data
        return None
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return None

def save_user_data(user_id, data):
    """ذخیره اطلاعات کاربر در دیتابیس"""
    try:
        data_to_save = {**data}
        if "current_hunt_animal" in data_to_save and data_to_save["current_hunt_animal"]:
            data_to_save["current_hunt_animal"] = json.dumps(data_to_save["current_hunt_animal"])
        if "bank_transactions" in data_to_save and data_to_save["bank_transactions"]:
            data_to_save["bank_transactions"] = json.dumps(data_to_save["bank_transactions"])
        if "created_at" in data_to_save:
            del data_to_save["created_at"]
        data_to_save["last_updated"] = datetime.now().isoformat()
        
        supabase.table("users").upsert(data_to_save).execute()
        return True
    except Exception as e:
        logging.error(f"Error saving data: {e}")
        return False

def get_user_by_identifier(identifier):
    """دریافت اطلاعات کاربر با شناسه (آیدی عددی یا یوزرنیم)"""
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
    """دریافت اطلاعات کاربر با شماره کارت"""
    try:
        response = supabase.table("users").select("*").eq("bank_card_number", card_number).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logging.error(f"Error getting user by card: {e}")
        return None
