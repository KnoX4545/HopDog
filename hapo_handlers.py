# hapo_handlers.py - هندلرهای هاپو، پنجه، شکار، اسم هاپو

import asyncio
import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    RANK_NAMES, CLAW_IMAGES, MAX_CLAW_LEVEL, HUNT_DECISION_TIMER,
    FRIDGE_REQUIRED_LEVEL, FRIDGE_PURCHASE_COST, FRIDGE_MAX_LEVEL,
    FRIDGE_CAPACITY, FRIDGE_UPGRADE_COSTS, FRIDGE_COOK_MULTIPLIER_SELL,
    FRIDGE_COOK_MULTIPLIER_FOOD, HAPO_NAMES, MAX_LEVEL
)
from globals import get_game, set_xo_state, get_xo_state, clear_xo_state
from utils import format_number, parse_amount, get_confirm_keyboard
from logger_config import log_transaction, log_error, log_game
from database import supabase

logger = logging.getLogger(__name__)


# ================================================================
# ✅ لیست کلمات ممنوع برای اسم هاپو (فقط فحش‌های خیلی رکیک)
# ================================================================

FORBIDDEN_HAPO_NAMES = [
    "کیر", "کص", "کس", "کون", "کصکش", "کسکش",
    "جنده", "حروم", "حرومزاده"
]


def is_valid_hapo_name(name: str) -> tuple:
    """
    اعتبارسنجی اسم هاپو - فقط فحش‌های خیلی رکیک ممنوع
    
    Args:
        name: اسم پیشنهادی
    
    Returns:
        tuple: (معتبر است, پیام خطا)
    """
    name = name.strip()
    
    # بررسی طول
    if len(name) < 1 or len(name) > 30:
        return False, "❌ اسم هاپو باید بین ۱ تا ۳۰ کاراکتر باشد"
    
    # بررسی کاراکترهای مجاز (فقط حروف و اعداد و فاصله)
    if not re.match(r'^[\u0600-\u06FF\uFB8A\u067E\u0686\u06AF\u2000-\u200F\u202A-\u202E\uFEFFa-zA-Z0-9\s\-_\.]+$', name):
        return False, "❌ اسم هاپو فقط می‌تواند شامل حروف، اعداد و فاصله باشد"
    
    # ✅ فقط فحش‌های خیلی رکیک ممنوع
    name_lower = name.lower().strip()
    
    for bad in FORBIDDEN_HAPO_NAMES:
        if bad in name_lower:
            return False, f"❌ اسم «{name}» مجاز نیست. لطفاً اسم دیگری انتخاب کن."
    
    # بررسی کلمات ترکیبی با فحش
    bad_patterns = [
        r'ک[صس]', r'ک[صس]کش', r'کیر', r'کون',
        r'جنده', r'حروم'
    ]
    for pattern in bad_patterns:
        if re.search(pattern, name_lower):
            return False, f"❌ اسم «{name}» مجاز نیست. لطفاً اسم دیگری انتخاب کن."
    
    return True, ""


def contains_bad_word(text: str) -> bool:
    """چک کردن سریع وجود فحش در متن"""
    text = text.lower()
    for bad in FORBIDDEN_HAPO_NAMES:
        if bad in text:
            return True
    return False


# ================================================================
# متن و کیبورد منوی هاپو
# ================================================================

def get_hapo_menu_text(game):
    """دریافت متن منوی هاپو با نمایش وضعیت «کار نمیکنم»"""
    game.update_hapo_production()
    total = game.get_hapo_total_level()
    max_food = game.get_hapo_max_food()
    capacity = game.get_hapo_capacity()
    status = game.get_hapo_food_status()
    prod = game.get_hapo_production()
    is_max = total >= 20
    hapo_rank = game._to_int(game.data["hapo_rank"])
    hapo_level = game._to_int(game.data["hapo_level"])
    hapo_food = game._to_int(game.data["hapo_food"])
    hapo_harvest = game._to_int(game.data["hapo_harvest"])
    hop_point = game._to_int(game.data["hop_point"])
    
    msg = f"🐶 *{game.data['hapo_name']}*\n"
    msg += f"💕 نام : {game.data['hapo_name']}\n"
    
    # ✅ نمایش وضعیت غذا با پیام "کار نمیکنم"
    if hapo_food == 0:
        msg += f"🍖 شکم : 😢 کار نمیکنم... (۰/{max_food})\n"
    else:
        msg += f"🍖 شکم : {status['text']} ({hapo_food}/{max_food})\n"
    
    msg += f"🌟 مقام : {RANK_NAMES[hapo_rank]}\n"
    msg += f"⭐️ سطح : {hapo_level}/5\n"
    msg += f"💰 هاپو پوینت های تولید شده : {format_number(hapo_harvest)} 🪙\n"
    
    # ✅ اگر غذا ۰ باشد، تولید ۰ نمایش داده می‌شود
    if hapo_food == 0:
        msg += f"💫 تولید هاپو پوینت در ثانیه : ۰ 🪙 *(گرسنه‌ام!)*\n"
    else:
        msg += f"💫 تولید هاپو پوینت در ثانیه : {prod:.2f} 🪙\n"
    
    msg += f"📦 ظرفیت : {format_number(capacity)}\n"
    msg += f"💰 *هاپو پوینت هات :* {format_number(hop_point)} 🪙\n"
    
    if is_max:
        msg += "🏆 مقام نهایی"
    elif hapo_level >= 5 and hapo_rank < 4:
        rank_price = game.get_hapo_rank_up_price()
        msg += f"💰 هزینه ارتقا مقام : {format_number(rank_price)} 🪙"
    else:
        price = game.get_hapo_upgrade_price()
        msg += f"💰 هزینه ارتقا سطح : {format_number(price)} 🪙"
    
    # ✅ اگر هاپو گرسنه است، پیام اضافه
    if hapo_food == 0:
        msg += "\n\n😢 *هاپو گرسنه است! بهش غذا بده تا دوباره کار کنه* 🍖"
    
    return msg


def get_hapo_menu_keyboard(game):
    """دریافت کیبورد منوی هاپو"""
    keyboard = [
        [InlineKeyboardButton("💰 برداشت", callback_data="hapo_harvest")],
    ]
    total = game.get_hapo_total_level()
    is_max = total >= 20
    hapo_level = game._to_int(game.data["hapo_level"])
    hapo_rank = game._to_int(game.data["hapo_rank"])
    max_level = game.get_hapo_max_level_for_rank(hapo_rank)
    hapo_food = game._to_int(game.data["hapo_food"])
    
    # ✅ اگر غذا ۰ است، دکمه غذا دادن نمایش داده شود
    if hapo_food == 0:
        keyboard.append([InlineKeyboardButton("🍖 غذا دادن به هاپو", callback_data="hapo_feed_show")])
    elif is_max:
        keyboard[0].append(InlineKeyboardButton("🏆 نهایی", callback_data="hapo_max"))
    elif hapo_level >= max_level and hapo_rank < 4:
        price = game.get_hapo_rank_up_price()
        if price != float('inf'):
            keyboard.append([InlineKeyboardButton(f"🌟 ارتقا مقام ({format_number(price)})", callback_data="hapo_rank_up_confirm")])
    else:
        price = game.get_hapo_upgrade_price()
        if price != float('inf'):
            keyboard.append([InlineKeyboardButton(f"⬆️ ارتقا سطح ({format_number(price)})", callback_data="hapo_level_up")])
    
    hop_point = game._to_int(game.data["hop_point"])
    if hop_point >= 750:
        keyboard.append([InlineKeyboardButton("✏️ تغییر اسم هاپو", callback_data="hapo_rename")])
    
    return InlineKeyboardMarkup(keyboard)


# ================================================================
# منوی اصلی هاپو
# ================================================================

async def show_hapo_menu(update: Update, game):
    if game.is_jailed():
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "⛓️ *شما در زندان هستید.*\n\n"
                "📌 *دستورات مجاز در زندان:*\n"
                "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
                "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "⛓️ *شما در زندان هستید.*\n\n"
                "📌 *دستورات مجاز در زندان:*\n"
                "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
                "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
                parse_mode="Markdown"
            )
        return
    
    if not game.data["hapo_owned"]:
        level = game._to_int(game.data["level"])
        if level < 3:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "🐕 *هاپو از سطح 3 باز میشود*",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "🐕 *هاپو از سطح 3 باز میشود*",
                    parse_mode="Markdown"
                )
            return
        
        hop_point = game._to_int(game.data["hop_point"])
        if hop_point < 300:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    f"🐕 *برای خرید هاپو به 300 هاپو پوینت نیاز داری*\n"
                    f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"🐕 *برای خرید هاپو به 300 هاپو پوینت نیاز داری*\n"
                    f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                    parse_mode="Markdown"
                )
            return
        
        keyboard = [[InlineKeyboardButton(f"🐕 خرید هاپو (300 هاپو پوینت)", callback_data="buy_hapo")]]
        if update.callback_query:
            await update.callback_query.edit_message_text(
                f"🐕 *آیا میخوای هاپو بخری؟*\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"🐕 *آیا میخوای هاپو بخری؟*\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        return
    
    try:
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                msg,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                msg,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error in show_hapo_menu: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "🐕 *هاپو*\n\n❌ *خطا در نمایش منوی هاپو. لطفاً دوباره تلاش کنید.*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🐕 *هاپو*\n\n❌ *خطا در نمایش منوی هاپو. لطفاً دوباره تلاش کنید.*",
                parse_mode="Markdown"
            )


# ================================================================
# منوی غذا دادن به هاپو
# ================================================================

async def show_hapo_feed_menu(update, game, query=None):
    """نمایش گزینه‌های غذا دادن به هاپو"""
    hapo_food = game._to_int(game.data["hapo_food"])
    
    if hapo_food > 0:
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        if query:
            await query.edit_message_text(
                f"🍖 *هاپو سیر است!*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"🍖 *هاپو سیر است!*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        return
    
    # بررسی وجود حیوان در حال شکار
    animal = game.data.get("current_hunt_animal")
    if animal:
        msg = f"🍖 *یک حیوان برای غذا دادن داری!*\n\n"
        msg += f"{animal['emoji']} *{animal['name']}*\n"
        msg += f"⭐ *سطح :* {animal['rarity_name']}\n"
        msg += f"🍖 *ارزش غذایی :* {animal['nutrition']} کالری\n\n"
        msg += f"💰 *هاپو پوینت هات:* {format_number(game._to_int(game.data['hop_point']))} 🪙\n\n"
        msg += f"❗️ *میخوای به هاپو بدی؟*"
        
        keyboard = [
            [InlineKeyboardButton(f"🍖 به هاپو بده", callback_data="hunt_feed")],
            [InlineKeyboardButton("◀️ برگشت", callback_data="hapo_back")]
        ]
        if query:
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    # بررسی یخچال
    if game.data.get("fridge_owned", False):
        items = game.get_fridge_items()
        if items:
            msg = f"🍖 *از یخچال به هاپو غذا بده!*\n\n"
            msg += f"📦 *موجودی یخچال:*\n"
            
            keyboard = []
            for i, item in enumerate(items[:5]):
                if not item.get("cooking", False):
                    name = item.get("name", "ناشناس")
                    emoji = item.get("emoji", "🐟")
                    nutrition = item.get("nutrition", 1)
                    msg += f"{emoji} {name} - {nutrition} کالری\n"
                    keyboard.append([InlineKeyboardButton(
                        f"{emoji} {name}", 
                        callback_data=f"hapo_feed_fridge_{i}"
                    )])
            
            if keyboard:
                keyboard.append([InlineKeyboardButton("◀️ برگشت", callback_data="hapo_back")])
                if query:
                    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                else:
                    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return
    
    # هیچ غذایی در دسترس نیست
    msg = get_hapo_menu_text(game)
    keyboard = get_hapo_menu_keyboard(game)
    if query:
        await query.edit_message_text(
            f"🍖 *هیچ غذایی برای هاپو نداری!*\n\n"
            f"💡 *برای غذا دادن به هاپو باید یک حیوان شکار کنی*\n"
            f"💡 *یا از یخچال هاپویی استفاده کن*\n\n"
            f"{msg}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🍖 *هیچ غذایی برای هاپو نداری!*\n\n"
            f"💡 *برای غذا دادن به هاپو باید یک حیوان شکار کنی*\n"
            f"💡 *یا از یخچال هاپویی استفاده کن*\n\n"
            f"{msg}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


# ================================================================
# تغییر اسم هاپو
# ================================================================

async def handle_hapo_rename_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش اسم جدید هاپو - فقط فحش‌های خیلی رکیک ممنوع"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not context.user_data.get("waiting_for_hapo_name"):
        return
    
    new_name = update.message.text.strip()
    
    # ✅ اعتبارسنجی اسم (فحش‌های خیلی رکیک ممنوع)
    is_valid, error_msg = is_valid_hapo_name(new_name)
    if not is_valid:
        await update.message.reply_text(
            f"{error_msg}\n\n✏️ *لطفاً اسم جدید رو وارد کن:*",
            parse_mode="Markdown"
        )
        return
    
    # بررسی اینکه اسم خالی نباشد
    if not new_name or len(new_name) < 1:
        await update.message.reply_text(
            "❌ *اسم نمی‌تواند خالی باشد*\n\n✏️ *لطفاً اسم جدید رو وارد کن:*",
            parse_mode="Markdown"
        )
        return
    
    hop_point = game._to_int(game.data["hop_point"])
    if hop_point < 750:
        await update.message.reply_text(
            f"❌ *پوینت کافی نیست!*\n"
            f"💰 نیاز: 750 🪙\n"
            f"💰 هاپو پوینت هات: {format_number(hop_point)} 🪙",
            parse_mode="Markdown"
        )
        context.user_data["waiting_for_hapo_name"] = False
        return
    
    old_name = game.data["hapo_name"]
    
    # ✅ بررسی نهایی قبل از تایید
    if contains_bad_word(new_name):
        await update.message.reply_text(
            f"❌ *اسم «{new_name}» مجاز نیست.*\n✏️ *لطفاً اسم دیگری انتخاب کن:*",
            parse_mode="Markdown"
        )
        return
    
    keyboard = get_confirm_keyboard(
        f"confirm_hapo_name_{new_name}",
        "cancel_hapo_name"
    )
    
    await update.message.reply_text(
        f"⚠️ *آیا از تغییر اسم هاپو مطمئنی؟*\n\n"
        f"📛 *اسم قدیمی:* {old_name}\n"
        f"📛 *اسم جدید:* {new_name}\n"
        f"💰 *هزینه:* 750 🪙",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    context.user_data["new_hapo_name"] = new_name
    context.user_data["waiting_for_hapo_name"] = False


# ================================================================
# پنجه
# ================================================================

async def show_claw_menu(update: Update, game):
    if game.is_jailed():
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "⛓️ *شما در زندان هستید.*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "⛓️ *شما در زندان هستید.*",
                parse_mode="Markdown"
            )
        return
    
    level = game._to_int(game.data["level"])
    if level < 2:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "🔒 *پنجه از سطح 2 باز میشود*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🔒 *پنجه از سطح 2 باز میشود*",
                parse_mode="Markdown"
            )
        return
    
    claw_level = game._to_int(game.data["claw_level"])
    if claw_level == 0:
        cost = game.get_claw_cost(1)
        keyboard = [[InlineKeyboardButton(f"🛒 خرید پنجه ({format_number(cost)})", callback_data="buy_claw")]]
        msg = f"🦞 *شما پنجه ندارید*\n\n💰 *هزینه خرید: {format_number(cost)} هاپو پوینت*\n⏳ *زمان استراحت: 60:00*\n🍀 *شانس شکار:*\n  ⚪ معمولی: 95%\n  🔵 کمیاب: 5%"
        
        if update.callback_query:
            try:
                await update.callback_query.edit_message_caption(
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            except:
                await update.callback_query.edit_message_text(
                    msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        else:
            try:
                await update.message.reply_photo(
                    photo=CLAW_IMAGES[1],
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            except:
                await update.message.reply_text(
                    msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        return
    
    claw_data = game.get_claw_data(claw_level)
    next_level = claw_level + 1
    next_data = game.get_claw_data(next_level)
    msg = f"🦞 *پنجه شما*\n⭐ *سطح:* {claw_level}\n⏳ *زمان استراحت:* {claw_data['cooldown']:02d}:00\n🍀 *شانس شکار:*\n  ⚪ معمولی: {claw_data['common']}%\n  🔵 کمیاب: {claw_data['uncommon']}%"
    if claw_data['epic'] > 0:
        msg += f"\n  🟣 حماسی: {claw_data['epic']}%"
    if claw_data['legendary'] > 0:
        msg += f"\n  🟡 افسانه‌ای: {claw_data['legendary']}%"
    
    keyboard = []
    if next_data:
        keyboard.append([InlineKeyboardButton(f"⬆️ سطح {next_level} ({format_number(next_data['cost'])})", callback_data="upgrade_claw")])
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_caption(
                caption=msg,
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                parse_mode="Markdown"
            )
        except:
            await update.callback_query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                parse_mode="Markdown"
            )
    else:
        try:
            await update.message.reply_photo(
                photo=CLAW_IMAGES[claw_level],
                caption=msg,
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                parse_mode="Markdown"
            )
        except:
            await update.message.reply_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                parse_mode="Markdown"
            )


# ================================================================
# شکار
# ================================================================

async def do_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE, game):
    if game.is_jailed():
        await update.message.reply_text(
            "⛓️ *شما در زندان هستید.*",
            parse_mode="Markdown"
        )
        return
    
    result = game.do_hunt()
    if not result["success"]:
        reason = result.get("reason", "")
        if "فرار کرد" in reason:
            await update.message.reply_text(f"❌ *{reason}*", parse_mode="Markdown")
        elif reason == "خسته‌ام":
            remaining = result.get("remaining", 0)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await update.message.reply_text(f"⏳ *تا شکار بعدی {mins}:{secs:02d} مونده*", parse_mode="Markdown")
        elif "ثانیه مونده" in reason:
            await update.message.reply_text(f"⏳ *{reason}*", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ *{reason}*", parse_mode="Markdown")
        return
    
    try:
        if update.message.chat.type in ["group", "supergroup"]:
            chat_id = str(update.message.chat.id)
            from database import add_group
            add_group(chat_id, update.message.chat.title or "گروه بدون نام")
            response = supabase.table("groups").select("total_hunts").eq("chat_id", chat_id).execute()
            if response.data:
                total_hunts = int(float(response.data[0].get("total_hunts", 0))) + 1
                supabase.table("groups").update({
                    "total_hunts": str(total_hunts)
                }).eq("chat_id", chat_id).execute()
    except Exception as e:
        logger.error(f"Error updating group hunt stats: {e}")
    
    hunt_msg = await update.message.reply_text("🏹 *در حال شکار ...*", parse_mode="Markdown")
    await asyncio.sleep(2)
    
    animal = result["animal"]
    animal_name = animal.get("name", "")
    
    msg = f"*شما با موفقیت {animal['emoji']} گرفتید…*\n⭐️ *سطح :* {animal['rarity_name']}\n⚖️ *وزن :* {animal['weight']} کیلو\n💰 *ارزش :* {format_number(animal['value'])} 🪙\n🍖 *ارزش غذایی :* {animal['nutrition']} کالری\n\n⏳ *60 ثانیه فرصت انتخاب داری*"
    
    keyboard = [
        [InlineKeyboardButton(f"💰 فروش ({format_number(animal['value'])})", callback_data="hunt_sell")]
    ]
    if game.data["hapo_owned"]:
        keyboard.append([InlineKeyboardButton(f"🍖 به هاپو بده", callback_data="hunt_feed")])
    if game.data.get("fridge_owned", False):
        keyboard.append([InlineKeyboardButton("❄️ بندازش تو یخچال", callback_data=f"hunt_fridge_{animal_name}")])
    
    try:
        await hunt_msg.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Could not edit hunt message, sending new: {e}")
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    user_id = update.effective_user.id
    context.user_data["hunt_chat_id"] = update.message.chat.id
    context.user_data["hunt_message_id"] = hunt_msg.message_id
    context.user_data["hunt_user_id"] = user_id
    
    asyncio.create_task(hunt_animal_timer(update, context, user_id))


async def hunt_animal_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    await asyncio.sleep(HUNT_DECISION_TIMER)
    try:
        game = get_game(user_id)
        animal = game.data.get("current_hunt_animal")
        if not animal:
            return
        
        hunt_time = game._to_float(game.data.get("hunt_time", 0))
        now = datetime.now().timestamp()
        if (now - hunt_time) >= HUNT_DECISION_TIMER:
            animal_name = animal.get("name", "حیوان")
            game.data["current_hunt_animal"] = None
            game.data["hunt_time"] = "0"
            game.save_data()
            
            chat_id = context.user_data.get("hunt_chat_id")
            message_id = context.user_data.get("hunt_message_id")
            
            if chat_id and message_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"🦌 *{animal_name} فرار کرد! وقتت تموم شد.*\n\n💡 دفعه دیگه سریعتر تصمیم بگیر!",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"Could not edit hunt message: {e}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🦌 *{animal_name} فرار کرد! وقتت تموم شد.*",
                        parse_mode="Markdown"
                    )
    except Exception as e:
        logger.error(f"Error in hunt_animal_timer: {e}")


async def handle_hunt_release(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    animal = game.data.get("current_hunt_animal")
    if not animal:
        await query.edit_message_text("❌ *هیچ حیوانی برای رها کردن وجود ندارد*", parse_mode="Markdown")
        return
    
    animal_name = animal.get("name", "حیوان")
    animal_emoji = animal.get("emoji", "🐾")
    
    game.data["current_hunt_animal"] = None
    game.data["hunt_time"] = "0"
    game.save_data()
    
    await query.edit_message_text(
        f"{animal_emoji} *{animal_name} رو رها کردی!*\n\n🐾 حیوان به طبیعت برگشت...",
        parse_mode="Markdown"
    )


# ================================================================
# کالبک‌های هاپو (برای handle_callback)
# ================================================================

async def handle_hapo_callback(query, game, data, context):
    """هندلر کالبک‌های هاپو"""
    user_id = query.from_user.id
    
    # ======== خرید هاپو ========
    if data == "buy_hapo":
        result = game.buy_hapo()
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.edit_message_text(
                f"✅ *هاپو خریداری شد!*\n📛 اسم هاپو: {result['name']}\n💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *{result['reason']}*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        return
    
    # ======== برداشت ========
    if data == "hapo_harvest":
        hapo_food = game._to_int(game.data["hapo_food"])
        hapo_harvest = game._to_int(game.data["hapo_harvest"])
        
        # ✅ اگر غذا ۰ است، پیام بده
        if hapo_food == 0:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"😢 *هاپو گرسنه است و کار نمیکند!*\n\n🍖 *بهش غذا بده تا دوباره کار کنه*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        if hapo_harvest > 0:
            hop_point = game._to_int(game.data["hop_point"])
            game.data["hop_point"] = str(hop_point + hapo_harvest)
            game.data["hapo_harvest"] = "0"
            game.save_data()
            await query.edit_message_text(
                f"✅ *{format_number(hapo_harvest)} هاپو پوینت برداشت شد*\n💰 *هاپو پوینت هات:* {format_number(hop_point + hapo_harvest)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *هیچ هاپو پوینتی برای برداشت نیست*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        return
    
    # ======== ارتقا سطح ========
    if data == "hapo_level_up":
        check = game.can_upgrade_level()
        if not check["success"]:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *{check['reason']}*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        price = game.get_hapo_upgrade_price()
        hop_point = game._to_int(game.data["hop_point"])
        if hop_point < price:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *پوینت کافی نیست!*\n💰 نیاز: {format_number(price)} 🪙\n💰 هاپو پوینت هات: {format_number(hop_point)} 🪙\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        result = game.upgrade_hapo_level()
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.edit_message_text(
                f"✅ *سطح هاپو به {result['new_level']} ارتقا یافت*\n💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *{result['reason']}*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        return
    
    # ======== ارتقا مقام ========
    if data == "hapo_rank_up_confirm":
        check = game.can_rank_up()
        if not check["success"]:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *{check['reason']}*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        price = game.get_hapo_rank_up_price()
        hop_point = game._to_int(game.data["hop_point"])
        if hop_point < price:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *پوینت کافی نیست!*\n💰 نیاز: {format_number(price)} 🪙\n💰 هاپو پوینت هات: {format_number(hop_point)} 🪙\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        hapo_rank = game._to_int(game.data["hapo_rank"])
        current_max = game.get_hapo_max_level_for_rank(hapo_rank)
        next_max = game.get_hapo_max_level_for_rank(hapo_rank + 1)
        
        msg = f"⚠️ *آیا از ارتقا مقام هاپو مطمئنی؟*\n\n"
        msg += f"🌟 *مقام فعلی:* {RANK_NAMES[hapo_rank]}\n"
        msg += f"🌟 *مقام جدید:* {RANK_NAMES[hapo_rank + 1]}\n"
        msg += f"📊 *سقف سطح فعلی:* {current_max}\n"
        msg += f"📊 *سقف سطح جدید:* {next_max}\n"
        msg += f"💰 *هزینه:* {format_number(price)} 🪙"
        
        await query.edit_message_text(
            msg,
            reply_markup=get_confirm_keyboard("hapo_rank_up_yes", "hapo_rank_up_no"),
            parse_mode="Markdown"
        )
        return
    
    if data == "hapo_rank_up_yes":
        result = game.confirm_rank_up()
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.edit_message_text(
                f"✅ *مقام هاپو به {result['new_rank_name']} ارتقا یافت!*\n💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *{result['reason']}*\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        return
    
    if data == "hapo_rank_up_no":
        await query.edit_message_text("❌ *ارتقا مقام لغو شد*", parse_mode="Markdown")
        await asyncio.sleep(1)
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    # ======== تغییر اسم ========
    if data == "hapo_rename":
        hop_point = game._to_int(game.data["hop_point"])
        if hop_point < 750:
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(
                f"❌ *پوینت کافی نیست!*\n💰 نیاز: 750 🪙\n💰 هاپو پوینت هات: {format_number(hop_point)} 🪙\n\n{msg}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        await query.edit_message_text("✏️ *اسم جدید هاپو رو وارد کن:*", parse_mode="Markdown")
        context.user_data["waiting_for_hapo_name"] = True
        return
    
    # ======== تایید اسم جدید ========
    if data.startswith("confirm_hapo_name_"):
        new_name = data.replace("confirm_hapo_name_", "")
        
        # ✅ اعتبارسنجی مجدد
        is_valid, error_msg = is_valid_hapo_name(new_name)
        if not is_valid:
            await query.edit_message_text(
                f"{error_msg}\n\n✏️ *برای تغییر اسم، دوباره «هاپو» رو بزن.*",
                parse_mode="Markdown"
            )
            context.user_data["new_hapo_name"] = None
            return
        
        if contains_bad_word(new_name):
            await query.edit_message_text(
                f"❌ *اسم «{new_name}» مجاز نیست.*\n✏️ *برای تغییر اسم، دوباره «هاپو» رو بزن.*",
                parse_mode="Markdown"
            )
            context.user_data["new_hapo_name"] = None
            return
        
        if not game.data.get("hapo_owned", False):
            await query.edit_message_text("❌ *شما هاپو ندارید!*", parse_mode="Markdown")
            context.user_data["new_hapo_name"] = None
            return
        
        hop_point = game._to_int(game.data["hop_point"])
        if hop_point < 750:
            await query.edit_message_text(
                f"❌ *پوینت کافی نیست!*\n💰 نیاز: 750 🪙\n💰 هاپو پوینت هات: {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            context.user_data["new_hapo_name"] = None
            return
        
        old_name = game.data["hapo_name"]
        game.data["hapo_name"] = new_name
        game.data["hop_point"] = str(hop_point - 750)
        game.save_data()
        
        log_transaction(user_id, "تغییر اسم هاپو", 750, f"از {old_name} به {new_name}")
        
        await query.edit_message_text(
            f"✅ *اسم هاپو با موفقیت تغییر کرد!*\n\n📛 *اسم جدید:* {new_name}\n💰 *هاپو پوینت هات:* {format_number(hop_point - 750)} 🪙",
            parse_mode="Markdown"
        )
        
        context.user_data["new_hapo_name"] = None
        await asyncio.sleep(1)
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    if data == "cancel_hapo_name":
        await query.edit_message_text("❌ *تغییر اسم هاپو لغو شد*", parse_mode="Markdown")
        context.user_data["new_hapo_name"] = None
        await asyncio.sleep(1)
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    # ======== غذا دادن به هاپو ========
    if data == "hapo_feed_show":
        await show_hapo_feed_menu(update, game, query)
        return
    
    if data == "hapo_back":
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    # ======== نهایی ========
    if data == "hapo_max":
        await query.edit_message_text("🏆 *هاپو در بالاترین سطح است*", parse_mode="Markdown")
        await asyncio.sleep(1)
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return


# ================================================================
# کالبک‌های شکار (برای handle_callback)
# ================================================================

async def handle_hunt_callback(query, game, data, context):
    """هندلر کالبک‌های شکار"""
    
    # ======== فروش حیوان ========
    if data == "hunt_sell":
        result = game.sell_animal()
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.message.reply_text(
                f"💰 *حیوان فروخته شد!*\n✅ *{format_number(result['value'])} 🪙 دریافت کردی*\n💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
        else:
            await query.answer(f"❌ {result['reason']}", show_alert=True)
        return
    
    # ======== غذا دادن به هاپو ========
    if data == "hunt_feed":
        result = game.feed_hapo()
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.message.reply_text(
                f"🍖 *{result['fed']} غذا به هاپو داده شد*\n✅ *هاپو سیر شد!*\n💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            return
        
        error_msg = result["reason"]
        animal = game.data.get("current_hunt_animal")
        if error_msg == "هاپو سیر است" and animal:
            msg = f"❌ *هاپو سیر است!*\n\n"
            msg += f"{animal['emoji']} *{animal['name']}*\n"
            msg += f"⭐ *سطح :* {animal['rarity_name']}\n"
            msg += f"⚖️ *وزن :* {animal['weight']} کیلو\n"
            msg += f"💰 *ارزش فروش :* {format_number(animal['value'])} 🪙\n\n"
            msg += "❗️ *میخوای چیکارش کنی ؟*"
            keyboard = [
                [InlineKeyboardButton(f"💰 فروش ({format_number(animal['value'])})", callback_data="hunt_sell")]
            ]
            if game.data.get("fridge_owned", False):
                from fridge_handlers import handle_hunt_to_fridge
                keyboard.append([InlineKeyboardButton("❄️ بندازش تو یخچال", callback_data=f"hunt_fridge_{animal.get('name', '')}")])
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        await query.answer(f"❌ {error_msg}", show_alert=True)
        return
    
    # ======== پنجه ========
    if data == "buy_claw":
        result = game.buy_claw()
        if result["success"]:
            await query.message.reply_text("✅ *پنجه خریداری شد!*", parse_mode="Markdown")
            await asyncio.sleep(1)
            await show_claw_menu(update, game)
        else:
            await query.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
        return
    
    if data == "upgrade_claw":
        result = game.upgrade_claw()
        if result["success"]:
            await query.message.reply_text(f"✅ *پنجه به سطح {result['new_level']} ارتقا یافت*", parse_mode="Markdown")
            await asyncio.sleep(1)
            await show_claw_menu(update, game)
        else:
            await query.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
        return


# ================================================================
# کالبک‌های غذا از یخچال (برای handle_callback)
# ================================================================

async def handle_hapo_feed_fridge(query, game, data, context):
    """هندلر غذا دادن به هاپو از یخچال"""
    if data.startswith("hapo_feed_fridge_"):
        index = int(data.replace("hapo_feed_fridge_", ""))
        result = game.feed_hapo_from_fridge(index)
        
        if result["success"]:
            item = result["item"]
            fed = result["fed"]
            new_food = result.get("new_food", 0)
            max_food = result.get("max_food", 0)
            
            await query.edit_message_text(
                f"🍖 *{item['emoji']} {item['name']} به هاپو داده شد!*\n\n"
                f"✅ *{fed} کالری به هاپو اضافه شد.*\n"
                f"🍖 *شکم هاپو:* {new_food}/{max_food}\n\n"
                f"😊 *هاپو دوباره کار میکنه!*",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
        return
