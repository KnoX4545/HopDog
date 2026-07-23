# utils.py - توابع کمکی عمومی

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from game import HopDogGame


# ================================================================
# دیکشنری user_games (برای ذخیره نمونه‌های بازی)
# ================================================================

user_games = {}


# ================================================================
# توابع کمکی
# ================================================================

def get_game(user_id, username=""):
    """دریافت یا ایجاد نمونه بازی برای کاربر"""
    if user_id not in user_games:
        user_games[user_id] = HopDogGame(user_id, username)
    return user_games[user_id]


def parse_amount(text):
    """تبدیل اختصارات اعداد به عدد واقعی
    مثال: 1k → 1000, 1m → 1000000, 1.5k → 1500
    عدد عادی مثل 1000 هم کار میکنه
    """
    text = str(text).strip().lower().replace(",", "").replace(" ", "")
    
    # تشخیص اختصارات
    if text.endswith("k"):
        try:
            num = float(text[:-1])
            return int(num * 1000)
        except:
            return None
    elif text.endswith("m"):
        try:
            num = float(text[:-1])
            return int(num * 1000000)
        except:
            return None
    elif text.endswith("کا"):
        try:
            num = float(text.replace("کا", ""))
            return int(num * 1000)
        except:
            return None
    elif text.endswith("میل"):
        try:
            num = float(text.replace("میل", ""))
            return int(num * 1000000)
        except:
            return None
    else:
        # عدد عادی
        try:
            return int(float(text))
        except:
            return None


def get_confirm_keyboard(callback_data_yes, callback_data_no):
    """ساخت کیبورد تایید"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ بله", callback_data=callback_data_yes),
         InlineKeyboardButton("❌ نه", callback_data=callback_data_no)]
    ])


def get_user_display_name(user_id, username=None, full_name=None):
    """ساخت نام نمایشی کاربر برای پیام‌ها"""
    if username:
        return f"@{username}"
    if full_name:
        return full_name
    return f"User {user_id}"
