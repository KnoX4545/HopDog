# academy.py - متن‌های آکادمی (نسخه کامل با اصلاحات)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils import format_number, format_duration
from logger_config import log_game, log_error
from globals import get_game

import logging
logger = logging.getLogger(__name__)


# ================================================================
# متن‌های آکادمی
# ================================================================

ACADEMY_MAIN = """🏫 *آکادمی هاپویی* ✨

🐾 جایی که هاپوهای کنجکاو جواب سوال‌هاشون رو پیدا میکنن

چنل رسمی هاپویی: @HopDogQ

لطفا بخش مورد نظر را انتخاب کنید ⬇️"""

ACADEMY_SUB_SYSTEM = """📚 *آکادمی هاپویی* ✨
┘─ 🐾 *بخش : سیستم هاپویی* ⚙️

لطفا بخش مورد نظر را انتخاب کنید ⬇️"""

ACADEMY_SUB_FEATURES = """📚 *آکادمی هاپویی* ✨
┘─ 🐾 *بخش : قابلیت های هاپویی* ✨

لطفا بخش مورد نظر را انتخاب کنید ⬇️"""

ACADEMY_SUB_ADVENTURE = """📚 *آکادمی هاپویی* ✨
┘─ 🐾 *بخش : شروع ماجراجویی* 🐾

لطفا بخش مورد نظر را انتخاب کنید ⬇️"""


# ================================================================
# متن‌های سیستم هاپویی
# ================================================================

ACADEMY_SYSTEM_PAGE1 = """📚 *آکادمی هاپویی* ✨
┘─ 🐾 *بخش : سیستم هاپویی* ⚙️
┘─ 📚 *مطلب : سطح کاربران* 🐾

✨ *لیست سطح های موجود کاربران* ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ *سطح 1*
┘─ 💰 پوینت : 5 - 15 🪙
┘─ ⏳ زمان : 5:00
┘─ 🔓 قابلیت ها : شروع
〰️〰️〰️〰️〰️〰️〰️
⭐️ *سطح 2*
┘─ 🐾 هاپ مورد نیاز : 5
┘─ 💰 پوینت : 10 - 20 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 50 🪙
┘─ 🔓 قابلیت ها : پنجه، شکار، دریافت هاپو پوینت
〰️〰️〰️〰️〰️〰️〰️
⭐️ *سطح 3*
┘─ 🐾 هاپ مورد نیاز : 15
┘─ 💰 پوینت : 15 - 25 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 225 🪙
┘─ 🔓 قابلیت ها : هاپو، انتقال هاپویی
〰️〰️〰️〰️〰️〰️〰️
⭐️ *سطح 4*
┘─ 🐾 هاپ مورد نیاز : 40
┘─ 💰 پوینت : 20 - 35 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 500 🪙
┘─ 🔓 قابلیت ها : بانک هاپویی
〰️〰️〰️〰️〰️〰️〰️
⭐️ *سطح 5*
┘─ 🐾 هاپ مورد نیاز : 75
┘─ 💰 پوینت : 25 - 40 🪙
┘─ ⏳ زمان : 4:55
┘─ 💝 جایزه ارتقا : 1000 🪙
┘─ 🔓 قابلیت ها : یخچال هاپویی، ارتقا بیشتر"""

# ... بقیه متن‌ها به همین شکل ادامه دارن ...


# ================================================================
# توابع آکادمی (با اصلاحات)
# ================================================================

async def show_academy_main(update, query=None):
    """
    نمایش منوی اصلی آکادمی
    
    Args:
        update: آبجکت آپدیت
        query: کالبک کوئری (اختیاری)
    """
    keyboard = [
        [
            InlineKeyboardButton("📚 سیستم هاپویی", callback_data="academy_system_menu"),
            InlineKeyboardButton("🔓 قابلیت ها", callback_data="academy_features_menu")
        ],
        [
            InlineKeyboardButton("🚀 شروع ماجراجویی", callback_data="academy_adventure_menu")
        ]
    ]
    
    try:
        if query:
            await query.edit_message_text(
                ACADEMY_MAIN, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                ACADEMY_MAIN, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        logger.info(f"📚 آکادمی برای {update.effective_user.id if update.effective_user else 'نامشخص'} نمایش داده شد")
    except Exception as e:
        logger.error(f"❌ خطا در نمایش آکادمی: {e}")
        log_error(e, "نمایش آکادمی")


async def show_academy_system_menu(update, query=None):
    """نمایش منوی سیستم هاپویی"""
    keyboard = [
        [
            InlineKeyboardButton("⭐ سطح کاربران", callback_data="academy_system_page1"),
            InlineKeyboardButton("🐾 حیوانات", callback_data="academy_animals_page1")
        ],
        [
            InlineKeyboardButton("🐾 سطح پنجه", callback_data="academy_claw_page1"),
            InlineKeyboardButton("◀️ برگشت", callback_data="academy_back_main")
        ]
    ]
    
    try:
        if query:
            await query.edit_message_text(
                ACADEMY_SUB_SYSTEM, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                ACADEMY_SUB_SYSTEM, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش منوی سیستم: {e}")
        log_error(e, "نمایش منوی سیستم هاپویی")


async def show_academy_features_menu(update, query=None):
    """نمایش منوی قابلیت‌ها"""
    keyboard = [
        [
            InlineKeyboardButton("🐕 هاپو", callback_data="academy_hapo"),
            InlineKeyboardButton("🏹 شکار", callback_data="academy_hunt")
        ],
        [
            InlineKeyboardButton("🏦 بانک هاپویی", callback_data="academy_bank"),
            InlineKeyboardButton("🧲 انتقال هاپویی", callback_data="academy_transfer")
        ],
        [
            InlineKeyboardButton("⛓️ زندان هاپویی", callback_data="academy_jail"),
            InlineKeyboardButton("🐶 هاپوی خیابونی", callback_data="academy_street_hapo")
        ],
        [
            InlineKeyboardButton("❄️ یخچال هاپویی", callback_data="academy_fridge"),
            InlineKeyboardButton("🥷 قاچاق هاپویی", callback_data="academy_smuggle")
        ],
        [
            InlineKeyboardButton("🏆 لیدربرد هاپویی", callback_data="academy_leaderboard"),
            InlineKeyboardButton("🕹 بازی هاپویی", callback_data="academy_games_menu")
        ],
        [
            InlineKeyboardButton("◀️ برگشت", callback_data="academy_back_main")
        ]
    ]
    
    try:
        if query:
            await query.edit_message_text(
                ACADEMY_SUB_FEATURES, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                ACADEMY_SUB_FEATURES, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش منوی قابلیت‌ها: {e}")
        log_error(e, "نمایش منوی قابلیت‌ها")


async def show_academy_adventure_menu(update, query=None):
    """نمایش منوی شروع ماجراجویی"""
    keyboard = [
        [
            InlineKeyboardButton("🐾 هاپ هاپ", callback_data="academy_hop"),
            InlineKeyboardButton("🪙 هاپو پوینت", callback_data="academy_points")
        ],
        [
            InlineKeyboardButton("⭐ تجربه و سطح", callback_data="academy_exp"),
            InlineKeyboardButton("🪪 پروفایل", callback_data="academy_profile")
        ],
        [
            InlineKeyboardButton("◀️ برگشت", callback_data="academy_back_main")
        ]
    ]
    
    try:
        if query:
            await query.edit_message_text(
                ACADEMY_SUB_ADVENTURE, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                ACADEMY_SUB_ADVENTURE, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش منوی ماجراجویی: {e}")
        log_error(e, "نمایش منوی ماجراجویی")


# ================================================================
# توابع نمایش صفحه‌بندی
# ================================================================

async def show_academy_system_pages(update, query, page):
    """نمایش صفحات سیستم هاپویی"""
    pages = {
        1: ACADEMY_SYSTEM_PAGE1,
        2: ACADEMY_SYSTEM_PAGE2,
        3: ACADEMY_SYSTEM_PAGE3,
        4: ACADEMY_SYSTEM_PAGE4
    }
    
    keyboard = []
    if page > 1:
        keyboard.append(InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_system_page{page-1}"))
    if page < 4:
        if keyboard:
            keyboard.append(InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_system_page{page+1}"))
        else:
            keyboard = [InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_system_page{page+1}")]
    
    if page == 4 and page > 1:
        keyboard = [InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_system_page{page-1}")]
    elif page == 1 and page < 4:
        keyboard = [InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_system_page{page+1}")]
    elif 1 < page < 4:
        keyboard = [
            InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_system_page{page-1}"),
            InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_system_page{page+1}")
        ]
    
    keyboard.append(InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu"))
    
    try:
        await query.edit_message_text(
            pages.get(page, ACADEMY_SYSTEM_PAGE1),
            reply_markup=InlineKeyboardMarkup([keyboard]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش صفحه {page} سیستم: {e}")
        log_error(e, f"نمایش صفحه {page} سیستم")


# ================================================================
# توابع مشابه برای animals و claw
# ================================================================

async def show_academy_animals_pages(update, query, page):
    """نمایش صفحات حیوانات"""
    pages = {
        1: ACADEMY_ANIMALS_PAGE1,
        2: ACADEMY_ANIMALS_PAGE2,
        3: ACADEMY_ANIMALS_PAGE3
    }
    
    keyboard = []
    if page > 1:
        keyboard.append(InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_animals_page{page-1}"))
    if page < 3:
        if keyboard:
            keyboard.append(InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_animals_page{page+1}"))
        else:
            keyboard = [InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_animals_page{page+1}")]
    
    if page == 3 and page > 1:
        keyboard = [InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_animals_page{page-1}")]
    elif page == 1 and page < 3:
        keyboard = [InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_animals_page{page+1}")]
    elif 1 < page < 3:
        keyboard = [
            InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_animals_page{page-1}"),
            InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_animals_page{page+1}")
        ]
    
    keyboard.append(InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu"))
    
    try:
        await query.edit_message_text(
            pages.get(page, ACADEMY_ANIMALS_PAGE1),
            reply_markup=InlineKeyboardMarkup([keyboard]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش صفحه {page} حیوانات: {e}")
        log_error(e, f"نمایش صفحه {page} حیوانات")


async def show_academy_claw_pages(update, query, page):
    """نمایش صفحات پنجه"""
    pages = {
        1: ACADEMY_CLAW_PAGE1,
        2: ACADEMY_CLAW_PAGE2,
        3: ACADEMY_CLAW_PAGE3
    }
    
    keyboard = []
    if page > 1:
        keyboard.append(InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_claw_page{page-1}"))
    if page < 3:
        if keyboard:
            keyboard.append(InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_claw_page{page+1}"))
        else:
            keyboard = [InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_claw_page{page+1}")]
    
    if page == 3 and page > 1:
        keyboard = [InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_claw_page{page-1}")]
    elif page == 1 and page < 3:
        keyboard = [InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_claw_page{page+1}")]
    elif 1 < page < 3:
        keyboard = [
            InlineKeyboardButton("◀️ صفحه قبل", callback_data=f"academy_claw_page{page-1}"),
            InlineKeyboardButton("▶️ صفحه بعد", callback_data=f"academy_claw_page{page+1}")
        ]
    
    keyboard.append(InlineKeyboardButton("◀️ برگشت", callback_data="academy_system_menu"))
    
    try:
        await query.edit_message_text(
            pages.get(page, ACADEMY_CLAW_PAGE1),
            reply_markup=InlineKeyboardMarkup([keyboard]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش صفحه {page} پنجه: {e}")
        log_error(e, f"نمایش صفحه {page} پنجه")


async def show_feature_page(update, query, feature):
    """نمایش صفحات قابلیت‌ها"""
    pages = {
        "hapo": ACADEMY_HAPO,
        "hunt": ACADEMY_HUNT,
        "bank": ACADEMY_BANK,
        "transfer": ACADEMY_TRANSFER,
        "jail": ACADEMY_JAIL,
        "street_hapo": ACADEMY_STREET_HAPO,
        "fridge": ACADEMY_FRIDGE,
        "smuggle": ACADEMY_SMUGGLE,
        "leaderboard": ACADEMY_LEADERBOARD
    }
    
    keyboard = [[InlineKeyboardButton("◀️ برگشت", callback_data="academy_features_menu")]]
    
    try:
        await query.edit_message_text(
            pages.get(feature, ACADEMY_HAPO),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش صفحه {feature}: {e}")
        log_error(e, f"نمایش صفحه {feature}")


async def show_adventure_page(update, query, page):
    """نمایش صفحات ماجراجویی"""
    pages = {
        "hop": ACADEMY_HOP,
        "points": ACADEMY_POINTS,
        "exp": ACADEMY_EXP,
        "profile": ACADEMY_PROFILE
    }
    
    keyboard = [[InlineKeyboardButton("◀️ برگشت", callback_data="academy_adventure_menu")]]
    
    try:
        await query.edit_message_text(
            pages.get(page, ACADEMY_HOP),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش صفحه {page}: {e}")
        log_error(e, f"نمایش صفحه {page}")


async def show_street_hapo_page(update, query):
    """نمایش صفحه هاپوی خیابونی"""
    keyboard = [[InlineKeyboardButton("◀️ برگشت", callback_data="academy_features_menu")]]
    
    try:
        await query.edit_message_text(
            ACADEMY_STREET_HAPO,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش صفحه هاپوی خیابونی: {e}")
        log_error(e, "نمایش صفحه هاپوی خیابونی")


async def show_academy_games_menu(update, query=None):
    """نمایش منوی بازی‌ها"""
    keyboard = [
        [InlineKeyboardButton("🧩 بازی XO", callback_data="academy_game_xo")],
        [InlineKeyboardButton("◀️ برگشت", callback_data="academy_features_menu")]
    ]
    
    msg = """🕹 *بازی های هاپویی* 🐶

❗️ لطفا بازی مورد نظر را انتخاب کنید ⬇️

🧩 *بازی میویی XO*
┘─ محدودیت بازیکن : 2 هاپو"""
    
    try:
        if query:
            await query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش منوی بازی‌ها: {e}")
        log_error(e, "نمایش منوی بازی‌ها")


async def show_academy_game_xo(update, query=None):
    """نمایش توضیحات بازی XO"""
    keyboard = [[InlineKeyboardButton("◀️ برگشت", callback_data="academy_games_menu")]]
    
    try:
        if query:
            await query.edit_message_text(
                ACADEMY_GAMES_XO,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                ACADEMY_GAMES_XO,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"❌ خطا در نمایش توضیحات XO: {e}")
        log_error(e, "نمایش توضیحات XO")
