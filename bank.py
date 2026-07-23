# bank.py - منطق بانک (نسخه کامل با اصلاحات)

from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import (
    BANK_INTEREST_RATE, 
    BANK_MAX_DAILY_INTEREST, 
    BANK_ACCOUNT_CHANGE_COST,
    BANK_REQUIRED_LEVEL,
    BANK_PURCHASE_COST
)
from utils import format_number, format_date, safe_int, safe_float, safe_str
from logger_config import log_transaction, log_error, log_db
from globals import get_game

import logging
logger = logging.getLogger(__name__)


# ================================================================
# توابع کمکی
# ================================================================

def get_next_interest_time(game) -> datetime:
    """
    دریافت زمان بعدی واریز سود (۲۴ ساعت بعد از آخرین سود)
    
    Args:
        game: نمونه بازی کاربر
    
    Returns:
        datetime: زمان بعدی واریز سود
    """
    try:
        last_time = game.data.get("bank_last_interest_at", 0)
        
        # تبدیل به float
        if isinstance(last_time, str):
            try:
                last_time = float(last_time)
            except ValueError:
                last_time = 0
        
        if last_time == 0:
            return datetime.now() + timedelta(seconds=1)
        
        return datetime.fromtimestamp(last_time) + timedelta(days=1)
        
    except Exception as e:
        logger.error(f"❌ خطا در محاسبه زمان سود: {e}")
        log_error(e, "محاسبه زمان سود بانکی")
        return datetime.now() + timedelta(days=1)


def calculate_interest(balance: int) -> int:
    """
    محاسبه سود بر اساس موجودی
    
    Args:
        balance: موجودی حساب
    
    Returns:
        int: مبلغ سود
    """
    if balance <= 0:
        return 0
    
    try:
        interest = int(balance * BANK_INTEREST_RATE)
        return min(interest, BANK_MAX_DAILY_INTEREST)
    except Exception as e:
        logger.error(f"❌ خطا در محاسبه سود: {e}")
        return 0


# ================================================================
# توابع نمایش بانک
# ================================================================

def get_bank_menu_text(game, show_transactions: bool = False) -> str:
    """
    دریافت متن منوی بانک
    
    Args:
        game: نمونه بازی کاربر
        show_transactions: نمایش تراکنش‌ها یا نه
    
    Returns:
        str: متن منوی بانک
    """
    try:
        data = game.data
        
        # بررسی وجود بانک
        if not data.get("bank_opened", False):
            return (
                f"🏦 *بانک هاپویی*\n\n"
                f"❌ شما بانک ندارید.\n"
                f"💰 *هزینه خرید:* {format_number(BANK_PURCHASE_COST)} 🪙\n"
                f"⭐ *سطح مورد نیاز:* {BANK_REQUIRED_LEVEL}\n\n"
                f"💡 برای خرید بانک روی دکمه زیر کلیک کن."
            )
        
        # اطلاعات بانک
        balance = safe_int(data.get("bank_balance", 0))
        card_number = safe_str(data.get("bank_card_number", "نامشخص"))
        player_name = safe_str(data.get("player_name", "کاربر"))
        interest = calculate_interest(balance)
        next_time = get_next_interest_time(game)
        
        # ساخت متن
        msg = "🏦 *بانک هاپویی* 🏦\n\n"
        msg += f"💳 *شماره حساب:* `{card_number}`\n"
        msg += f"👤 *به نام:* {player_name}\n\n"
        msg += f"💰 *موجودی حساب:* {format_number(balance)} 🪙\n\n"
        msg += "🤑 *سود بانکی*\n"
        msg += f"┘─ 🛍 *درصد سود:* {int(BANK_INTEREST_RATE * 100)}%\n"
        msg += f"┘─ 📥 *مبلغ واریزی:* {format_number(interest)} 🪙\n"
        msg += f"┘─ ⏳ *زمان واریز:* {format_date(next_time.timestamp())}\n\n"
        
        # نمایش تراکنش‌ها
        if show_transactions:
            msg += "🧾 *تراکنش‌های اخیر*\n"
            msg += "〰️〰️〰️〰️〰️〰️〰️\n\n"
            
            transactions = game.get_bank_transactions()
            if transactions:
                for t in transactions[:3]:
                    icon = "➕" if t.get("type") in ["واریز به حساب بانکی", "سود بانکی", "دریافت کارت به کارت"] else "➖"
                    msg += f"{icon} *{t.get('type', 'تراکنش')}*\n"
                    msg += f"┘─ 💰 *مبلغ:* {format_number(t.get('amount', 0))} 🪙\n"
                    msg += f"┘─ 📅 *تاریخ:* {t.get('date', 'نامشخص')}\n\n"
            else:
                msg += "هیچ تراکنشی ثبت نشده است.\n"
        
        msg += "\n❗️ *برای مدیریت حساب بانکی از گزینه‌های زیر استفاده کنید* ⬇️"
        
        return msg
        
    except Exception as e:
        logger.error(f"❌ خطا در دریافت متن بانک: {e}")
        log_error(e, "دریافت متن بانک", game.user_id)
        return "🏦 *بانک هاپویی*\n\n❌ *خطا در نمایش بانک. لطفاً دوباره تلاش کنید.*"


def get_bank_keyboard(show_transactions: bool = False) -> InlineKeyboardMarkup:
    """
    دریافت کیبورد منوی بانک
    
    Args:
        show_transactions: نمایش تراکنش‌ها یا نه
    
    Returns:
        InlineKeyboardMarkup: کیبورد بانک
    """
    keyboard = []
    
    keyboard.append([
        InlineKeyboardButton("➕ واریز", callback_data="bank_deposit"),
        InlineKeyboardButton("➖ برداشت", callback_data="bank_withdraw")
    ])
    
    keyboard.append([
        InlineKeyboardButton("💳 کارت به کارت", callback_data="bank_card_to_card"),
        InlineKeyboardButton("🧾 تراکنش‌ها", callback_data="bank_transactions")
    ])
    
    keyboard.append([
        InlineKeyboardButton("🔄 تغییر شماره حساب", callback_data="bank_change_card")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_change_card_confirm_text(game) -> str:
    """
    دریافت متن تایید تغییر شماره حساب
    
    Args:
        game: نمونه بازی کاربر
    
    Returns:
        str: متن تایید
    """
    try:
        data = game.data
        
        if not data.get("bank_opened", False):
            return "❌ *شما بانک ندارید.*"
        
        card_number = safe_str(data.get("bank_card_number", "نامشخص"))
        player_name = safe_str(data.get("player_name", "کاربر"))
        
        msg = "🏦 *بانک هاپویی* 🏦\n\n"
        msg += f"💳 *شماره حساب:* `{card_number}`\n"
        msg += f"👤 *به نام:* {player_name}\n\n"
        msg += "🔄 *تغییر شماره حساب*\n"
        msg += f"┘─ 💰 *هزینه:* {format_number(BANK_ACCOUNT_CHANGE_COST)} 🪙\n"
        msg += "┘─ ✅ *شما مجاز به انجام این عملیات هستید.*\n\n"
        msg += "❗️ *با انجام این عملیات، شماره حساب بانکی شما برای همیشه تغییر میکند.*"
        
        return msg
        
    except Exception as e:
        logger.error(f"❌ خطا در دریافت متن تغییر کارت: {e}")
        return "❌ *خطا در دریافت اطلاعات بانک.*"


def get_card_to_card_text() -> str:
    """
    دریافت متن کارت به کارت
    
    Returns:
        str: متن راهنما
    """
    return (
        "💳 *کارت به کارت هاپویی* 💳\n\n"
        "❓ شما درحال تعیین مبلغ کارت به کارت و شماره حساب مقصد هستید.\n\n"
        "🔺 *لطفاً مبلغ و شماره حساب مقصد را در جواب همین پنل وارد کنید*\n"
        "┘─ *مثال:* `500 1234567890123456`\n"
        "┘─ *مثال:* `1k 1234567890123456`\n\n"
        "💡 *مبلغ رو می‌تونی با اختصارات هم وارد کنی:*\n"
        "┘─ `1k` = 1,000 | `1.5k` = 1,500\n"
        "┘─ `1m` = 1,000,000 | `1.5m` = 1,500,000"
    )


def get_bank_not_enough_points_text(needed: int, current: int) -> str:
    """
    دریافت متن عدم موجودی کافی
    
    Args:
        needed: مبلغ مورد نیاز
        current: موجودی فعلی
    
    Returns:
        str: متن خطا
    """
    return (
        f"❌ *پوینت کافی نیست!*\n\n"
        f"💰 *نیاز:* {format_number(needed)} 🪙\n"
        f"💰 *موجودی شما:* {format_number(current)} 🪙\n\n"
        f"💡 *برای افزایش پوینت، هاپ هاپ کن!* 🐾"
    )


def get_bank_balance_text(balance: int) -> str:
    """
    دریافت متن موجودی بانک
    
    Args:
        balance: موجودی
    
    Returns:
        str: متن موجودی
    """
    return f"💰 *موجودی بانک:* {format_number(balance)} 🪙"


# ================================================================
# توابع اعتبارسنجی بانک
# ================================================================

def validate_bank_amount(amount: int) -> tuple:
    """
    اعتبارسنجی مبلغ بانکی
    
    Args:
        amount: مبلغ
    
    Returns:
        tuple: (معتبر است, پیام خطا)
    """
    if amount <= 0:
        return False, "❌ مبلغ باید بیشتر از صفر باشد"
    
    if amount < 100:
        return False, "❌ حداقل مبلغ 100 هاپو پوینت است"
    
    return True, ""


def validate_card_number(card_number: str) -> tuple:
    """
    اعتبارسنجی شماره کارت بانکی
    
    Args:
        card_number: شماره کارت
    
    Returns:
        tuple: (معتبر است, پیام خطا)
    """
    if not card_number:
        return False, "❌ شماره کارت را وارد کن"
    
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if len(card_number) != 16:
        return False, "❌ شماره کارت باید ۱۶ رقم باشد"
    
    if not card_number.isdigit():
        return False, "❌ شماره کارت فقط باید شامل اعداد باشد"
    
    return True, ""


# ================================================================
# توابع مدیریت تراکنش‌ها
# ================================================================

def log_bank_transaction(game, transaction_type: str, amount: int, detail: str = ""):
    """
    ثبت تراکنش بانکی
    
    Args:
        game: نمونه بازی کاربر
        transaction_type: نوع تراکنش
        amount: مبلغ
        detail: جزئیات
    """
    try:
        game.add_bank_transaction(transaction_type, amount, detail)
        log_transaction(
            game.user_id, 
            f"بانک - {transaction_type}", 
            amount, 
            detail
        )
        log_db("INSERT", "bank_transactions", game.user_id, f"{transaction_type}: {amount}")
    except Exception as e:
        logger.error(f"❌ خطا در ثبت تراکنش بانکی: {e}")
        log_error(e, "ثبت تراکنش بانکی", game.user_id)
