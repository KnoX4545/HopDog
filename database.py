# database.py - عملیات دیتابیس Supabase

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
