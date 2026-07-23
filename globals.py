# globals.py - اشیاء و متغیرهای سراسری (نسخه کامل)

from game_functions import game_manager
from game import StreetHapo
from game import HopDogGame

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
# دیکشنری user_games (برای ذخیره نمونه‌های بازی کاربران)
# ================================================================

user_games = {}

def get_game(user_id, username=""):
    """
    دریافت یا ایجاد نمونه بازی برای کاربر
    
    Args:
        user_id: آیدی عددی کاربر
        username: نام کاربری (اختیاری)
    
    Returns:
        HopDogGame: نمونه بازی کاربر
    """
    if user_id not in user_games:
        user_games[user_id] = HopDogGame(user_id, username)
    return user_games[user_id]


def clear_user_game(user_id):
    """پاک کردن نمونه بازی کاربر از حافظه (برای ریست)"""
    if user_id in user_games:
        del user_games[user_id]
        return True
    return False


def get_all_user_games():
    """دریافت لیست همه کاربران فعال در حافظه"""
    return list(user_games.keys())


# ================================================================
# توابع کمکی برای مدیریت GAME_MESSAGES
# ================================================================

def save_game_message(chat_id, message_id, game_id):
    """ذخیره پیام بازی برای ویرایش بعدی"""
    key = f"{chat_id}_{game_id}"
    GAME_MESSAGES[key] = message_id


def get_game_message(chat_id, game_id):
    """دریافت پیام ذخیره شده بازی"""
    key = f"{chat_id}_{game_id}"
    return GAME_MESSAGES.get(key)


def clear_game_message(chat_id, game_id):
    """پاک کردن پیام ذخیره شده بازی"""
    key = f"{chat_id}_{game_id}"
    if key in GAME_MESSAGES:
        del GAME_MESSAGES[key]
        return True
    return False


def clear_all_game_messages():
    """پاک کردن همه پیام‌های ذخیره شده بازی"""
    GAME_MESSAGES.clear()


# ================================================================
# توابع کمکی برای مدیریت GAME_XO_STATE
# ================================================================

def set_xo_state(user_id, state_data):
    """تنظیم وضعیت بازی XO برای کاربر"""
    GAME_XO_STATE[str(user_id)] = state_data


def get_xo_state(user_id):
    """دریافت وضعیت بازی XO برای کاربر"""
    return GAME_XO_STATE.get(str(user_id))


def clear_xo_state(user_id):
    """پاک کردن وضعیت بازی XO برای کاربر"""
    if str(user_id) in GAME_XO_STATE:
        del GAME_XO_STATE[str(user_id)]
        return True
    return False


# ================================================================
# توابع کمکی برای مدیریت SPAM_TRACKER
# ================================================================

def get_spam_tracker(user_id):
    """دریافت وضعیت اسپم کاربر"""
    return SPAM_TRACKER.get(user_id)


def set_spam_tracker(user_id, data):
    """تنظیم وضعیت اسپم کاربر"""
    SPAM_TRACKER[user_id] = data


def clear_spam_tracker(user_id):
    """پاک کردن وضعیت اسپم کاربر"""
    if user_id in SPAM_TRACKER:
        del SPAM_TRACKER[user_id]
        return True
    return False


# ================================================================
# توابع کمکی برای مدیریت TRANSFER_STATE
# ================================================================

def set_transfer_state(user_id, data):
    """تنظیم وضعیت انتقال کاربر"""
    TRANSFER_STATE[str(user_id)] = data


def get_transfer_state(user_id):
    """دریافت وضعیت انتقال کاربر"""
    return TRANSFER_STATE.get(str(user_id))


def clear_transfer_state(user_id):
    """پاک کردن وضعیت انتقال کاربر"""
    if str(user_id) in TRANSFER_STATE:
        del TRANSFER_STATE[str(user_id)]
        return True
    return False


# ================================================================
# توابع کمکی برای مدیریت STREET_HAPO_LAST_SENT
# ================================================================

def get_street_hapo_last_sent(chat_id):
    """دریافت زمان آخرین ارسال هاپوی خیابونی به گروه"""
    return STREET_HAPO_LAST_SENT.get(str(chat_id), 0)


def set_street_hapo_last_sent(chat_id, timestamp):
    """تنظیم زمان آخرین ارسال هاپوی خیابونی به گروه"""
    STREET_HAPO_LAST_SENT[str(chat_id)] = timestamp


def clear_street_hapo_last_sent(chat_id):
    """پاک کردن زمان آخرین ارسال هاپوی خیابونی به گروه"""
    if str(chat_id) in STREET_HAPO_LAST_SENT:
        del STREET_HAPO_LAST_SENT[str(chat_id)]
        return True
    return False
