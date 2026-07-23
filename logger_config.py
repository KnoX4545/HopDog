# logger_config.py - تنظیمات پیشرفته لاگ (نسخه کامل)

import logging
import sys
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# ================================================================
# کلاس فرمت‌کننده سفارشی با رنگ
# ================================================================

class CustomFormatter(logging.Formatter):
    """فرمت‌کننده سفارشی لاگ با رنگ و زمان"""
    
    # رنگ‌ها
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    blue = "\x1b[34;20m"
    cyan = "\x1b[36;20m"
    magenta = "\x1b[35;20m"
    reset = "\x1b[0m"
    
    # فرمت‌های مختلف برای سطوح مختلف
    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: blue + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
    }
    
    # فرمت‌های خاص برای لاگ‌های تراکنش و امنیت
    TRANSACTION_FORMAT = green + "%(asctime)s - 💰 %(message)s" + reset
    SECURITY_FORMAT = magenta + "%(asctime)s - 🔒 %(message)s" + reset
    GAME_FORMAT = cyan + "%(asctime)s - 🎮 %(message)s" + reset
    
    def format(self, record):
        # برای لاگ‌های تراکنش
        if hasattr(record, 'transaction') and record.transaction:
            formatter = logging.Formatter(self.TRANSACTION_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
            return formatter.format(record)
        
        # برای لاگ‌های امنیتی
        if hasattr(record, 'security') and record.security:
            formatter = logging.Formatter(self.SECURITY_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
            return formatter.format(record)
        
        # برای لاگ‌های بازی
        if hasattr(record, 'game') and record.game:
            formatter = logging.Formatter(self.GAME_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
            return formatter.format(record)
        
        # لاگ‌های عادی
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


# ================================================================
# کلاس فیلتر برای لاگ‌های خاص
# ================================================================

class TransactionFilter(logging.Filter):
    """فیلتر برای لاگ‌های تراکنش"""
    def filter(self, record):
        return hasattr(record, 'transaction') and record.transaction


class SecurityFilter(logging.Filter):
    """فیلتر برای لاگ‌های امنیتی"""
    def filter(self, record):
        return hasattr(record, 'security') and record.security


class GameFilter(logging.Filter):
    """فیلتر برای لاگ‌های بازی"""
    def filter(self, record):
        return hasattr(record, 'game') and record.game


# ================================================================
# تابع اصلی تنظیمات لاگ
# ================================================================

def setup_logging():
    """
    تنظیمات کامل لاگینگ
    
    Returns:
        tuple: (root_logger, transaction_logger, security_logger, game_logger)
    """
    
    # ======== ایجاد پوشه logs ========
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # ======== تنظیم لاگر اصلی ========
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # حذف هندلرهای قبلی
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # ======== هندلر کنسول (رنگی) ========
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # ======== هندلر فایل اصلی (چرخشی) ========
    # هر فایل تا 10MB و حداکثر 5 فایل بکاپ
    file_handler = RotatingFileHandler(
        f"logs/hopdog_{datetime.now().strftime('%Y%m%d')}.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    
    # ======== هندلر خطاها (فایل جداگانه) ========
    error_handler = RotatingFileHandler(
        "logs/errors.log",
        maxBytes=5_000_000,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root_logger.addHandler(error_handler)
    
    # ================================================================
    # لاگر تراکنش‌ها (مالی)
    # ================================================================
    
    transaction_logger = logging.getLogger("transactions")
    transaction_logger.setLevel(logging.INFO)
    transaction_logger.propagate = False  # جلوگیری از دوبار لاگ شدن
    
    transaction_handler = RotatingFileHandler(
        "logs/transactions.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    transaction_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    transaction_handler.addFilter(TransactionFilter())
    transaction_logger.addHandler(transaction_handler)
    
    # لاگ تراکنش‌ها در کنسول (با رنگ سبز)
    transaction_console = logging.StreamHandler(sys.stdout)
    transaction_console.setFormatter(CustomFormatter())
    transaction_console.addFilter(TransactionFilter())
    transaction_logger.addHandler(transaction_console)
    
    # ================================================================
    # لاگر امنیتی
    # ================================================================
    
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    security_handler = RotatingFileHandler(
        "logs/security.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    security_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    security_handler.addFilter(SecurityFilter())
    security_logger.addHandler(security_handler)
    
    # لاگ امنیتی در کنسول (با رنگ بنفش)
    security_console = logging.StreamHandler(sys.stdout)
    security_console.setFormatter(CustomFormatter())
    security_console.addFilter(SecurityFilter())
    security_logger.addHandler(security_console)
    
    # ================================================================
    # لاگر بازی‌ها
    # ================================================================
    
    game_logger = logging.getLogger("game")
    game_logger.setLevel(logging.INFO)
    game_logger.propagate = False
    
    game_handler = RotatingFileHandler(
        "logs/games.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    game_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    game_handler.addFilter(GameFilter())
    game_logger.addHandler(game_handler)
    
    # لاگ بازی در کنسول (با رنگ فیروزه‌ای)
    game_console = logging.StreamHandler(sys.stdout)
    game_console.setFormatter(CustomFormatter())
    game_console.addFilter(GameFilter())
    game_logger.addHandler(game_console)
    
    # ================================================================
    # لاگر دیتابیس
    # ================================================================
    
    db_logger = logging.getLogger("database")
    db_logger.setLevel(logging.INFO)
    db_logger.propagate = False
    
    db_handler = RotatingFileHandler(
        "logs/database.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    db_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    db_logger.addHandler(db_handler)
    
    # ================================================================
    # لاگ‌های اولیه
    # ================================================================
    
    root_logger.info("=" * 60)
    root_logger.info("🚀 سیستم لاگینگ راه‌اندازی شد")
    root_logger.info(f"📁 پوشه لاگ: logs/")
    root_logger.info(f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    root_logger.info("=" * 60)
    
    return root_logger, transaction_logger, security_logger, game_logger, db_logger


# ================================================================
# توابع کمکی برای لاگ کردن
# ================================================================

def log_transaction(user_id, action, amount, details="", success=True):
    """
    لاگ تراکنش‌های مالی
    
    Args:
        user_id: آیدی کاربر
        action: نوع عملیات (واریز, برداشت, انتقال, خرید)
        amount: مبلغ
        details: جزئیات اضافی
        success: موفقیت‌آمیز بودن
    """
    logger = logging.getLogger("transactions")
    status = "✅" if success else "❌"
    logger.info(
        f"{status} | {user_id} | {action} | {amount:,} 🪙 | {details}",
        extra={'transaction': True}
    )


def log_security(user_id, action, details="", level="INFO"):
    """
    لاگ رویدادهای امنیتی
    
    Args:
        user_id: آیدی کاربر
        action: نوع عملیات (تغییر سطح, زندانی کردن, ریست)
        details: جزئیات اضافی
        level: سطح اهمیت (INFO, WARNING, ERROR)
    """
    logger = logging.getLogger("security")
    
    if level == "WARNING":
        logger.warning(
            f"{user_id} | {action} | {details}",
            extra={'security': True}
        )
    elif level == "ERROR":
        logger.error(
            f"{user_id} | {action} | {details}",
            extra={'security': True}
        )
    else:
        logger.info(
            f"{user_id} | {action} | {details}",
            extra={'security': True}
        )


def log_game(game_id, event, details="", user_id=None):
    """
    لاگ رویدادهای بازی
    
    Args:
        game_id: آیدی بازی
        event: نوع رویداد (ساخت, پیوستن, حرکت, پایان)
        details: جزئیات اضافی
        user_id: آیدی کاربر (اختیاری)
    """
    logger = logging.getLogger("game")
    
    user_part = f" | {user_id}" if user_id else ""
    logger.info(
        f"{game_id} | {event}{user_part} | {details}",
        extra={'game': True}
    )


def log_db(operation, table, user_id=None, details=""):
    """
    لاگ عملیات دیتابیس
    
    Args:
        operation: نوع عملیات (SELECT, INSERT, UPDATE, DELETE)
        table: نام جدول
        user_id: آیدی کاربر (اختیاری)
        details: جزئیات اضافی
    """
    logger = logging.getLogger("database")
    user_part = f" | {user_id}" if user_id else ""
    logger.info(f"{operation} | {table}{user_part} | {details}")


def log_error(error, context="", user_id=None):
    """
    لاگ خطاها با جزئیات کامل
    
    Args:
        error: خطا
        context: زمینه خطا
        user_id: آیدی کاربر (اختیاری)
    """
    logger = logging.getLogger()
    user_part = f" | {user_id}" if user_id else ""
    logger.error(f"❌ {context}{user_part}: {str(error)}", exc_info=True)


# ================================================================
# لاگ‌های آماری (هر ساعت)
# ================================================================

def log_stats(user_count, game_count, group_count):
    """
    لاگ آمار کلی سیستم
    
    Args:
        user_count: تعداد کاربران فعال
        game_count: تعداد بازی‌های فعال
        group_count: تعداد گروه‌های فعال
    """
    logger = logging.getLogger()
    logger.info(
        f"📊 آمار سیستم | "
        f"کاربران: {user_count} | "
        f"بازی‌ها: {game_count} | "
        f"گروه‌ها: {group_count}"
    )


# ================================================================
# نمونه‌های جهانی لاگرها
# ================================================================

# اینها بعد از فراخوانی setup_logging() مقداردهی میشن
root_logger = None
transaction_logger = None
security_logger = None
game_logger = None
db_logger = None


def init_logging():
    """مقداردهی اولیه لاگرهای جهانی"""
    global root_logger, transaction_logger, security_logger, game_logger, db_logger
    root_logger, transaction_logger, security_logger, game_logger, db_logger = setup_logging()
    return root_logger, transaction_logger, security_logger, game_logger, db_logger


# ================================================================
# اگر فایل مستقیم اجرا شد، تست کن
# ================================================================

if __name__ == "__main__":
    # تست لاگ‌ها
    root, trans, sec, game, db = setup_logging()
    
    root.info("🧪 تست لاگ معمولی")
    root.warning("⚠️ تست لاگ هشدار")
    root.error("❌ تست لاگ خطا")
    
    log_transaction(123456789, "انتقال", 5000, "به کاربر 987654321")
    log_security(123456789, "تغییر سطح", "کاربر 987654321 به سطح 5")
    log_game("game_123", "ساخت", "مبلغ: 1000", 123456789)
    log_db("UPDATE", "users", 123456789, "سطح به 5 تغییر کرد")
    
    root.info("✅ همه تست‌ها با موفقیت انجام شد!")
