# bank.py - منطق بانک (منوها، کارت، تراکنش‌ها)

from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import BANK_INTEREST_RATE, BANK_MAX_DAILY_INTEREST, BANK_ACCOUNT_CHANGE_COST

# ================================================================
# توابع کمکی
# ================================================================

def format_number(n):
    """فرمت کردن اعداد با کاما"""
    if n is None:
        return "0"
    try:
        return f"{int(float(n)):,}"
    except (ValueError, TypeError):
        return "0"

def format_date(dt):
    """فرمت کردن تاریخ"""
    if dt is None:
        return "نامشخص"
    try:
        return dt.strftime("%H:%M %Y/%m/%d")
    except:
        return "نامشخص"

def get_next_interest_time(game):
    """دریافت زمان بعدی واریز سود (۲۴ ساعت بعد از آخرین سود)"""
    try:
        last_time = game.data.get("bank_last_interest_at", 0)
        # تبدیل به float اگر string باشه
        if isinstance(last_time, str):
            try:
                last_time = float(last_time)
            except ValueError:
                last_time = 0
        
        if last_time == 0:
            return datetime.now() + timedelta(seconds=1)
        
        return datetime.fromtimestamp(last_time) + timedelta(days=1)
    except Exception as e:
        print(f"Error in get_next_interest_time: {e}")
        return datetime.now() + timedelta(days=1)

def calculate_interest(balance):
    """محاسبه سود بر اساس موجودی"""
    if balance <= 0:
        return 0
    try:
        return min(int(balance * BANK_INTEREST_RATE), BANK_MAX_DAILY_INTEREST)
    except:
        return 0

# ================================================================
# توابع نمایش بانک
# ================================================================

def get_bank_menu_text(game, show_transactions=False):
    """دریافت متن منوی بانک"""
    try:
        data = game.data
        if not data.get("bank_opened", False):
            return "🏦 بانک هاپویی\n\n❌ شما بانک ندارید. برای خرید بانک روی دکمه زیر کلیک کن."
        
        balance = int(float(data.get("bank_balance", 0)))
        card_number = data.get("bank_card_number", "نامشخص")
        player_name = data.get("player_name", "کاربر")
        interest = calculate_interest(balance)
        next_time = get_next_interest_time(game)
        
        msg = "🏦 بانک هاپویی 🏦\n\n"
        msg += f"💳 شماره حساب : {card_number}\n"
        msg += f"👤 به نام : {player_name}\n\n"
        msg += f"💰 موجودی حساب : {format_number(balance)} 🪙\n\n"
        msg += "🤑 سود بانکی\n"
        msg += f"┘─ 🛍 درصد سود : {int(BANK_INTEREST_RATE * 100)}%\n"
        msg += f"┘─ 📥 مبلغ واریزی : {format_number(interest)} 🪙\n"
        msg += f"┘─ ⏳ زمان واریز : {format_date(next_time)}\n\n"
        
        if show_transactions:
            msg += "🧾 تراکنش های اخیر\n"
            msg += "〰️〰️〰️〰️〰️〰️〰️\n\n"
            transactions = game.get_bank_transactions()
            if transactions:
                for t in transactions[:3]:
                    icon = "➕" if t.get("type") in ["واریز به حساب بانکی", "سود بانکی", "دریافت کارت به کارت"] else "➖"
                    msg += f"{icon} {t.get('type', 'تراکنش')}\n"
                    msg += f"┘─ 💰 مبلغ : {format_number(t.get('amount', 0))} 🪙\n"
                    msg += f"┘─ 📅 تاریخ : {t.get('date', 'نامشخص')}\n\n"
            else:
                msg += "هیچ تراکنشی ثبت نشده است.\n"
        
        msg += "\n❗️ برای مدیریت حساب بانکی از گزینه های زیر استفاده کنید ⬇️"
        return msg
    except Exception as e:
        print(f"Error in get_bank_menu_text: {e}")
        return "🏦 بانک هاپویی\n\n❌ خطا در نمایش بانک. لطفاً دوباره تلاش کنید."

def get_bank_keyboard(show_transactions=False):
    """دریافت کیبورد منوی بانک"""
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

def get_change_card_confirm_text(game):
    """دریافت متن تایید تغییر شماره حساب"""
    try:
        data = game.data
        if not data.get("bank_opened", False):
            return "❌ شما بانک ندارید."
        
        card_number = data.get("bank_card_number", "نامشخص")
        player_name = data.get("player_name", "کاربر")
        
        msg = "🏦 بانک هاپویی🏦\n\n"
        msg += f"💳 شماره حساب : {card_number}\n"
        msg += f"👤 به نام : {player_name}\n\n"
        msg += "🔄 تغییر شماره حساب\n"
        msg += f"┘─ 💰 هزینه تغییر شماره حساب : {format_number(BANK_ACCOUNT_CHANGE_COST)} 🪙\n"
        msg += "┘─ ✅ شما مجاز به انجام این عملیات میباشید.\n\n"
        msg += "❗️ با انجام این عملیات , شماره حساب بانکی شما برای همیشه تغییر میکند."
        
        return msg
    except Exception as e:
        print(f"Error in get_change_card_confirm_text: {e}")
        return "❌ خطا در دریافت اطلاعات بانک."

def get_card_to_card_text():
    """دریافت متن کارت به کارت"""
    return """💳 کارت به کارت هاپویی 💳

❓ شما درحال تعیین مبلغ کارت به کارت و شماره حساب مقصد میباشید.

🔺 لطفا مبلغ کارت به کارت و شماره حساب مقصد را در جواب همین پنل وارد کنید
┘─ مثال :
500 1234567890123
┘─ مثال : {مبلغ} {شماره حساب}"""
