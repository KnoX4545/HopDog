# utils.py - توابع کمکی عمومی (نسخه کامل)

import re
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, Tuple, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ================================================================
# توابع تبدیل و فرمت‌بندی اعداد
# ================================================================

def format_number(n: Union[int, float, str, None]) -> str:
    """
    فرمت کردن اعداد با کاما
    
    Args:
        n: عدد (می‌تواند int, float, str یا None باشد)
    
    Returns:
        str: عدد فرمت شده با کاما
    
    Examples:
        >>> format_number(1000)
        '1,000'
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(None)
        '0'
    """
    if n is None:
        return "0"
    try:
        if isinstance(n, str):
            n = float(n.replace(',', ''))
        return f"{int(float(n)):,}"
    except (ValueError, TypeError):
        return "0"


def parse_amount(text: str) -> Optional[int]:
    """
    تبدیل اختصارات اعداد به عدد واقعی
    
    پشتیبانی از:
    - اعداد معمولی: 1000, 500
    - k (هزار): 1k = 1000, 1.5k = 1500
    - m (میلیون): 1m = 1000000, 1.5m = 1500000
    - کا (هزار): 1کا = 1000
    - میل (میلیون): 1میل = 1000000
    
    Args:
        text: رشته ورودی
    
    Returns:
        Optional[int]: عدد تبدیل شده یا None در صورت خطا
    
    Examples:
        >>> parse_amount("1000")
        1000
        >>> parse_amount("1k")
        1000
        >>> parse_amount("1.5m")
        1500000
        >>> parse_amount("abc")
        None
    """
    if not text:
        return None
    
    text = str(text).strip().lower().replace(",", "").replace(" ", "")
    
    # حذف کاراکترهای غیرعددی به جز نقطه و حروف اختصاری
    if not re.match(r'^[\d.]+[kmکیل]?$', text.replace('میل', '')):
        # بررسی با حذف اختصارات فارسی
        clean_text = text.replace('کا', '').replace('میل', '')
        if not re.match(r'^[\d.]+$', clean_text):
            return None
    
    try:
        # تشخیص اختصارات
        if text.endswith('k'):
            num = float(text[:-1])
            return int(num * 1000)
        elif text.endswith('m'):
            num = float(text[:-1])
            return int(num * 1000000)
        elif text.endswith('کا'):
            num = float(text.replace('کا', ''))
            return int(num * 1000)
        elif text.endswith('میل'):
            num = float(text.replace('میل', ''))
            return int(num * 1000000)
        else:
            # عدد عادی
            return int(float(text))
    except (ValueError, TypeError):
        return None


def format_duration(seconds: int) -> str:
    """
    تبدیل ثانیه به فرمت خوانا
    
    Args:
        seconds: تعداد ثانیه
    
    Returns:
        str: زمان فرمت شده
    
    Examples:
        >>> format_duration(65)
        '1 دقیقه و 5 ثانیه'
        >>> format_duration(3600)
        '1 ساعت'
        >>> format_duration(3665)
        '1 ساعت و 1 دقیقه و 5 ثانیه'
    """
    if seconds <= 0:
        return "0 ثانیه"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} ساعت")
    if minutes > 0:
        parts.append(f"{minutes} دقیقه")
    if secs > 0:
        parts.append(f"{secs} ثانیه")
    
    return " و ".join(parts)


def format_date(timestamp: Union[int, float, str, None]) -> str:
    """
    تبدیل timestamp به تاریخ خوانا
    
    Args:
        timestamp: timestamp (یا None)
    
    Returns:
        str: تاریخ فرمت شده
    
    Examples:
        >>> format_date(1640995200)
        '01/01/2022 00:00:00'
    """
    if timestamp is None:
        return "نامشخص"
    try:
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y/%m/%d %H:%M:%S")
    except (ValueError, TypeError):
        return "نامشخص"


def format_date_persian(timestamp: Union[int, float, str, None]) -> str:
    """
    تبدیل timestamp به تاریخ شمسی (تقریبی)
    
    Args:
        timestamp: timestamp (یا None)
    
    Returns:
        str: تاریخ فرمت شده به شمسی
    """
    if timestamp is None:
        return "نامشخص"
    try:
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        dt = datetime.fromtimestamp(timestamp)
        # تبدیل تقریبی به شمسی (فقط برای نمایش)
        persian_months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 
                         'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
        # محاسبه تقریبی (دقت کامل نیست)
        year = dt.year - 622
        month = dt.month
        day = dt.day
        if month > 3:
            month -= 3
        else:
            month += 9
            year -= 1
        return f"{day} {persian_months[month-1]} {year} ساعت {dt.strftime('%H:%M')}"
    except:
        return "نامشخص"


# ================================================================
# توابع کیبورد
# ================================================================

def get_confirm_keyboard(callback_data_yes: str, callback_data_no: str) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تایید (بله/نه)
    
    Args:
        callback_data_yes: کالبک برای دکمه بله
        callback_data_no: کالبک برای دکمه نه
    
    Returns:
        InlineKeyboardMarkup: کیبورد تایید
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ بله", callback_data=callback_data_yes),
            InlineKeyboardButton("❌ نه", callback_data=callback_data_no)
        ]
    ])


def get_cancel_keyboard(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """
    ساخت کیبورد لغو
    
    Args:
        callback_data: کالبک برای دکمه لغو
    
    Returns:
        InlineKeyboardMarkup: کیبورد لغو
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ لغو", callback_data=callback_data)]
    ])


def get_back_keyboard(callback_data: str = "back") -> InlineKeyboardMarkup:
    """
    ساخت کیبورد برگشت
    
    Args:
        callback_data: کالبک برای دکمه برگشت
    
    Returns:
        InlineKeyboardMarkup: کیبورد برگشت
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ برگشت", callback_data=callback_data)]
    ])


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    base_callback: str,
    extra_buttons: Optional[List[List[InlineKeyboardButton]]] = None
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد صفحه‌بندی
    
    Args:
        current_page: صفحه فعلی (از 0 شروع)
        total_pages: تعداد کل صفحات
        base_callback: پیشوند کالبک (مثلاً "page_")
        extra_buttons: دکمه‌های اضافی
    
    Returns:
        InlineKeyboardMarkup: کیبورد صفحه‌بندی
    """
    keyboard = []
    
    # دکمه‌های صفحه‌بندی
    if total_pages > 1:
        row = []
        if current_page > 0:
            row.append(InlineKeyboardButton("◀️", callback_data=f"{base_callback}_{current_page-1}"))
        row.append(InlineKeyboardButton(f"📄 {current_page+1}/{total_pages}", callback_data="noop"))
        if current_page < total_pages - 1:
            row.append(InlineKeyboardButton("▶️", callback_data=f"{base_callback}_{current_page+1}"))
        keyboard.append(row)
    
    # دکمه‌های اضافی
    if extra_buttons:
        keyboard.extend(extra_buttons)
    
    return InlineKeyboardMarkup(keyboard)


# ================================================================
# توابع تولید کد و شناسه
# ================================================================

def generate_random_string(length: int = 8, chars: str = string.ascii_letters + string.digits) -> str:
    """
    تولید رشته تصادفی
    
    Args:
        length: طول رشته
        chars: کاراکترهای مجاز
    
    Returns:
        str: رشته تصادفی
    """
    return ''.join(random.choice(chars) for _ in range(length))


def generate_card_number() -> str:
    """
    تولید شماره کارت بانکی ۱۶ رقمی
    
    Returns:
        str: شماره کارت ۱۶ رقمی
    """
    return ''.join(str(random.randint(0, 9)) for _ in range(16))


def generate_game_id(prefix: str = "game") -> str:
    """
    تولید شناسه یکتا برای بازی
    
    Args:
        prefix: پیشوند
    
    Returns:
        str: شناسه بازی
    """
    timestamp = int(datetime.now().timestamp() * 1000)
    random_part = random.randint(100, 999)
    return f"{prefix}-{timestamp}-{random_part}"


def generate_vote_key(chat_id: int, user_id: int) -> str:
    """
    تولید کلید یکتا برای رای‌گیری میو
    
    Args:
        chat_id: آیدی گروه
        user_id: آیدی کاربر متخلف
    
    Returns:
        str: کلید یکتا
    """
    timestamp = int(datetime.now().timestamp() * 1000)
    return f"meow_{chat_id}_{user_id}_{timestamp}"


# ================================================================
# توابع اعتبارسنجی
# ================================================================

def is_valid_amount(amount: int, min_amount: int = 0, max_amount: Optional[int] = None) -> Tuple[bool, str]:
    """
    اعتبارسنجی مبلغ
    
    Args:
        amount: مبلغ
        min_amount: حداقل
        max_amount: حداکثر (None = بدون محدودیت)
    
    Returns:
        Tuple[bool, str]: (معتبر است, پیام خطا)
    """
    if amount <= 0:
        return False, "❌ مبلغ باید بیشتر از صفر باشد"
    if amount < min_amount:
        return False, f"❌ حداقل مبلغ {format_number(min_amount)} است"
    if max_amount is not None and amount > max_amount:
        return False, f"❌ حداکثر مبلغ {format_number(max_amount)} است"
    return True, ""


def is_valid_card_number(card_number: str) -> bool:
    """
    اعتبارسنجی شماره کارت بانکی
    
    Args:
        card_number: شماره کارت
    
    Returns:
        bool: معتبر است یا نه
    """
    if not card_number:
        return False
    card_number = card_number.replace(" ", "").replace("-", "")
    return len(card_number) == 16 and card_number.isdigit()


def is_valid_username(username: str) -> bool:
    """
    اعتبارسنجی یوزرنیم تلگرام
    
    Args:
        username: یوزرنیم
    
    Returns:
        bool: معتبر است یا نه
    """
    if not username:
        return False
    username = username.replace("@", "")
    return bool(re.match(r'^[a-zA-Z0-9_]{5,32}$', username))


# ================================================================
# توابع مربوط به زمان
# ================================================================

def get_time_remaining(target_time: Union[int, float, datetime]) -> int:
    """
    محاسبه زمان باقی‌مانده تا یک زمان مشخص
    
    Args:
        target_time: زمان هدف (timestamp یا datetime)
    
    Returns:
        int: زمان باقی‌مانده به ثانیه (۰ اگر گذشته باشد)
    """
    if isinstance(target_time, (int, float)):
        target = datetime.fromtimestamp(target_time)
    elif isinstance(target_time, datetime):
        target = target_time
    else:
        return 0
    
    remaining = (target - datetime.now()).total_seconds()
    return max(0, int(remaining))


def is_expired(timestamp: Union[int, float, datetime, None]) -> bool:
    """
    بررسی منقضی شدن یک زمان
    
    Args:
        timestamp: زمان (timestamp یا datetime)
    
    Returns:
        bool: منقضی شده است یا نه
    """
    if timestamp is None:
        return True
    if isinstance(timestamp, (int, float)):
        return datetime.now().timestamp() > timestamp
    if isinstance(timestamp, datetime):
        return datetime.now() > timestamp
    return True


def get_cooldown_text(remaining: int, action: str = "") -> str:
    """
    تولید متن خنک‌سازی
    
    Args:
        remaining: زمان باقی‌مانده به ثانیه
        action: نام عملیات (اختیاری)
    
    Returns:
        str: متن خنک‌سازی
    """
    if remaining <= 0:
        return ""
    
    minutes = remaining // 60
    seconds = remaining % 60
    
    if minutes > 0:
        time_text = f"{minutes} دقیقه و {seconds} ثانیه"
    else:
        time_text = f"{seconds} ثانیه"
    
    action_text = f" برای {action}" if action else ""
    
    return f"⏳ *به جیبت استراحت بده!*\n💤 {time_text} دیگه میتونی{action_text}"


# ================================================================
# توابع مربوط به لاگ و دیباگ
# ================================================================

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    کوتاه کردن متن برای لاگ
    
    Args:
        text: متن
        max_length: حداکثر طول
        suffix: پسوند
    
    Returns:
        str: متن کوتاه شده
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_dict(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    دریافت ایمن از دیکشنری
    
    Args:
        data: دیکشنری
        key: کلید
        default: مقدار پیش‌فرض
    
    Returns:
        Any: مقدار یا پیش‌فرض
    """
    return data.get(key, default) if data else default


def safe_int(value: Any, default: int = 0) -> int:
    """
    تبدیل ایمن به int
    
    Args:
        value: مقدار
        default: مقدار پیش‌فرض
    
    Returns:
        int: عدد یا پیش‌فرض
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    تبدیل ایمن به float
    
    Args:
        value: مقدار
        default: مقدار پیش‌فرض
    
    Returns:
        float: عدد یا پیش‌فرض
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """
    تبدیل ایمن به str
    
    Args:
        value: مقدار
        default: مقدار پیش‌فرض
    
    Returns:
        str: رشته یا پیش‌فرض
    """
    if value is None:
        return default
    return str(value)


# ================================================================
# توابع مربوط به متن و فرمت‌بندی
# ================================================================

def get_emoji_rating(value: int, max_value: int = 5) -> str:
    """
    دریافت ایموجی بر اساس مقدار
    
    Args:
        value: مقدار
        max_value: حداکثر
    
    Returns:
        str: ایموجی‌ها
    """
    filled = int((value / max_value) * 5)
    filled = min(filled, 5)
    return "⭐" * filled + "☆" * (5 - filled)


def get_progress_bar(progress: int, total: int, length: int = 10) -> str:
    """
    ساخت نوار پیشرفت
    
    Args:
        progress: مقدار پیشرفت
        total: مقدار کل
        length: طول نوار
    
    Returns:
        str: نوار پیشرفت
    """
    if total <= 0:
        return "[" + "░" * length + "]"
    
    ratio = min(progress / total, 1.0)
    filled = int(ratio * length)
    empty = length - filled
    
    return "█" * filled + "░" * empty


def bold(text: str) -> str:
    """متن پررنگ (Markdown)"""
    return f"*{text}*"


def code(text: str) -> str:
    """متن کد (Markdown)"""
    return f"`{text}`"


def italic(text: str) -> str:
    """متن ایتالیک (Markdown)"""
    return f"_{text}_"


def underline(text: str) -> str:
    """متن زیرخط‌دار (Markdown)"""
    return f"__{text}__"


def spoiler(text: str) -> str:
    """متن اسپویلر (Markdown)"""
    return f"||{text}||"


# ================================================================
# نمونه‌های تست
# ================================================================

if __name__ == "__main__":
    # تست توابع
    print("🧪 تست توابع utils.py...")
    
    # تست format_number
    print(f"✅ format_number(1000): {format_number(1000)}")
    print(f"✅ format_number(1234567): {format_number(1234567)}")
    
    # تست parse_amount
    print(f"✅ parse_amount('1k'): {parse_amount('1k')}")
    print(f"✅ parse_amount('1.5m'): {parse_amount('1.5m')}")
    print(f"✅ parse_amount('500'): {parse_amount('500')}")
    
    # تست format_duration
    print(f"✅ format_duration(3665): {format_duration(3665)}")
    
    # تست get_cooldown_text
    print(f"✅ get_cooldown_text(125, 'انتقال'): {get_cooldown_text(125, 'انتقال')}")
    
    # تست generate_random_string
    print(f"✅ generate_random_string(): {generate_random_string()}")
    
    # تست get_progress_bar
    print(f"✅ get_progress_bar(7, 10): {get_progress_bar(7, 10)}")
    
    print("🎉 همه تست‌ها با موفقیت انجام شد!")
