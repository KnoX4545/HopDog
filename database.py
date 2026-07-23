# database.py - نسخه کامل با اصلاحات جدید (Supabase)

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# ================================================================
# تنظیمات اولیه
# ================================================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ================================================================
# توابع کمکی داخلی
# ================================================================

def _parse_json_field(value, default=None):
    """تبدیل رشته JSON به دیکشنری یا لیست"""
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return default
    return default


def _to_json_string(value):
    """تبدیل دیکشنری یا لیست به رشته JSON"""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except:
        return str(value)


def _to_str(value, default="0"):
    """تبدیل هر نوع داده به رشته"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _to_int(value, default=0):
    """تبدیل هر نوع داده به عدد صحیح"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except:
            return default
    return default


def _to_bool(value, default=False):
    """تبدیل هر نوع داده به بولین"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ["true", "1", "yes", "on"]
    return bool(value)


# ================================================================
# توابع اصلی کاربر
# ================================================================

def get_user_data(user_id: Union[int, str]) -> Optional[Dict[str, Any]]:
    """
    دریافت اطلاعات کامل یک کاربر از دیتابیس
    
    Args:
        user_id: آیدی عددی کاربر
    
    Returns:
        Optional[Dict]: دیکشنری اطلاعات کاربر یا None اگر وجود نداشته باشد
    """
    try:
        user_id = str(user_id)
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            data = response.data[0]
            
            # ======== تبدیل فیلدهای JSON ========
            json_fields = [
                "current_hunt_animal", 
                "bank_transactions", 
                "jail_voted", 
                "fridge_items"
            ]
            
            for field in json_fields:
                if field in data:
                    data[field] = _parse_json_field(data[field], [] if field != "current_hunt_animal" else None)
                else:
                    if field == "fridge_items":
                        data[field] = []
                    elif field == "current_hunt_animal":
                        data[field] = None
                    else:
                        data[field] = []
            
            # ======== فیلدهای پیش‌فرض ========
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
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            for key, default in defaults.items():
                if key not in data:
                    data[key] = default
            
            # ======== چک خودکار آزادی از زندان ========
            if data.get("jailed", False):
                now = datetime.now().timestamp()
                jail_until = _to_float(data.get("jail_until", 0))
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
        logger.error(f"❌ خطا در دریافت اطلاعات کاربر {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def save_user_data(user_id: Union[int, str], data: Dict[str, Any]) -> bool:
    """
    ذخیره اطلاعات کاربر در دیتابیس
    
    Args:
        user_id: آیدی عددی کاربر
        data: دیکشنری اطلاعات کاربر
    
    Returns:
        bool: موفقیت‌آمیز بودن ذخیره‌سازی
    """
    try:
        user_id = str(user_id)
        data_to_save = {**data}
        
        # ======== حذف فیلدهای اضافی که نباید ذخیره بشن ========
        remove_fields = ["created_at", "last_updated"]
        for field in remove_fields:
            if field in data_to_save:
                del data_to_save[field]
        
        # ======== لیست فیلدهایی که باید به string تبدیل بشن ========
        string_fields = [
            "hop_point", "last_hop_time", "level", "hop_count",
            "claw_level", "last_hunt_time", "hunt_time",
            "hapo_rank", "hapo_level", "hapo_food", "hapo_harvest", "hapo_last_update",
            "bank_balance", "bank_last_interest_at",
            "street_hapo_rescued",
            "jail_until", "jail_fine", "jail_arrest_time",
            "fridge_level", "smuggle_count", "smuggle_start", 
            "smuggle_duration", "smuggle_success_chance", "smuggle_used_hapo",
            "total_hunts", "last_transfer_time",
            "bank_card_number", "hapo_name", "player_name"
        ]
        
        for field in string_fields:
            if field in data_to_save and data_to_save[field] is not None:
                if not isinstance(data_to_save[field], str):
                    data_to_save[field] = _to_str(data_to_save[field])
        
        # ======== تبدیل فیلدهای JSON به string ========
        json_fields = ["current_hunt_animal", "bank_transactions", "jail_voted", "fridge_items"]
        for field in json_fields:
            if field in data_to_save:
                if data_to_save[field] is None:
                    if field == "current_hunt_animal":
                        data_to_save[field] = None
                    else:
                        data_to_save[field] = "[]"
                elif isinstance(data_to_save[field], (dict, list)):
                    try:
                        data_to_save[field] = json.dumps(data_to_save[field], ensure_ascii=False)
                    except Exception as e:
                        logger.error(f"❌ خطا در تبدیل {field} به JSON: {e}")
                        if field == "current_hunt_animal":
                            data_to_save[field] = None
                        else:
                            data_to_save[field] = "[]"
                elif isinstance(data_to_save[field], str):
                    # اگه قبلاً string هست، بررسی کن که JSON معتبر هست یا نه
                    if field == "fridge_items" and data_to_save[field] == "":
                        data_to_save[field] = "[]"
                    elif field == "current_hunt_animal" and data_to_save[field] == "":
                        data_to_save[field] = None
                    elif field == "bank_transactions" and data_to_save[field] == "":
                        data_to_save[field] = "[]"
                    elif field == "jail_voted" and data_to_save[field] == "":
                        data_to_save[field] = "[]"
                else:
                    if field == "current_hunt_animal":
                        data_to_save[field] = None
                    else:
                        data_to_save[field] = "[]"
        
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
                    data_to_save[field] = data_to_save[field].lower() in ["true", "1", "yes", "on"]
                else:
                    data_to_save[field] = bool(data_to_save[field])
        
        # ======== اطمینان از وجود user_id ========
        data_to_save["user_id"] = user_id
        
        # ======== اضافه کردن زمان ========
        data_to_save["last_updated"] = datetime.now().isoformat()
        
        # ======== لاگ برای دیباگ ========
        logger.info(f"💾 ذخیره کاربر {user_id} - سطح: {data_to_save.get('level', '1')} - پوینت: {data_to_save.get('hop_point', '0')}")
        
        # ======== ذخیره در دیتابیس ========
        response = supabase.table("users").upsert(data_to_save).execute()
        
        logger.info(f"✅ کاربر {user_id} با موفقیت ذخیره شد")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره کاربر {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_user_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    """
    جستجوی کاربر بر اساس شناسه (آیدی عددی یا یوزرنیم)
    
    Args:
        identifier: آیدی عددی یا یوزرنیم (با یا بدون @)
    
    Returns:
        Optional[Dict]: اطلاعات کاربر یا None
    """
    try:
        identifier = identifier.strip()
        
        # ======== جستجو با آیدی عددی ========
        if identifier.isdigit():
            response = supabase.table("users").select("*").eq("user_id", identifier).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        # ======== جستجو با یوزرنیم ========
        username = identifier.replace("@", "").lower()
        
        # جستجوی مستقیم
        response = supabase.table("users").select("*").eq("player_name", username).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        # جستجو با @
        response = supabase.table("users").select("*").eq("player_name", f"@{username}").execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        # جستجوی جزئی (شامل)
        response = supabase.table("users").select("*").ilike("player_name", f"%{username}%").execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"❌ خطا در جستجوی کاربر {identifier}: {e}")
        return None


def get_user_by_card(card_number: str) -> Optional[Dict[str, Any]]:
    """
    جستجوی کاربر بر اساس شماره کارت بانکی
    
    Args:
        card_number: شماره کارت ۱۶ رقمی
    
    Returns:
        Optional[Dict]: اطلاعات کاربر یا None
    """
    try:
        response = supabase.table("users").select("*").eq("bank_card_number", card_number).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
        
    except Exception as e:
        logger.error(f"❌ خطا در جستجوی کاربر با کارت {card_number}: {e}")
        return None


def is_card_unique(card_number: str) -> bool:
    """
    بررسی یکتا بودن شماره کارت
    
    Args:
        card_number: شماره کارت ۱۶ رقمی
    
    Returns:
        bool: یکتا بودن یا نه
    """
    try:
        response = supabase.table("users").select("user_id").eq("bank_card_number", card_number).execute()
        return len(response.data) == 0
        
    except Exception as e:
        logger.error(f"❌ خطا در بررسی یکتا بودن کارت {card_number}: {e}")
        return False


def _to_float(value, default=0.0):
    """تبدیل هر نوع داده به عدد اعشاری"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except:
            return default
    return default


# ================================================================
# توابع گروه
# ================================================================

def add_group(chat_id: Union[int, str], title: str) -> bool:
    """
    افزودن گروه جدید به دیتابیس
    
    Args:
        chat_id: آیدی گروه
        title: عنوان گروه
    
    Returns:
        bool: موفقیت‌آمیز بودن افزودن
    """
    try:
        chat_id = str(chat_id)
        
        # بررسی وجود گروه
        response = supabase.table("groups").select("chat_id").eq("chat_id", chat_id).execute()
        
        if response.data and len(response.data) > 0:
            # گروه وجود دارد، فقط به‌روزرسانی کن
            supabase.table("groups").update({
                "title": title,
                "is_active": True,
                "last_activity": datetime.now().isoformat()
            }).eq("chat_id", chat_id).execute()
            logger.info(f"🔄 گروه {chat_id} به‌روزرسانی شد")
        else:
            # گروه جدید
            supabase.table("groups").upsert({
                "chat_id": chat_id,
                "title": title,
                "added_at": datetime.now().isoformat(),
                "is_active": True,
                "last_activity": datetime.now().isoformat(),
                "total_hops": "0",
                "total_hapo_points": "0",
                "total_hunts": "0",
                "member_count": "0"
            }).execute()
            logger.info(f"✅ گروه {chat_id} اضافه شد")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در افزودن گروه {chat_id}: {e}")
        return False


def get_all_groups() -> List[str]:
    """
    دریافت لیست همه گروه‌های فعال
    
    Returns:
        List[str]: لیست آیدی گروه‌ها
    """
    try:
        response = supabase.table("groups").select("chat_id").eq("is_active", True).execute()
        if response.data:
            return [row["chat_id"] for row in response.data]
        return []
        
    except Exception as e:
        logger.error(f"❌ خطا در دریافت لیست گروه‌ها: {e}")
        return []


def get_group_stats(chat_id: Union[int, str]) -> Optional[Dict[str, Any]]:
    """
    دریافت آمار یک گروه
    
    Args:
        chat_id: آیدی گروه
    
    Returns:
        Optional[Dict]: دیکشنری آمار گروه
    """
    try:
        chat_id = str(chat_id)
        response = supabase.table("groups").select("*").eq("chat_id", chat_id).execute()
        
        if response.data and len(response.data) > 0:
            data = response.data[0]
            return {
                "total_hops": _to_int(data.get("total_hops", 0)),
                "total_hapo_points": _to_int(data.get("total_hapo_points", 0)),
                "total_hunts": _to_int(data.get("total_hunts", 0)),
                "member_count": _to_int(data.get("member_count", 0)),
                "is_active": _to_bool(data.get("is_active", True)),
                "title": data.get("title", "گروه بدون نام")
            }
        return None
        
    except Exception as e:
        logger.error(f"❌ خطا در دریافت آمار گروه {chat_id}: {e}")
        return None


def update_group_stats(chat_id: Union[int, str], hops: int = 0, points: int = 0, hunts: int = 0) -> bool:
    """
    به‌روزرسانی آمار گروه
    
    Args:
        chat_id: آیدی گروه
        hops: تعداد هاپ‌های جدید
        points: تعداد پوینت‌های جدید
        hunts: تعداد شکارهای جدید
    
    Returns:
        bool: موفقیت‌آمیز بودن به‌روزرسانی
    """
    try:
        chat_id = str(chat_id)
        current = get_group_stats(chat_id)
        if current is None:
            return False
        
        new_hops = current["total_hops"] + hops
        new_points = current["total_hapo_points"] + points
        new_hunts = current["total_hunts"] + hunts
        
        supabase.table("groups").update({
            "total_hops": _to_str(new_hops),
            "total_hapo_points": _to_str(new_points),
            "total_hunts": _to_str(new_hunts),
            "last_activity": datetime.now().isoformat()
        }).eq("chat_id", chat_id).execute()
        
        logger.info(f"📊 گروه {chat_id}: هاپ={new_hops}, پوینت={new_points}, شکار={new_hunts}")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در به‌روزرسانی آمار گروه {chat_id}: {e}")
        return False


def update_group_member_count(chat_id: Union[int, str], count: int) -> bool:
    """
    به‌روزرسانی تعداد اعضای گروه
    
    Args:
        chat_id: آیدی گروه
        count: تعداد اعضا
    
    Returns:
        bool: موفقیت‌آمیز بودن به‌روزرسانی
    """
    try:
        chat_id = str(chat_id)
        supabase.table("groups").update({
            "member_count": _to_str(count),
            "last_activity": datetime.now().isoformat()
        }).eq("chat_id", chat_id).execute()
        
        logger.info(f"👥 تعداد اعضای گروه {chat_id} آپدیت شد: {count}")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در به‌روزرسانی تعداد اعضا گروه {chat_id}: {e}")
        return False


def update_group_activity(chat_id: Union[int, str]) -> bool:
    """
    به‌روزرسانی زمان آخرین فعالیت گروه
    
    Args:
        chat_id: آیدی گروه
    
    Returns:
        bool: موفقیت‌آمیز بودن به‌روزرسانی
    """
    try:
        chat_id = str(chat_id)
        supabase.table("groups").update({
            "last_activity": datetime.now().isoformat()
        }).eq("chat_id", chat_id).execute()
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در به‌روزرسانی فعالیت گروه {chat_id}: {e}")
        return False


def remove_group(chat_id: Union[int, str]) -> bool:
    """
    غیرفعال کردن گروه
    
    Args:
        chat_id: آیدی گروه
    
    Returns:
        bool: موفقیت‌آمیز بودن غیرفعال‌سازی
    """
    try:
        chat_id = str(chat_id)
        supabase.table("groups").update({
            "is_active": False,
            "last_activity": datetime.now().isoformat()
        }).eq("chat_id", chat_id).execute()
        
        logger.info(f"❌ گروه {chat_id} غیرفعال شد")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در غیرفعال‌سازی گروه {chat_id}: {e}")
        return False


# ================================================================
# توابع هاپوی خیابونی
# ================================================================

def reset_street_hapo_global() -> bool:
    """
    ریست کردن وضعیت جهانی هاپوی خیابونی
    
    Returns:
        bool: موفقیت‌آمیز بودن ریست
    """
    try:
        supabase.table("settings").upsert({
            "key": "street_hapo_active",
            "value": "false",
            "data": {},
            "updated_at": datetime.now().isoformat()
        }).execute()
        logger.info("🔄 وضعیت هاپوی خیابونی ریست شد")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در ریست هاپوی خیابونی: {e}")
        return False


def get_street_hapo_status() -> Dict[str, Any]:
    """
    دریافت وضعیت فعلی هاپوی خیابونی
    
    Returns:
        Dict: وضعیت هاپوی خیابونی
    """
    try:
        response = supabase.table("settings").select("*").eq("key", "street_hapo_active").execute()
        
        if response.data and len(response.data) > 0:
            data = response.data[0]
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
        logger.error(f"❌ خطا در دریافت وضعیت هاپوی خیابونی: {e}")
        return {"active": False, "data": {}}


def set_street_hapo_status(active: bool, data: Optional[Dict] = None) -> bool:
    """
    تنظیم وضعیت هاپوی خیابونی
    
    Args:
        active: فعال یا غیرفعال
        data: داده‌های اضافی
    
    Returns:
        bool: موفقیت‌آمیز بودن تنظیم
    """
    try:
        supabase.table("settings").upsert({
            "key": "street_hapo_active",
            "value": "true" if active else "false",
            "data": data or {},
            "updated_at": datetime.now().isoformat()
        }).execute()
        
        logger.info(f"📋 وضعیت هاپوی خیابونی: {'فعال' if active else 'غیرفعال'}")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در تنظیم وضعیت هاپوی خیابونی: {e}")
        return False


# ================================================================
# توابع رای‌گیری (Votes) - جدید
# ================================================================

def save_vote(vote_key: str, data: Dict[str, Any], expires_at: datetime) -> bool:
    """
    ذخیره رای در دیتابیس
    
    Args:
        vote_key: کلید یکتای رای
        data: داده‌های رای
        expires_at: زمان انقضا
    
    Returns:
        bool: موفقیت‌آمیز بودن ذخیره
    """
    try:
        data_json = json.dumps(data, ensure_ascii=False, default=str)
        
        supabase.table("votes").upsert({
            "vote_key": vote_key,
            "data": data_json,
            "expires_at": expires_at.isoformat(),
            "updated_at": datetime.now().isoformat()
        }).execute()
        
        logger.info(f"✅ رای {vote_key} ذخیره شد")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره رای {vote_key}: {e}")
        return False


def get_vote(vote_key: str) -> Optional[Dict[str, Any]]:
    """
    دریافت اطلاعات رای
    
    Args:
        vote_key: کلید یکتای رای
    
    Returns:
        Optional[Dict]: اطلاعات رای یا None
    """
    try:
        response = supabase.table("votes").select("data").eq("vote_key", vote_key).execute()
        
        if response.data and len(response.data) > 0:
            data_str = response.data[0].get("data")
            if data_str:
                return json.loads(data_str)
        return None
        
    except Exception as e:
        logger.error(f"❌ خطا در دریافت رای {vote_key}: {e}")
        return None


def delete_vote(vote_key: str) -> bool:
    """
    حذف رای از دیتابیس
    
    Args:
        vote_key: کلید یکتای رای
    
    Returns:
        bool: موفقیت‌آمیز بودن حذف
    """
    try:
        supabase.table("votes").delete().eq("vote_key", vote_key).execute()
        logger.info(f"🗑️ رای {vote_key} حذف شد")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در حذف رای {vote_key}: {e}")
        return False


def cleanup_expired_votes() -> int:
    """
    پاک‌سازی رای‌های منقضی شده
    
    Returns:
        int: تعداد رای‌های حذف شده
    """
    try:
        now = datetime.now().isoformat()
        
        # شمارش رای‌های منقضی شده
        count_response = supabase.table("votes").select("vote_key", count="exact").lt("expires_at", now).execute()
        count = count_response.count if hasattr(count_response, 'count') else 0
        
        if count > 0:
            supabase.table("votes").delete().lt("expires_at", now).execute()
            logger.info(f"🧹 {count} رای منقضی شده پاک شد")
        
        return count
        
    except Exception as e:
        logger.error(f"❌ خطا در پاک‌سازی رای‌های منقضی شده: {e}")
        return 0


def get_active_votes(limit: int = 100) -> List[Dict[str, Any]]:
    """
    دریافت لیست رای‌های فعال
    
    Args:
        limit: حداکثر تعداد
    
    Returns:
        List[Dict]: لیست رای‌های فعال
    """
    try:
        now = datetime.now().isoformat()
        
        response = supabase.table("votes") \
            .select("vote_key, data, expires_at") \
            .gt("expires_at", now) \
            .limit(limit) \
            .execute()
        
        if response.data:
            votes = []
            for row in response.data:
                try:
                    data = json.loads(row.get("data", "{}"))
                    votes.append({
                        "vote_key": row.get("vote_key"),
                        "data": data,
                        "expires_at": row.get("expires_at")
                    })
                except:
                    continue
            return votes
        
        return []
        
    except Exception as e:
        logger.error(f"❌ خطا در دریافت رای‌های فعال: {e}")
        return []


# ================================================================
# توابع کمکی اضافی
# ================================================================

def get_top_users(limit: int = 100, order_by: str = "hop_point") -> List[Dict[str, Any]]:
    """
    دریافت لیست کاربران برتر
    
    Args:
        limit: تعداد
        order_by: فیلد مرتب‌سازی
    
    Returns:
        List[Dict]: لیست کاربران
    """
    try:
        response = supabase.table("users") \
            .select("user_id, player_name, hop_point, hop_count, street_hapo_rescued, total_hunts") \
            .order(order_by, desc=True) \
            .limit(limit) \
            .execute()
        
        if response.data:
            return response.data
        return []
        
    except Exception as e:
        logger.error(f"❌ خطا در دریافت کاربران برتر: {e}")
        return []


def get_top_groups(limit: int = 10, order_by: str = "total_hops") -> List[Dict[str, Any]]:
    """
    دریافت لیست گروه‌های برتر
    
    Args:
        limit: تعداد
        order_by: فیلد مرتب‌سازی
    
    Returns:
        List[Dict]: لیست گروه‌ها
    """
    try:
        response = supabase.table("groups") \
            .select("chat_id, title, total_hops, total_hapo_points, total_hunts, member_count") \
            .eq("is_active", True) \
            .order(order_by, desc=True) \
            .limit(limit) \
            .execute()
        
        if response.data:
            return response.data
        return []
        
    except Exception as e:
        logger.error(f"❌ خطا در دریافت گروه‌های برتر: {e}")
        return []


# ================================================================
# اسکریپت‌های راه‌اندازی دیتابیس
# ================================================================

INIT_SQL = """
-- جدول کاربران
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    player_name TEXT,
    hop_point TEXT DEFAULT '0',
    last_hop_time TEXT DEFAULT '0',
    level TEXT DEFAULT '1',
    hop_count TEXT DEFAULT '0',
    is_admin BOOLEAN DEFAULT FALSE,
    claw_level TEXT DEFAULT '0',
    last_hunt_time TEXT DEFAULT '0',
    hunt_active BOOLEAN DEFAULT FALSE,
    hapo_owned BOOLEAN DEFAULT FALSE,
    hapo_name TEXT DEFAULT '',
    hapo_rank TEXT DEFAULT '0',
    hapo_level TEXT DEFAULT '1',
    hapo_food TEXT DEFAULT '4',
    hapo_harvest TEXT DEFAULT '0',
    hapo_last_update TEXT DEFAULT '0',
    bank_opened BOOLEAN DEFAULT FALSE,
    bank_balance TEXT DEFAULT '0',
    bank_last_interest_at TEXT DEFAULT '0',
    bank_card_number TEXT DEFAULT '',
    bank_transactions JSONB DEFAULT '[]',
    has_seen_welcome BOOLEAN DEFAULT FALSE,
    current_hunt_animal JSONB DEFAULT NULL,
    profile_hidden BOOLEAN DEFAULT FALSE,
    profile_locked BOOLEAN DEFAULT FALSE,
    hunt_time TEXT DEFAULT '0',
    last_transfer_time TEXT DEFAULT '0',
    is_transferring BOOLEAN DEFAULT FALSE,
    jailed BOOLEAN DEFAULT FALSE,
    jail_reason TEXT DEFAULT '',
    jail_until TEXT DEFAULT '0',
    jail_fine TEXT DEFAULT '0',
    jail_arrest_time TEXT DEFAULT '0',
    jail_voted JSONB DEFAULT '[]',
    jail_admin_id TEXT,
    street_hapo_rescued TEXT DEFAULT '0',
    fridge_owned BOOLEAN DEFAULT FALSE,
    fridge_level TEXT DEFAULT '1',
    fridge_items JSONB DEFAULT '[]',
    smuggling BOOLEAN DEFAULT FALSE,
    smuggle_count TEXT DEFAULT '0',
    smuggle_start TEXT DEFAULT '0',
    smuggle_duration TEXT DEFAULT '0',
    smuggle_success_chance TEXT DEFAULT '0',
    smuggle_used_hapo TEXT DEFAULT '0',
    total_hunts TEXT DEFAULT '0',
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- جدول گروه‌ها
CREATE TABLE IF NOT EXISTS groups (
    chat_id TEXT PRIMARY KEY,
    title TEXT,
    added_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP DEFAULT NOW(),
    total_hops TEXT DEFAULT '0',
    total_hapo_points TEXT DEFAULT '0',
    total_hunts TEXT DEFAULT '0',
    member_count TEXT DEFAULT '0'
);

-- جدول تنظیمات
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    data JSONB DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- جدول رای‌ها (جدید)
CREATE TABLE IF NOT EXISTS votes (
    vote_key TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ایندکس‌ها
CREATE INDEX IF NOT EXISTS idx_users_level ON users(level);
CREATE INDEX IF NOT EXISTS idx_users_hop_point ON users(hop_point);
CREATE INDEX IF NOT EXISTS idx_groups_active ON groups(is_active);
CREATE INDEX IF NOT EXISTS idx_votes_expires_at ON votes(expires_at);

-- تریگر برای به‌روزرسانی خودکار last_updated
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_users_updated
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
"""

# ================================================================
# تست و راه‌اندازی
# ================================================================

def init_database():
    """راه‌اندازی اولیه دیتابیس (اجرای اسکریپت‌های ایجاد جدول)"""
    try:
        # اینجا می‌تونید اسکریپت SQL رو اجرا کنید
        logger.info("🗄️ دیتابیس آماده است")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی دیتابیس: {e}")
        return False


if __name__ == "__main__":
    # تست اتصال
    try:
        supabase.table("users").select("count").limit(1).execute()
        print("✅ اتصال به Supabase برقرار است!")
    except Exception as e:
        print(f"❌ خطا در اتصال به Supabase: {e}")
