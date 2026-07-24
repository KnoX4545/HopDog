# globals.py - اشیاء و متغیرهای سراسری (نسخه کامل با کش TTL و به‌روزرسانی)

import time
from typing import Dict, Optional, Any, List
from game_functions import game_manager
from game import StreetHapo, HopDogGame

# ================================================================
# دیکشنری‌های عمومی (که در حافظه هستن)
# ================================================================

# ردیابی اسپم کاربران
SPAM_TRACKER = {}

# رای‌گیری میو (فقط برای زمان‌بندی، داده اصلی در دیتابیسه)
MEOW_VOTES = {}

# وضعیت انتقال کاربران
TRANSFER_STATE = {}

# زمان آخرین ارسال هاپوی خیابونی به هر گروه
STREET_HAPO_LAST_SENT = {}

# وضعیت بازی XO برای هر کاربر (تعیین مبلغ شرط)
GAME_XO_STATE = {}

# پیام‌های بازی برای ویرایش
GAME_MESSAGES = {}


# ================================================================
# کش کاربران با TTL (Time To Live)
# ================================================================

# دیکشنری ذخیره نمونه‌های بازی کاربران
user_games: Dict[int, HopDogGame] = {}

# زمان آخرین به‌روزرسانی هر کاربر (برای TTL)
USER_CACHE_TIMESTAMPS: Dict[int, float] = {}

# زمان انقضای کش به ثانیه (۵ دقیقه)
USER_CACHE_TTL = 300


# ================================================================
# نمونه StreetHapo (Singleton)
# ================================================================

street_hapo_instance = None

def get_street_hapo():
    """دریافت یا ایجاد نمونه StreetHapo"""
    global street_hapo_instance
    if street_hapo_instance is None:
        street_hapo_instance = StreetHapo()
    return street_hapo_instance


# ================================================================
# توابع مدیریت کش کاربران (نسخه نهایی با TTL)
# ================================================================

def get_game(user_id: int, username: str = "") -> HopDogGame:
    """
    دریافت یا ایجاد نمونه بازی برای کاربر با کش TTL
    
    Args:
        user_id: آیدی عددی کاربر
        username: نام کاربری (اختیاری)
    
    Returns:
        HopDogGame: نمونه بازی کاربر
    """
    user_id = int(user_id)
    
    # بررسی وجود کاربر در کش و TTL
    if user_id in user_games:
        timestamp = USER_CACHE_TIMESTAMPS.get(user_id, 0)
        # اگر کش هنوز معتبر است
        if time.time() - timestamp < USER_CACHE_TTL:
            return user_games[user_id]
        else:
            # کش منقضی شده، حذف کن
            del user_games[user_id]
            if user_id in USER_CACHE_TIMESTAMPS:
                del USER_CACHE_TIMESTAMPS[user_id]
    
    # ایجاد نمونه جدید (بارگذاری از دیتابیس)
    user_games[user_id] = HopDogGame(user_id, username)
    USER_CACHE_TIMESTAMPS[user_id] = time.time()
    return user_games[user_id]


def refresh_user_cache(user_id: int) -> bool:
    """
    بازخوانی کش کاربر از دیتابیس (برای بعد از تغییرات ادمین)
    
    Args:
        user_id: آیدی عددی کاربر
    
    Returns:
        bool: موفقیت‌آمیز بودن بازخوانی
    """
    user_id = int(user_id)
    if user_id in user_games:
        # بارگذاری مجدد از دیتابیس
        user_games[user_id].load_data()
        # به‌روزرسانی زمان کش
        USER_CACHE_TIMESTAMPS[user_id] = time.time()
        return True
    return False


def clear_user_game(user_id: int) -> bool:
    """
    پاک کردن نمونه بازی کاربر از حافظه
    
    Args:
        user_id: آیدی عددی کاربر
    
    Returns:
        bool: موفقیت‌آمیز بودن پاک کردن
    """
    user_id = int(user_id)
    if user_id in user_games:
        del user_games[user_id]
        if user_id in USER_CACHE_TIMESTAMPS:
            del USER_CACHE_TIMESTAMPS[user_id]
        return True
    return False


def get_all_user_games() -> List[int]:
    """
    دریافت لیست همه کاربران فعال در حافظه
    
    Returns:
        List[int]: لیست آیدی کاربران
    """
    return list(user_games.keys())


def get_user_cache_info(user_id: int) -> Optional[Dict[str, Any]]:
    """
    دریافت اطلاعات کش یک کاربر
    
    Args:
        user_id: آیدی عددی کاربر
    
    Returns:
        Optional[Dict]: اطلاعات کش یا None
    """
    user_id = int(user_id)
    if user_id in user_games and user_id in USER_CACHE_TIMESTAMPS:
        timestamp = USER_CACHE_TIMESTAMPS[user_id]
        remaining = max(0, USER_CACHE_TTL - (time.time() - timestamp))
        return {
            "cached": True,
            "age": time.time() - timestamp,
            "remaining": remaining,
            "expired": remaining <= 0
        }
    return {"cached": False}


def clear_all_user_cache() -> int:
    """
    پاک کردن همه کش کاربران
    
    Returns:
        int: تعداد کاربران پاک شده
    """
    count = len(user_games)
    user_games.clear()
    USER_CACHE_TIMESTAMPS.clear()
    return count


# ================================================================
# توابع کمکی برای مدیریت GAME_MESSAGES
# ================================================================

def save_game_message(chat_id: int, message_id: int, game_id: str) -> None:
    """
    ذخیره پیام بازی برای ویرایش بعدی
    
    Args:
        chat_id: آیدی گروه
        message_id: آیدی پیام
        game_id: آیدی بازی
    """
    key = f"{chat_id}_{game_id}"
    GAME_MESSAGES[key] = message_id


def get_game_message(chat_id: int, game_id: str) -> Optional[int]:
    """
    دریافت پیام ذخیره شده بازی
    
    Args:
        chat_id: آیدی گروه
        game_id: آیدی بازی
    
    Returns:
        Optional[int]: آیدی پیام یا None
    """
    key = f"{chat_id}_{game_id}"
    return GAME_MESSAGES.get(key)


def clear_game_message(chat_id: int, game_id: str) -> bool:
    """
    پاک کردن پیام ذخیره شده بازی
    
    Args:
        chat_id: آیدی گروه
        game_id: آیدی بازی
    
    Returns:
        bool: موفقیت‌آمیز بودن پاک کردن
    """
    key = f"{chat_id}_{game_id}"
    if key in GAME_MESSAGES:
        del GAME_MESSAGES[key]
        return True
    return False


def clear_all_game_messages() -> int:
    """
    پاک کردن همه پیام‌های ذخیره شده بازی
    
    Returns:
        int: تعداد پیام‌های پاک شده
    """
    count = len(GAME_MESSAGES)
    GAME_MESSAGES.clear()
    return count


# ================================================================
# توابع کمکی برای مدیریت GAME_XO_STATE
# ================================================================

def set_xo_state(user_id: int, state_data: Dict[str, Any]) -> None:
    """
    تنظیم وضعیت بازی XO برای کاربر
    
    Args:
        user_id: آیدی کاربر
        state_data: داده‌های وضعیت
    """
    GAME_XO_STATE[str(user_id)] = state_data


def get_xo_state(user_id: int) -> Optional[Dict[str, Any]]:
    """
    دریافت وضعیت بازی XO برای کاربر
    
    Args:
        user_id: آیدی کاربر
    
    Returns:
        Optional[Dict]: داده‌های وضعیت یا None
    """
    return GAME_XO_STATE.get(str(user_id))


def clear_xo_state(user_id: int) -> bool:
    """
    پاک کردن وضعیت بازی XO برای کاربر
    
    Args:
        user_id: آیدی کاربر
    
    Returns:
        bool: موفقیت‌آمیز بودن پاک کردن
    """
    key = str(user_id)
    if key in GAME_XO_STATE:
        del GAME_XO_STATE[key]
        return True
    return False


def clear_all_xo_states() -> int:
    """
    پاک کردن همه وضعیت‌های بازی XO
    
    Returns:
        int: تعداد وضعیت‌های پاک شده
    """
    count = len(GAME_XO_STATE)
    GAME_XO_STATE.clear()
    return count


# ================================================================
# توابع کمکی برای مدیریت SPAM_TRACKER
# ================================================================

def get_spam_tracker(user_id: int) -> Optional[Dict[str, Any]]:
    """
    دریافت وضعیت اسپم کاربر
    
    Args:
        user_id: آیدی کاربر
    
    Returns:
        Optional[Dict]: وضعیت اسپم یا None
    """
    return SPAM_TRACKER.get(user_id)


def set_spam_tracker(user_id: int, data: Dict[str, Any]) -> None:
    """
    تنظیم وضعیت اسپم کاربر
    
    Args:
        user_id: آیدی کاربر
        data: داده‌های وضعیت
    """
    SPAM_TRACKER[user_id] = data


def clear_spam_tracker(user_id: int) -> bool:
    """
    پاک کردن وضعیت اسپم کاربر
    
    Args:
        user_id: آیدی کاربر
    
    Returns:
        bool: موفقیت‌آمیز بودن پاک کردن
    """
    if user_id in SPAM_TRACKER:
        del SPAM_TRACKER[user_id]
        return True
    return False


def clear_all_spam_trackers() -> int:
    """
    پاک کردن همه وضعیت‌های اسپم
    
    Returns:
        int: تعداد وضعیت‌های پاک شده
    """
    count = len(SPAM_TRACKER)
    SPAM_TRACKER.clear()
    return count


# ================================================================
# توابع کمکی برای مدیریت TRANSFER_STATE
# ================================================================

def set_transfer_state(user_id: int, data: Dict[str, Any]) -> None:
    """
    تنظیم وضعیت انتقال کاربر
    
    Args:
        user_id: آیدی کاربر
        data: داده‌های وضعیت
    """
    TRANSFER_STATE[str(user_id)] = data


def get_transfer_state(user_id: int) -> Optional[Dict[str, Any]]:
    """
    دریافت وضعیت انتقال کاربر
    
    Args:
        user_id: آیدی کاربر
    
    Returns:
        Optional[Dict]: داده‌های وضعیت یا None
    """
    return TRANSFER_STATE.get(str(user_id))


def clear_transfer_state(user_id: int) -> bool:
    """
    پاک کردن وضعیت انتقال کاربر
    
    Args:
        user_id: آیدی کاربر
    
    Returns:
        bool: موفقیت‌آمیز بودن پاک کردن
    """
    key = str(user_id)
    if key in TRANSFER_STATE:
        del TRANSFER_STATE[key]
        return True
    return False


def clear_all_transfer_states() -> int:
    """
    پاک کردن همه وضعیت‌های انتقال
    
    Returns:
        int: تعداد وضعیت‌های پاک شده
    """
    count = len(TRANSFER_STATE)
    TRANSFER_STATE.clear()
    return count


# ================================================================
# توابع کمکی برای مدیریت STREET_HAPO_LAST_SENT
# ================================================================

def get_street_hapo_last_sent(chat_id: int) -> float:
    """
    دریافت زمان آخرین ارسال هاپوی خیابونی به گروه
    
    Args:
        chat_id: آیدی گروه
    
    Returns:
        float: تایم‌استمپ آخرین ارسال
    """
    return STREET_HAPO_LAST_SENT.get(str(chat_id), 0)


def set_street_hapo_last_sent(chat_id: int, timestamp: float) -> None:
    """
    تنظیم زمان آخرین ارسال هاپوی خیابونی به گروه
    
    Args:
        chat_id: آیدی گروه
        timestamp: تایم‌استمپ
    """
    STREET_HAPO_LAST_SENT[str(chat_id)] = timestamp


def clear_street_hapo_last_sent(chat_id: int) -> bool:
    """
    پاک کردن زمان آخرین ارسال هاپوی خیابونی به گروه
    
    Args:
        chat_id: آیدی گروه
    
    Returns:
        bool: موفقیت‌آمیز بودن پاک کردن
    """
    key = str(chat_id)
    if key in STREET_HAPO_LAST_SENT:
        del STREET_HAPO_LAST_SENT[key]
        return True
    return False


def clear_all_street_hapo_last_sent() -> int:
    """
    پاک کردن همه زمان‌های ارسال هاپوی خیابونی
    
    Returns:
        int: تعداد آیتم‌های پاک شده
    """
    count = len(STREET_HAPO_LAST_SENT)
    STREET_HAPO_LAST_SENT.clear()
    return count


# ================================================================
# توابع کمکی برای مدیریت MEOW_VOTES
# ================================================================

def get_meow_vote(chat_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    دریافت رای میو برای یک کاربر در یک گروه
    
    Args:
        chat_id: آیدی گروه
        user_id: آیدی کاربر
    
    Returns:
        Optional[Dict]: داده‌های رای یا None
    """
    key = f"{chat_id}_{user_id}"
    return MEOW_VOTES.get(key)


def set_meow_vote(chat_id: int, user_id: int, data: Dict[str, Any]) -> None:
    """
    تنظیم رای میو برای یک کاربر در یک گروه
    
    Args:
        chat_id: آیدی گروه
        user_id: آیدی کاربر
        data: داده‌های رای
    """
    key = f"{chat_id}_{user_id}"
    MEOW_VOTES[key] = data


def clear_meow_vote(chat_id: int, user_id: int) -> bool:
    """
    پاک کردن رای میو برای یک کاربر در یک گروه
    
    Args:
        chat_id: آیدی گروه
        user_id: آیدی کاربر
    
    Returns:
        bool: موفقیت‌آمیز بودن پاک کردن
    """
    key = f"{chat_id}_{user_id}"
    if key in MEOW_VOTES:
        del MEOW_VOTES[key]
        return True
    return False


def clear_all_meow_votes() -> int:
    """
    پاک کردن همه رای‌های میو
    
    Returns:
        int: تعداد رای‌های پاک شده
    """
    count = len(MEOW_VOTES)
    MEOW_VOTES.clear()
    return count


# ================================================================
# تابع پاک‌سازی کامل همه کش‌ها (برای ری‌استارت)
# ================================================================

def clear_all_caches() -> Dict[str, int]:
    """
    پاک کردن همه کش‌ها و دیکشنری‌های حافظه
    
    Returns:
        Dict[str, int]: آمار پاک‌سازی
    """
    return {
        "user_games": clear_all_user_cache(),
        "game_messages": clear_all_game_messages(),
        "xo_states": clear_all_xo_states(),
        "spam_trackers": clear_all_spam_trackers(),
        "transfer_states": clear_all_transfer_states(),
        "street_hapo_last_sent": clear_all_street_hapo_last_sent(),
        "meow_votes": clear_all_meow_votes()
    }


# ================================================================
# تابع دریافت آمار حافظه (برای دیباگ)
# ================================================================

def get_memory_stats() -> Dict[str, int]:
    """
    دریافت آمار استفاده از حافظه
    
    Returns:
        Dict[str, int]: آمار حافظه
    """
    return {
        "user_games": len(user_games),
        "game_messages": len(GAME_MESSAGES),
        "xo_states": len(GAME_XO_STATE),
        "spam_trackers": len(SPAM_TRACKER),
        "transfer_states": len(TRANSFER_STATE),
        "street_hapo_last_sent": len(STREET_HAPO_LAST_SENT),
        "meow_votes": len(MEOW_VOTES),
        "total": (
            len(user_games) + 
            len(GAME_MESSAGES) + 
            len(GAME_XO_STATE) + 
            len(SPAM_TRACKER) + 
            len(TRANSFER_STATE) + 
            len(STREET_HAPO_LAST_SENT) + 
            len(MEOW_VOTES)
        )
    }


# ================================================================
# تست و راه‌اندازی
# ================================================================

if __name__ == "__main__":
    # تست کش
    print("🧪 تست globals.py...")
    
    # تست get_game
    game1 = get_game(123456789, "testuser")
    print(f"✅ کاربر 123456789: {game1.data.get('player_name')}")
    
    # تست کش
    print(f"✅ کش کاربران: {len(user_games)}")
    
    # تست refresh
    refresh_user_cache(123456789)
    print("✅ کش به‌روزرسانی شد")
    
    # تست clear
    clear_user_game(123456789)
    print(f"✅ کاربر پاک شد: {len(user_games)}")
    
    # تست آمار
    stats = get_memory_stats()
    print(f"📊 آمار حافظه: {stats}")
    
    print("🎉 همه تست‌ها با موفقیت انجام شد!")
