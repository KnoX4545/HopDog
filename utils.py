# utils.py - توابع کمکی عمومی

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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
