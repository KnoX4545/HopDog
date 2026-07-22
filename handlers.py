# handlers.py - فایل اصلی (نسخه کامل)

import logging
import asyncio
import random
import re
import traceback
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    ADMIN_PASSWORD, MIN_MEMBERS_TO_STAY, RANK_NAMES, MAX_LEVEL,
    TRANSFER_MIN_AMOUNT, TRANSFER_MAX_AMOUNT, TRANSFER_COOLDOWN,
    TRANSFER_MIN_LEVEL_SENDER, TRANSFER_MIN_LEVEL_RECEIVER,
    BANK_PURCHASE_COST, JAIL_MAX_SPAM_COMMANDS, JAIL_SPAM_WINDOW,
    JAIL_DURATION_SPAM, JAIL_FINE_SPAM, JAIL_REASON_SPAM,
    JAIL_DURATION_MEOW, JAIL_FINE_MEOW, JAIL_REASON_MEOW,
    JAIL_REASON_SMUGGLE, JAIL_DURATION_SMUGGLE, JAIL_FINE_SMUGGLE,
    JAIL_VOTE_DURATION, JAIL_VOTE_NEEDED, HUNT_DECISION_TIMER,
    STREET_HAPO_DECISION_TIME, STREET_HAPO_COSTS, STREET_HAPO_SUCCESS_CHANCE,
    STREET_HAPO_IMAGE_URL, STREET_HAPO_REWARD_MIN, STREET_HAPO_REWARD_MAX,
    STREET_HAPO_FAIL_MESSAGES, STREET_HAPO_MAX_ATTEMPTS, CLAW_IMAGES,
    SMUGGLE_MIN_HAPO, SMUGGLE_MAX_HAPO, SMUGGLE_REQUIRED_LEVEL,
    SMUGGLE_REWARD_MIN, SMUGGLE_REWARD_MAX, FRIDGE_REQUIRED_LEVEL,
    FRIDGE_PURCHASE_COST, FRIDGE_MAX_LEVEL, FRIDGE_CAPACITY,
    FRIDGE_UPGRADE_COSTS, FRIDGE_COOK_MULTIPLIER_SELL, FRIDGE_COOK_MULTIPLIER_FOOD,
    SMUGGLE_TIME_PER_HAPO, LEADERBOARD_MAX_USERS, LEADERBOARD_MAX_GROUPS
)

from handlers_common import get_game, get_street_hapo, GAME_XO_STATE, get_user_display_name

from game_handlers import (
    show_games_menu, show_xo_main, handle_xo_set_bet, 
    process_xo_bet, handle_xo_create, handle_xo_join,
    handle_xo_move, handle_xo_close, handle_xo_cancel
)

from claw_handlers import show_claw_menu, handle_buy_claw, handle_upgrade_claw
from street_handlers import handle_street_hapo_rescue

from game import StreetHapo
from database import (
    get_user_by_identifier, get_user_by_card, get_all_groups,
    add_group, remove_group, get_user_data, save_user_data, supabase
)
from bank import (
    get_bank_menu_text, get_bank_keyboard, get_change_card_confirm_text,
    get_card_to_card_text, format_number
)
from academy import (
    ACADEMY_MAIN, ACADEMY_SUB_SYSTEM, ACADEMY_SUB_FEATURES, ACADEMY_SUB_ADVENTURE,
    ACADEMY_SYSTEM_PAGE1, ACADEMY_SYSTEM_PAGE2, ACADEMY_SYSTEM_PAGE3, ACADEMY_SYSTEM_PAGE4,
    ACADEMY_ANIMALS_PAGE1, ACADEMY_ANIMALS_PAGE2, ACADEMY_ANIMALS_PAGE3,
    ACADEMY_CLAW_PAGE1, ACADEMY_CLAW_PAGE2, ACADEMY_CLAW_PAGE3,
    ACADEMY_HAPO, ACADEMY_HUNT, ACADEMY_BANK, ACADEMY_TRANSFER, ACADEMY_JAIL, ACADEMY_STREET_HAPO,
    ACADEMY_HOP, ACADEMY_POINTS, ACADEMY_EXP, ACADEMY_PROFILE,
    ACADEMY_FRIDGE, ACADEMY_SMUGGLE, ACADEMY_LEADERBOARD,
    ACADEMY_GAMES, ACADEMY_GAMES_XO, ACADEMY_GAMES_MENU,
    show_academy_main, show_academy_system_menu, show_academy_features_menu,
    show_academy_adventure_menu, show_academy_games_menu, show_academy_game_xo,
    show_academy_system_pages, show_academy_animals_pages, show_academy_claw_pages,
    show_feature_page, show_adventure_page, show_street_hapo_page
)

# دیکشنری‌های عمومی
SPAM_TRACKER = {}
MEOW_VOTES = {}
TRANSFER_STATE = {}
STREET_HAPO_LAST_SENT = {}

logger = logging.getLogger(__name__)


# ================================================================
# توابع کمکی
# ================================================================

def get_confirm_keyboard(callback_data_yes, callback_data_no):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ بله", callback_data=callback_data_yes),
         InlineKeyboardButton("❌ نه", callback_data=callback_data_no)]
    ])


def get_hapo_menu_keyboard(game):
    keyboard = [
        [InlineKeyboardButton("💰 برداشت", callback_data="hapo_harvest")],
    ]
    
    total = game.get_hapo_total_level()
    is_max = total >= 20
    
    hapo_level = game._to_int(game.data["hapo_level"])
    hapo_rank = game._to_int(game.data["hapo_rank"])
    max_level = game.get_hapo_max_level_for_rank(hapo_rank)
    
    if is_max:
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


def get_hapo_menu_text(game):
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
    
    msg = f"🐶 *{game.data['hapo_name']}*\n"
    msg += f"💕 نام : {game.data['hapo_name']}\n"
    msg += f"🍖 شکم : {status['text']} ({hapo_food}/{max_food})\n"
    msg += f"🌟 مقام : {RANK_NAMES[hapo_rank]}\n"
    msg += f"⭐️ سطح : {hapo_level}/5\n"
    msg += f"💰 هاپو پوینت های تولید شده : {format_number(hapo_harvest)} 🪙\n"
    msg += f"💫 تولید هاپو پوینت در ثانیه : {prod:.2f} 🪙\n"
    msg += f"📦 ظرفیت : {format_number(capacity)}\n"
    
    if is_max:
        msg += "🏆 مقام نهایی"
    elif hapo_level >= 5 and hapo_rank < 4:
        rank_price = game.get_hapo_rank_up_price()
        msg += f"💰 هزینه ارتقا مقام : {format_number(rank_price)} 🪙"
    else:
        price = game.get_hapo_upgrade_price()
        msg += f"💰 هزینه ارتقا سطح : {format_number(price)} 🪙"
    
    return msg


def check_spam(user_id):
    now = datetime.now().timestamp()
    
    if user_id not in SPAM_TRACKER:
        SPAM_TRACKER[user_id] = {"commands": [now]}
        return False
    
    tracker = SPAM_TRACKER[user_id]
    tracker["commands"] = [t for t in tracker["commands"] if (now - t) <= JAIL_SPAM_WINDOW]
    tracker["commands"].append(now)
    
    if len(tracker["commands"]) >= JAIL_MAX_SPAM_COMMANDS:
        del SPAM_TRACKER[user_id]
        return True
    
    return False


# ================================================================
# دستورات اصلی
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    display_name = get_user_display_name(user_id, username, full_name)
    game = get_game(user_id, display_name)
    
    if game.data.get("player_name", "").startswith("کاربر") and display_name and not display_name.startswith("کاربر"):
        game.data["player_name"] = display_name
        game.save_data()
    
    keyboard = [[InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{context.bot.username}?startgroup=start")]]
    
    if not game.data.get("has_seen_welcome", False):
        game.data["has_seen_welcome"] = True
        game.save_data()
        await update.message.reply_text(
            "🐾 *ربات سرگرمی هاپویی* 🐶\n\n"
            "🐕 یه هاپوی بامزه برای گروهت…\n"
            "کافیه توی گروه هاپ هاپ کنی تا هاپ پوینت بگیری 🐶\n\n"
            "⭐️ هاپ پوینت جمع کن و با بقیه رقابت کن\n"
            "🏆 لیدربرد هاپویی رو فتح کن و پادشاه هاپو ها شو\n\n"
            "✨ *چرا هاپویی ؟*\n\n"
            "⚡ پاسخگویی فوق‌العاده سریع\n"
            "🛠️ عملکرد پایدار و بدون باگ\n"
            "🔄 آپدیت‌های هفتگی\n"
            "👥 کامیونیتی فعال و پرانرژی\n"
            "🚨 پشتیبانی ۲۴ ساعته\n"
            "🪙 کاملاً رایگان برای همه\n\n"
            "🐶 کافیه ربات رو به گروهت اضافه کنی…\n"
            "بعدش شروع کنی به هاپ هاپ کردن",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🐾 *سلام {display_name}!*\n"
            "به هاپ داگ خوش اومدی 🐕\n\n"
            "*دستورات:*\n"
            "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
            "📊 هاپوهام - مشاهده پروفایل خودت\n"
            "⛓️ زندان هاپویی - اطلاعات زندان\n"
            "📚 آکادمی - راهنمای کامل\n"
            "❄️ یخچال هاپویی - ذخیره حیوانات\n"
            "🥷 قاچاق هاپویی - قاچاق هاپوها\n"
            "🕹 بازی هاپویی - بازی‌های هاپویی\n"
            "🔒 برای دستورات ادمین، از پیوی بات استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        await show_academy_main(update)
        return
    await show_academy_main(update)


async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما دسترسی به این دستور ندارید.*", parse_mode="Markdown")
        return
    
    help_text = (
        "🛡️ *دستورات ادمین هاپویی*\n\n"
        "📊 *مدیریت کاربران:*\n"
        "`/userinfo [id]` - اطلاعات کاربر\n"
        "`/setlevel [id] [level]` - تنظیم سطح\n"
        "`/addlevel [id] [level]` - اضافه کردن سطح\n"
        "`/setpoint [id] [point]` - تنظیم پوینت\n"
        "`/addpoint [id] [point]` - اضافه کردن پوینت\n"
        "`/rest [id]` - ریست کامل کاربر\n\n"
        "⛓️ *مدیریت زندان:*\n"
        "`/jail [id] [دقیقه] [دلیل]` - زندانی کردن کاربر\n\n"
        "🐶 *هاپوی خیابونی:*\n"
        "`/hapo [chat_id]` - ارسال هاپوی خیابونی به گروه\n"
        "`/setstreethapo [id] [count]` - تنظیم هاپوی خیابونی\n"
        "`/addstreethapo [id] [count]` - اضافه کردن هاپوی خیابونی\n\n"
        "📋 *سایر:*\n"
        "`/groups` - لیست گروه‌های ثبت شده\n"
        "`/ahelp` - نمایش این راهنما"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


# ================================================================
# توابع لیدربرد
# ================================================================

async def get_leaderboard_data(category, limit=250, group=False):
    try:
        if group:
            limit = LEADERBOARD_MAX_GROUPS
            
            if category == "hop":
                response = supabase.table("groups").select("chat_id, title, total_hops").eq("is_active", True).execute()
                if response.data:
                    data = []
                    for item in response.data:
                        try:
                            val = int(float(item.get("total_hops", 0)))
                        except:
                            val = 0
                        data.append({
                            "chat_id": item.get("chat_id"),
                            "title": item.get("title", "گروه بدون نام"),
                            "total_hops": val
                        })
                    data.sort(key=lambda x: x["total_hops"], reverse=True)
                    return data[:limit]
                return []
            elif category == "population":
                response = supabase.table("groups").select("chat_id, title, member_count").eq("is_active", True).execute()
                if response.data:
                    data = []
                    for item in response.data:
                        try:
                            val = int(float(item.get("member_count", 0)))
                        except:
                            val = 0
                        data.append({
                            "chat_id": item.get("chat_id"),
                            "title": item.get("title", "گروه بدون نام"),
                            "member_count": val
                        })
                    data.sort(key=lambda x: x["member_count"], reverse=True)
                    return data[:limit]
                return []
            elif category == "wealth":
                response = supabase.table("groups").select("chat_id, title, total_hapo_points").eq("is_active", True).execute()
                if response.data:
                    data = []
                    for item in response.data:
                        try:
                            val = int(float(item.get("total_hapo_points", 0)))
                        except:
                            val = 0
                        data.append({
                            "chat_id": item.get("chat_id"),
                            "title": item.get("title", "گروه بدون نام"),
                            "total_hapo_points": val
                        })
                    data.sort(key=lambda x: x["total_hapo_points"], reverse=True)
                    return data[:limit]
                return []
            elif category == "hunt":
                response = supabase.table("groups").select("chat_id, title, total_hunts").eq("is_active", True).execute()
                if response.data:
                    data = []
                    for item in response.data:
                        try:
                            val = int(float(item.get("total_hunts", 0)))
                        except:
                            val = 0
                        data.append({
                            "chat_id": item.get("chat_id"),
                            "title": item.get("title", "گروه بدون نام"),
                            "total_hunts": val
                        })
                    data.sort(key=lambda x: x["total_hunts"], reverse=True)
                    return data[:limit]
                return []
            else:
                return []
        else:
            if category == "point":
                response = supabase.table("users").select("user_id, player_name, hop_point").execute()
                if response.data:
                    data = []
                    for item in response.data:
                        try:
                            val = int(float(item.get("hop_point", 0)))
                        except:
                            val = 0
                        data.append({
                            "user_id": item.get("user_id"),
                            "player_name": item.get("player_name", f"کاربر{item.get('user_id')}"),
                            "hop_point": val
                        })
                    data.sort(key=lambda x: x["hop_point"], reverse=True)
                    return data[:limit]
                return []
            elif category == "hop":
                response = supabase.table("users").select("user_id, player_name, hop_count").execute()
                if response.data:
                    data = []
                    for item in response.data:
                        try:
                            val = int(float(item.get("hop_count", 0)))
                        except:
                            val = 0
                        data.append({
                            "user_id": item.get("user_id"),
                            "player_name": item.get("player_name", f"کاربر{item.get('user_id')}"),
                            "hop_count": val
                        })
                    data.sort(key=lambda x: x["hop_count"], reverse=True)
                    return data[:limit]
                return []
            elif category == "street":
                response = supabase.table("users").select("user_id, player_name, street_hapo_rescued").execute()
                if response.data:
                    data = []
                    for item in response.data:
                        try:
                            val = int(float(item.get("street_hapo_rescued", 0)))
                        except:
                            val = 0
                        data.append({
                            "user_id": item.get("user_id"),
                            "player_name": item.get("player_name", f"کاربر{item.get('user_id')}"),
                            "street_hapo_rescued": val
                        })
                    data.sort(key=lambda x: x["street_hapo_rescued"], reverse=True)
                    return data[:limit]
                return []
            elif category == "hunt":
                response = supabase.table("users").select("user_id, player_name, total_hunts").execute()
                if response.data:
                    data = []
                    for item in response.data:
                        try:
                            val = int(float(item.get("total_hunts", 0)))
                        except:
                            val = 0
                        data.append({
                            "user_id": item.get("user_id"),
                            "player_name": item.get("player_name", f"کاربر{item.get('user_id')}"),
                            "total_hunts": val
                        })
                    data.sort(key=lambda x: x["total_hunts"], reverse=True)
                    return data[:limit]
                return []
            else:
                return []
    except Exception as e:
        logger.error(f"Error getting leaderboard data: {e}")
        return []


async def get_user_rank(user_id, category):
    try:
        data = await get_leaderboard_data(category, limit=1000, group=False)
        for i, item in enumerate(data):
            if str(item.get("user_id")) == str(user_id):
                return i + 1
        return None
    except Exception as e:
        logger.error(f"Error getting user rank: {e}")
        return None


async def show_leaderboard_result(update: Update, context: ContextTypes.DEFAULT_TYPE, category, group=False, page=0):
    query = update.callback_query
    await query.answer()
    
    data = await get_leaderboard_data(category, group=group)
    
    if not data:
        await query.edit_message_text("❌ *هیچ داده‌ای برای نمایش وجود ندارد.*", parse_mode="Markdown")
        return
    
    items_per_page = 10
    total_pages = (len(data) + items_per_page - 1) // items_per_page
    
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(data))
    page_data = data[start_idx:end_idx]
    
    if group:
        titles = {
            "hop": "🐾 *پر سر و صدا ترین گروه ها*",
            "population": "👥 *پر جمعیت ترین گروه ها*",
            "wealth": "🏦 *ثروتمند ترین گروه ها*",
            "hunt": "🏹 *بهترین بازار شکار*"
        }
        title = titles.get(category, "🏆 *لیدربرد گروهی*")
        msg = f"{title} 🏆\n\n"
        
        for i, item in enumerate(page_data, start=start_idx + 1):
            name = item.get("title", "گروه بدون نام")
            if category == "hop":
                value = item.get("total_hops", 0)
                emoji = "🐾"
            elif category == "population":
                value = item.get("member_count", 0)
                emoji = "👥"
            elif category == "wealth":
                value = item.get("total_hapo_points", 0)
                emoji = "🏦"
            elif category == "hunt":
                value = item.get("total_hunts", 0)
                emoji = "🏹"
            else:
                value = 0
                emoji = "📊"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
            msg += f"{medal} {emoji} *{name}* : `{format_number(value)}`\n"
    else:
        titles = {
            "point": "🪙 *ثروتمند ترین هاپو ها*",
            "hop": "🐾 *پر سر و صدا ترین هاپو ها*",
            "street": "🐶 *مهربون ترین هاپو ها*",
            "hunt": "🏹 *بهترین شکارچی ها*"
        }
        title = titles.get(category, "🏆 *لیدربرد هاپوها*")
        msg = f"{title} 🏆\n\n"
        
        for i, item in enumerate(page_data, start=start_idx + 1):
            user_id = item.get("user_id", "نامشخص")
            name = item.get("player_name", f"کاربر{user_id}")
            
            if category == "point":
                value = item.get("hop_point", 0)
                emoji = "🪙"
            elif category == "hop":
                value = item.get("hop_count", 0)
                emoji = "🐾"
            elif category == "street":
                value = item.get("street_hapo_rescued", 0)
                emoji = "🐶"
            elif category == "hunt":
                value = item.get("total_hunts", 0)
                emoji = "🏹"
            else:
                value = 0
                emoji = "📊"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
            msg += f"{medal} {emoji} *{name}* : `{format_number(value)}`\n"
    
    keyboard = []
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️", callback_data=f"lb_{category}_page_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("▶️", callback_data=f"lb_{category}_page_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    if group:
        keyboard.append([InlineKeyboardButton("◀️ برگشت به منوی گروه", callback_data="lb_group")])
    else:
        keyboard.append([InlineKeyboardButton("◀️ برگشت به منوی هاپو", callback_data="lb_hapo")])
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def show_leaderboard_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type not in ["private", "group", "supergroup"]:
        return
    
    keyboard = [
        [InlineKeyboardButton("🏆 برترین هاپو ها", callback_data="lb_hapo")],
        [InlineKeyboardButton("🏰 برترین گروه ها", callback_data="lb_group")],
        [InlineKeyboardButton("◀️ برگشت", callback_data="lb_back")]
    ]
    
    if update.message:
        await update.message.reply_text(LEADERBOARD_MAIN, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(LEADERBOARD_MAIN, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def show_leaderboard_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🪙 هاپو پوینت", callback_data="lb_hapo_point")],
        [InlineKeyboardButton("🐾 هاپ هاپ", callback_data="lb_hapo_hop")],
        [InlineKeyboardButton("🐶 هاپوی خیابونی", callback_data="lb_hapo_street")],
        [InlineKeyboardButton("🏹 شکار", callback_data="lb_hapo_hunt")],
        [InlineKeyboardButton("◀️ برگشت", callback_data="lb_main")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(LEADERBOARD_HAPO, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def show_leaderboard_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🐾 هاپ هاپ", callback_data="lb_group_hop")],
        [InlineKeyboardButton("👥 جمعیت", callback_data="lb_group_population")],
        [InlineKeyboardButton("🏦 خزانه", callback_data="lb_group_wealth")],
        [InlineKeyboardButton("🏹 بازار شکار", callback_data="lb_group_hunt")],
        [InlineKeyboardButton("◀️ برگشت", callback_data="lb_main")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(LEADERBOARD_GROUP, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ================================================================
# زندان هاپویی
# ================================================================

async def show_jail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    jail_info = game.get_jail_info()
    if not jail_info:
        await update.message.reply_text("🐶 *شما در زندان نیستید! آزاد هستید* 🎉", parse_mode="Markdown")
        return
    
    remaining = jail_info["remaining"]
    minutes = remaining // 60
    seconds = remaining % 60
    fine = jail_info["fine"]
    reason = jail_info["reason"]
    arrest_time = jail_info["arrest_time"]
    admin_id = jail_info.get("admin_id", None)
    
    arrest_date = datetime.fromtimestamp(arrest_time).strftime("%d %B %Y")
    
    msg = f"🐶 *زندان هاپویی* ⛓️\n\n"
    msg += f"🚨 شما هاپوی بدی بودین و زندانی شدید ❗️\n\n"
    msg += f"📝 *دلیل حبس :* {reason}\n"
    msg += f"⏳ *مدت حبس :* {minutes:02d}:{seconds:02d}\n"
    msg += f"🏦 *جریمه نقدی :* {format_number(fine)} 🪙\n"
    msg += f"┘─ میتونید با پرداخت جریمه از زندان آزاد شوید\n\n"
    
    if admin_id:
        try:
            admin_user = await context.bot.get_chat(admin_id)
            admin_name = admin_user.full_name or admin_user.username or f"کاربر{admin_id}"
            msg += f"👮 *زندانی شده توسط :* {admin_name}\n\n"
        except:
            msg += f"👮 *زندانی شده توسط :* ادمین\n\n"
    
    msg += f"👮 *دستگیر شده در* {arrest_date}\n\n"
    msg += f"❗️ تا زمانی که توی حبس باشید نمیتوانید از هیچ یک از امکانات ربات استفاده کنید.\n"
    msg += f"- با نوشتن \"زندان هاپویی\" میتوانید وارد سلول خود شوید"
    
    keyboard = [[InlineKeyboardButton("💰 پرداخت جریمه", callback_data="jail_pay_fine")]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ================================================================
# پروفایل
# ================================================================

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    display_name = get_user_display_name(user_id, username, full_name)
    game = get_game(user_id, display_name)
    
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
        return
    
    required = game.get_required_for_level(game._to_int(game.data["level"]))
    is_hidden = game.data.get("profile_hidden", False)
    is_locked = game.data.get("profile_locked", False)
    
    street_rescued = game._to_int(game.data.get("street_hapo_rescued", 0))
    hapo_rank = game._to_int(game.data.get("hapo_rank", 0))
    hapo_level = game._to_int(game.data.get("hapo_level", 1))
    hop_point = game._to_int(game.data["hop_point"])
    hop_count = game._to_int(game.data["hop_count"])
    level = game._to_int(game.data["level"])
    
    point_rank = await get_user_rank(user_id, "point")
    hop_rank = await get_user_rank(user_id, "hop")
    street_rank = await get_user_rank(user_id, "street")
    hunt_rank = await get_user_rank(user_id, "hunt")
    
    total_hunts = game._to_int(game.data.get("total_hunts", 0))
    
    msg = f"╮──「 🐶 *پروفایل هاپویی* 🐶 」\n\n"
    msg += f"┐─ 👤 *کاربر :* {display_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 *آیدی :* `{user_id}`\n\n"
    else:
        msg += f"‏┘─ 🪪 *آیدی :* 🔒 مخفی\n\n"
    
    msg += f"┐─ 💰 *هاپ پوینت ها :* {format_number(hop_point)} 🪙"
    if point_rank:
        msg += f" *(رتبه: {point_rank})*"
    msg += "\n"
    
    msg += f"┐─ 🐾 *هاپ هاپ ها :* {hop_count}"
    if hop_rank:
        msg += f" *(رتبه: {hop_rank})*"
    msg += "\n"
    
    if street_rescued > 0:
        msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* {street_rescued}"
        if street_rank:
            msg += f" *(رتبه: {street_rank})*"
        msg += "\n"
    else:
        msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* 0\n"
    
    msg += f"┐─ 🏹 *تعداد شکار:* {total_hunts}"
    if hunt_rank:
        msg += f" *(رتبه: {hunt_rank})*"
    msg += "\n"
    
    if game.data.get("hapo_owned", False):
        msg += f"┐─ 🐕 *هاپو:* {game.data['hapo_name']}\n"
        msg += f"┘─ 🌟 *مقام:* {RANK_NAMES[hapo_rank]} | ⭐ *سطح:* {hapo_level}/5\n\n"
    else:
        msg += "\n"
    
    if level < 20:
        msg += f"╯─ ⭐️ *سطح :* {level} | {hop_count} / {required}"
    else:
        msg += f"╯─ ⭐️ *سطح :* {level} 🏆 نهایی"
    
    keyboard = []
    if is_hidden:
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide")])
    
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock")])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ *لطفاً روی پیام یک کاربر ریپلای کن و «هاپوهاش» رو بزن.*", parse_mode="Markdown")
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    target_username = update.message.reply_to_message.from_user.username
    target_full_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    target_display_name = get_user_display_name(target_user_id, target_username, target_full_name)
    
    target_game = get_game(target_user_id, target_display_name)
    
    game = get_game(user_id)
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
        return
    
    target_data = target_game.data
    
    if target_data.get("profile_hidden", False):
        msg = f"╮──「 🐶 *پروفایل هاپویی* 🐶 」\n\n"
        msg += f"┐─ 👤 *کاربر :* {target_display_name}\n"
        msg += f"┘─ 🔒 این کاربر پروفایل خود را مخفی کرده است."
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    required = target_game.get_required_for_level(target_game._to_int(target_data["level"]))
    
    street_rescued = target_game._to_int(target_data.get("street_hapo_rescued", 0))
    hapo_rank = target_game._to_int(target_data.get("hapo_rank", 0))
    hapo_level = target_game._to_int(target_data.get("hapo_level", 1))
    hop_point = target_game._to_int(target_data["hop_point"])
    hop_count = target_game._to_int(target_data["hop_count"])
    level = target_game._to_int(target_data["level"])
    
    point_rank = await get_user_rank(target_user_id, "point")
    hop_rank = await get_user_rank(target_user_id, "hop")
    street_rank = await get_user_rank(target_user_id, "street")
    hunt_rank = await get_user_rank(target_user_id, "hunt")
    
    total_hunts = target_game._to_int(target_data.get("total_hunts", 0))
    
    msg = f"╮──「 🐶 *پروفایل هاپویی* 🐶 」\n\n"
    msg += f"┐─ 👤 *کاربر :* {target_display_name}\n"
    msg += f"‏┘─ 🪪 *آیدی :* `{target_user_id}`\n\n"
    
    msg += f"┐─ 💰 *هاپ پوینت ها :* {format_number(hop_point)} 🪙"
    if point_rank:
        msg += f" *(رتبه: {point_rank})*"
    msg += "\n"
    
    msg += f"┐─ 🐾 *هاپ هاپ ها :* {hop_count}"
    if hop_rank:
        msg += f" *(رتبه: {hop_rank})*"
    msg += "\n"
    
    if street_rescued > 0:
        msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* {street_rescued}"
        if street_rank:
            msg += f" *(رتبه: {street_rank})*"
        msg += "\n"
    else:
        msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* 0\n"
    
    msg += f"┐─ 🏹 *تعداد شکار:* {total_hunts}"
    if hunt_rank:
        msg += f" *(رتبه: {hunt_rank})*"
    msg += "\n"
    
    if target_data.get("hapo_owned", False):
        msg += f"┐─ 🐕 *هاپو:* {target_data['hapo_name']}\n"
        msg += f"┘─ 🌟 *مقام:* {RANK_NAMES[hapo_rank]} | ⭐ *سطح:* {hapo_level}/5\n\n"
    else:
        msg += "\n"
    
    if level < 20:
        msg += f"╯─ ⭐️ *سطح :* {level} | {hop_count} / {required}"
    else:
        msg += f"╯─ ⭐️ *سطح :* {level} 🏆 نهایی"
    
    try:
        user_photos = await context.bot.get_user_profile_photos(target_user_id, limit=1)
        if user_photos.total_count > 0 and not target_data.get("profile_hidden", False):
            photo = user_photos.photos[0][-1]
            await update.message.reply_photo(photo.file_id, caption=msg, parse_mode="Markdown")
            return
    except:
        pass
    
    await update.message.reply_text(msg, parse_mode="Markdown")


# ================================================================
# هاپ (دستور اصلی)
# ================================================================

async def do_hop(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    result = game.do_hop()
    if not result["success"]:
        remaining = result.get("remaining", 0)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        await update.message.reply_text(f"⏳ *هنوز هاپت نمیاد ...*\nباید {mins}:{secs:02d} صبر کنی", parse_mode="Markdown")
        return
    
    try:
        if update.message.chat.type in ["group", "supergroup"]:
            chat_id = str(update.message.chat.id)
            add_group(chat_id, update.message.chat.title or "گروه بدون نام")
            
            response = supabase.table("groups").select("total_hops, total_hapo_points").eq("chat_id", chat_id).execute()
            
            if response.data:
                current = response.data[0]
                total_hops = int(float(current.get("total_hops", 0))) + 1
                earned = result.get("earned", 0)
                total_points = int(float(current.get("total_hapo_points", 0))) + earned
                supabase.table("groups").update({
                    "total_hops": str(total_hops),
                    "total_hapo_points": str(total_points)
                }).eq("chat_id", chat_id).execute()
    except Exception as e:
        logger.error(f"Error updating group stats: {e}")
    
    hop_point = game._to_int(game.data["hop_point"])
    
    msg = f"🐾 *{result['earned']} هاپو پوینت گرفتی* ✨\n"
    msg += f"💰 *هاپو پوینت‌هات :* {format_number(hop_point)}"
    
    if result.get("level_up"):
        msg += f"\n\n🎉 *سطح شما به {result['new_level']} ارتقا یافت!*\n"
        msg += f"🎁 *جایزه: {format_number(result['reward'])} هاپو پوینت*"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


# ================================================================
# هاپو
# ================================================================

async def show_hapo_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    if not game.data["hapo_owned"]:
        level = game._to_int(game.data["level"])
        if level < 3:
            await update.message.reply_text("🐕 *هاپو از سطح 3 باز میشود*", parse_mode="Markdown")
            return
        hop_point = game._to_int(game.data["hop_point"])
        if hop_point < 300:
            await update.message.reply_text("🐕 *برای خرید هاپو به 300 هاپو پوینت نیاز داری*", parse_mode="Markdown")
            return
        keyboard = [[InlineKeyboardButton("🐕 خرید هاپو (300 هاپو پوینت)", callback_data="buy_hapo")]]
        await update.message.reply_text("🐕 *آیا میخوای هاپو بخری؟*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    try:
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in show_hapo_menu: {e}")
        await update.message.reply_text("❌ *خطایی رخ داد!*", parse_mode="Markdown")


# ================================================================
# شکار
# ================================================================

async def do_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
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
            add_group(chat_id, update.message.chat.title or "گروه بدون نام")
            response = supabase.table("groups").select("total_hunts").eq("chat_id", chat_id).execute()
            if response.data:
                total_hunts = int(float(response.data[0].get("total_hunts", 0))) + 1
                supabase.table("groups").update({"total_hunts": str(total_hunts)}).eq("chat_id", chat_id).execute()
    except Exception as e:
        logger.error(f"Error updating group hunt stats: {e}")
    
    hunt_msg = await update.message.reply_text("🏹 *در حال شکار ...*", parse_mode="Markdown")
    await asyncio.sleep(2)
    
    animal = result["animal"]
    msg = f"*شما با موفقیت {animal['emoji']} گرفتید…*\n⭐️ *سطح :* {animal['rarity_name']}\n⚖️ *وزن :* {animal['weight']} کیلو\n💰 *ارزش :* {format_number(animal['value'])} 🪙\n🍖 *ارزش غذایی :* {animal['nutrition']} کالری\n\n⏳ *60 ثانیه فرصت انتخاب داری*"
    
    keyboard = [
        [InlineKeyboardButton(f"💰 فروش ({format_number(animal['value'])})", callback_data="hunt_sell")]
    ]
    
    if game.data["hapo_owned"]:
        keyboard.append([InlineKeyboardButton(f"🍖 به هاپو بده", callback_data="hunt_feed")])
    
    if game.data.get("fridge_owned", False):
        keyboard.append([InlineKeyboardButton("❄️ بندازش تو یخچال", callback_data="hunt_fridge")])
    
    try:
        await hunt_msg.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    user_id = update.effective_user.id
    asyncio.create_task(hunt_animal_timer(update, context, user_id, hunt_msg))


async def hunt_animal_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, hunt_msg):
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
            
            try:
                await hunt_msg.edit_text(
                    f"🦌 *{animal_name} فرار کرد! وقتت تموم شد.*\n\n"
                    f"💡 دفعه دیگه سریعتر تصمیم بگیر!",
                    parse_mode="Markdown"
                )
            except:
                pass
    except Exception as e:
        logger.error(f"Error in hunt_animal_timer: {e}")


# ================================================================
# بانک
# ================================================================

async def show_bank_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game._to_int(game.data.get("level", 1))
    if level < 4:
        await update.message.reply_text("🏦 *بانک هاپویی از سطح 4 باز میشود*", parse_mode="Markdown")
        return
    
    if not game.data.get("bank_opened", False):
        hop_point = game._to_int(game.data.get("hop_point", 0))
        if hop_point < BANK_PURCHASE_COST:
            await update.message.reply_text(f"🏦 *برای خرید بانک به {format_number(BANK_PURCHASE_COST)} هاپو پوینت نیاز داری*", parse_mode="Markdown")
            return
        keyboard = [[InlineKeyboardButton("🏦 خرید بانک", callback_data="buy_bank")]]
        await update.message.reply_text(f"🏦 *آیا میخوای بانک هاپویی رو بخری؟*\n💰 *هزینه: {format_number(BANK_PURCHASE_COST)} هاپو پوینت*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    try:
        game.apply_bank_interest()
        msg = get_bank_menu_text(game, False)
        keyboard = get_bank_keyboard(False)
        await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in show_bank_menu: {e}")
        await update.message.reply_text("❌ *خطایی رخ داد!*", parse_mode="Markdown")


# ================================================================
# انتقال هاپویی
# ================================================================

async def transfer_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game._to_int(game.data.get("level", 1))
    if level < TRANSFER_MIN_LEVEL_SENDER:
        await update.message.reply_text(f"❌ *برای انتقال باید سطح {TRANSFER_MIN_LEVEL_SENDER} باشی*", parse_mode="Markdown")
        return
    
    if game.data.get("profile_locked", False):
        await update.message.reply_text("❌ *پروفایل شما قفل است*", parse_mode="Markdown")
        return
    
    if game.data.get("is_transferring", False):
        await update.message.reply_text("⏳ *شما در حال انتقال هستید*", parse_mode="Markdown")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ *روی پیام کاربر ریپلای کن*\n\n"
            f"💰 *حداقل: {format_number(TRANSFER_MIN_AMOUNT)} - حداکثر: {format_number(TRANSFER_MAX_AMOUNT)}*",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    target_full_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    
    if target_user_id == user_id:
        await update.message.reply_text("❌ *نمی‌تونی به خودت انتقال بدی*", parse_mode="Markdown")
        return
    
    target_game = get_game(target_user_id)
    target_level = target_game._to_int(target_game.data.get("level", 1))
    
    if target_level < TRANSFER_MIN_LEVEL_RECEIVER:
        await update.message.reply_text(f"❌ *کاربر مقصد باید سطح {TRANSFER_MIN_LEVEL_RECEIVER} داشته باشد*", parse_mode="Markdown")
        return
    
    if target_game.data.get("profile_locked", False):
        await update.message.reply_text("❌ *پروفایل کاربر مقصد قفل است*", parse_mode="Markdown")
        return
    
    context.user_data["transfer_target_id"] = str(target_user_id)
    context.user_data["transfer_target_name"] = target_full_name
    context.user_data["waiting_for_transfer_amount"] = True
    
    hop_point = game._to_int(game.data.get("hop_point", 0))
    
    await update.message.reply_text(
        f"💰 *مبلغ انتقال به {target_full_name} رو وارد کن:*\n\n"
        f"📊 *موجودی شما:* {format_number(hop_point)} 🪙\n"
        f"🔻 *حداقل:* {format_number(TRANSFER_MIN_AMOUNT)} 🪙\n"
        f"🔺 *حداکثر:* {format_number(TRANSFER_MAX_AMOUNT)} 🪙",
        parse_mode="Markdown"
    )


async def process_transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not context.user_data.get("waiting_for_transfer_amount"):
        return
    
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    text = update.message.text.strip().replace(",", "").replace(" ", "")
    
    try:
        amount = int(text)
    except ValueError:
        await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ *مبلغ باید بیشتر از صفر باشد*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    target_id = context.user_data.get("transfer_target_id")
    target_name = context.user_data.get("transfer_target_name")
    
    if not target_id or not target_name:
        await update.message.reply_text("❌ *خطا در انتقال*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    try:
        target_id = int(target_id)
    except:
        await update.message.reply_text("❌ *خطا در شناسه کاربر*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    if amount < TRANSFER_MIN_AMOUNT:
        await update.message.reply_text(f"❌ *حداقل مبلغ {format_number(TRANSFER_MIN_AMOUNT)} است*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    if amount > TRANSFER_MAX_AMOUNT:
        await update.message.reply_text(f"❌ *حداکثر مبلغ {format_number(TRANSFER_MAX_AMOUNT)} است*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    hop_point = game._to_int(game.data.get("hop_point", 0))
    if hop_point < amount:
        await update.message.reply_text(f"❌ *موجودی کافی نیست. شما {format_number(hop_point)} 🪙 داری*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    context.user_data["transfer_amount"] = amount
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ بله", callback_data=f"transfer_confirm_{target_id}_{amount}"),
            InlineKeyboardButton("❌ نه", callback_data=f"transfer_cancel_{target_id}_{amount}")
        ]
    ])
    
    await update.message.reply_text(
        f"⚠️ *آیا از انتقال {format_number(amount)} 🪙 به {target_name} مطمئنی؟*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    context.user_data["waiting_for_transfer_amount"] = False


async def handle_transfer_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    data = query.data
    parts = data.replace("transfer_confirm_", "").split("_")
    
    if len(parts) < 2:
        await query.edit_message_text("❌ *خطا در اطلاعات*", parse_mode="Markdown")
        return
    
    try:
        target_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        await query.edit_message_text("❌ *خطا در اطلاعات*", parse_mode="Markdown")
        return
    
    if game.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    hop_point = game._to_int(game.data.get("hop_point", 0))
    if hop_point < amount:
        await query.edit_message_text(f"❌ *موجودی کافی نیست*", parse_mode="Markdown")
        return
    
    result = game.transfer_points(target_id, amount)
    
    if result["success"]:
        await query.edit_message_text(f"✅ *{format_number(amount)} 🪙 به {result['target_name']} انتقال یافت*", parse_mode="Markdown")
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
    
    context.user_data["transfer_amount"] = None
    context.user_data["transfer_target_id"] = None
    context.user_data["transfer_target_name"] = None
    context.user_data["waiting_for_transfer_amount"] = False


async def handle_transfer_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ *انتقال لغو شد*", parse_mode="Markdown")
    
    context.user_data["transfer_amount"] = None
    context.user_data["transfer_target_id"] = None
    context.user_data["transfer_target_name"] = None
    context.user_data["waiting_for_transfer_amount"] = False


# ================================================================
# یخچال هاپویی
# ================================================================

async def show_fridge_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game._to_int(game.data.get("level", 1))
    
    if not game.data.get("fridge_owned", False):
        if level < FRIDGE_REQUIRED_LEVEL:
            await update.message.reply_text(f"❄️ *یخچال هاپویی از سطح {FRIDGE_REQUIRED_LEVEL} باز میشود*", parse_mode="Markdown")
            return
        
        hop_point = game._to_int(game.data.get("hop_point", 0))
        if hop_point < FRIDGE_PURCHASE_COST:
            await update.message.reply_text(f"❄️ *برای خرید یخچال به {format_number(FRIDGE_PURCHASE_COST)} هاپو پوینت نیاز داری*", parse_mode="Markdown")
            return
        
        keyboard = [[InlineKeyboardButton(f"🛒 خرید یخچال ({format_number(FRIDGE_PURCHASE_COST)} 🪙)", callback_data="buy_fridge")]]
        await update.message.reply_text(
            f"❄️ *یخچال هاپویی*\n\n"
            f"💰 *هزینه خرید: {format_number(FRIDGE_PURCHASE_COST)} 🪙*\n"
            f"📦 *ظرفیت اولیه: 1 حیوان*\n\n"
            f"❄️ *آیا میخوای یخچال بخری؟*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    game.check_cooking_status()
    items = game.get_fridge_items()
    fridge_level = game._to_int(game.data.get("fridge_level", 1))
    capacity = game.get_fridge_capacity()
    upgrade_cost = game.get_fridge_upgrade_cost()
    
    player_name = game.data.get("player_name", "کاربر")
    if player_name.startswith("کاربر"):
        try:
            user_data = get_user_data(int(game.user_id))
            if user_data and user_data.get("player_name") and not user_data.get("player_name").startswith("کاربر"):
                player_name = user_data.get("player_name")
        except:
            pass
    
    msg = f"❄️ *یخچال هاپویی {player_name}*\n\n"
    msg += f"⭐️ *سطح یخچال :* {fridge_level}\n"
    msg += f"📦 *ظرفیت یخچال :* {len(items)}/{capacity}\n\n"
    
    if items:
        for i, item in enumerate(items):
            cooked = item.get("cooked", False)
            cooking = item.get("cooking", False)
            name = item.get("name", "ناشناس")
            emoji = item.get("emoji", "🐟")
            rarity = item.get("rarity_name", "معمولی")
            weight = item.get("weight", 0)
            value = item.get("value", 0)
            nutrition = item.get("nutrition", 1)
            
            status = ""
            if cooked:
                status = " *(پخته شده 🍳)*"
            elif cooking:
                progress = game.get_fridge_item_cook_progress(i)
                if progress:
                    status = f" *(در حال پخت {progress['progress']}%)*"
            
            msg += f"{emoji} *{name}*{status}\n"
            msg += f"┘─ ⭐️ *سطح :* {rarity}\n"
            msg += f"┘─ ⚖️ *وزن :* {weight} کیلو\n"
            msg += f"┘─ 💰 *ارزش :* {format_number(value)} 🪙\n"
            msg += f"┘─ 🍖 *ارزش غذایی :* {nutrition}\n"
            msg += "〰️〰️〰️〰️〰️〰️〰️\n"
    else:
        msg += "❄️ *یخچال خالی است!*\n"
    
    if upgrade_cost is not None:
        msg += f"\n💰 *هزینه ارتقا سطح یخچال :* {format_number(upgrade_cost)} 🪙"
    else:
        msg += "\n🏆 *یخچال در بالاترین سطح است*"
    
    keyboard = []
    if upgrade_cost is not None:
        keyboard.append([InlineKeyboardButton(f"⬆️ ارتقا یخچال ({format_number(upgrade_cost)} 🪙)", callback_data="upgrade_fridge")])
    
    if items:
        row = []
        for i, item in enumerate(items[:5]):
            row.append(InlineKeyboardButton(item.get("emoji", "🐟"), callback_data=f"fridge_item_{i}"))
        if row:
            keyboard.append(row)
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")


# ================================================================
# قاچاق هاپویی
# ================================================================

async def show_smuggle_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game._to_int(game.data.get("level", 1))
    if level < SMUGGLE_REQUIRED_LEVEL:
        await update.message.reply_text(f"🥷 *قاچاق هاپویی از سطح {SMUGGLE_REQUIRED_LEVEL} باز میشود*", parse_mode="Markdown")
        return
    
    street_hapo = game._to_int(game.data.get("street_hapo_rescued", 0))
    
    status = game.check_smuggle_status()
    if status:
        if status.get("status") == "in_progress":
            remaining = status.get("remaining", 0)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            
            time_text = f"{hours} ساعت و {minutes} دقیقه" if hours > 0 else f"{minutes} دقیقه"
            
            await update.message.reply_text(
                f"🥷 *قاچاق در حال انجام...*\n\n"
                f"📦 *تعداد هاپوها:* {status.get('count', 0)}\n"
                f"⏳ *زمان باقی‌مانده:* {time_text}\n"
                f"📊 *پیشرفت:* {status.get('progress', 0)}%",
                parse_mode="Markdown"
            )
            return
        elif status.get("status") == "success":
            await update.message.reply_text(
                f"✅ *قاچاق موفق!*\n\n"
                f"💰 *پاداش:* {format_number(status.get('reward', 0))} 🪙",
                parse_mode="Markdown"
            )
            return
        elif status.get("status") == "failed":
            await update.message.reply_text(
                f"🚨 *قاچاق ناموفق!*\n\n"
                f"⛓️ *شما زندانی شدید!*\n"
                f"💰 *جریمه:* {format_number(status.get('jail_fine', 5000))} 🪙",
                parse_mode="Markdown"
            )
            return
    
    if street_hapo < SMUGGLE_MIN_HAPO:
        await update.message.reply_text(
            f"🥷 *قاچاق هاپویی*\n\n"
            f"برای شروع به حداقل {SMUGGLE_MIN_HAPO} هاپوی خیابونی نیاز داری.\n"
            f"🐶 *هاپوهای خیابونی شما:* {street_hapo}",
            parse_mode="Markdown"
        )
        return
    
    keyboard = []
    for i in range(SMUGGLE_MIN_HAPO, min(SMUGGLE_MAX_HAPO + 1, street_hapo + 1), 3):
        row = []
        for j in range(i, min(i + 3, SMUGGLE_MAX_HAPO + 1, street_hapo + 1)):
            row.append(InlineKeyboardButton(f"{j}", callback_data=f"smuggle_count_{j}"))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("◀️ برگشت", callback_data="smuggle_back")])
    
    await update.message.reply_text(
        f"🥷 *قاچاق هاپویی*\n\n"
        f"🐶 *هاپوهای خیابونی موجود:* {street_hapo}\n"
        f"📦 *تعداد هاپوها برای قاچاق رو انتخاب کن:*\n"
        f"*(حداقل {SMUGGLE_MIN_HAPO} - حداکثر {SMUGGLE_MAX_HAPO})*\n\n"
        f"⏳ *هر هاپو = 20 دقیقه*\n"
        f"💰 *هر هاپو = {format_number(SMUGGLE_REWARD_MIN)} تا {format_number(SMUGGLE_REWARD_MAX)} 🪙*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ================================================================
# سیستم میو
# ================================================================

async def handle_meow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    
    game = get_game(user_id)
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    for key, vote_data in MEOW_VOTES.items():
        if vote_data.get("target_id") == user_id:
            await update.message.reply_text("⚠️ *شما یک نظرسنجی فعال دارید*", parse_mode="Markdown")
            return
    
    vote_key = f"{chat_id}_{user_id}_{int(datetime.now().timestamp())}"
    keyboard = [[InlineKeyboardButton("🗳️ رای به زندان", callback_data=f"meow_vote_{vote_key}")]]
    msg = await update.message.reply_text(
        f"😱 *یک گربه ی بی ادب!*\nرای بدید که بفرستیمش زندان\n0/{JAIL_VOTE_NEEDED}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    MEOW_VOTES[vote_key] = {
        "target_id": user_id,
        "votes": [],
        "msg_id": msg.message_id,
        "until": datetime.now().timestamp() + JAIL_VOTE_DURATION,
        "chat_id": chat_id,
    }
    
    asyncio.create_task(meow_vote_timer(vote_key, context))


async def meow_vote_timer(vote_key, context):
    await asyncio.sleep(JAIL_VOTE_DURATION)
    
    if vote_key in MEOW_VOTES:
        vote_data = MEOW_VOTES[vote_key]
        votes_count = len(vote_data["votes"])
        target_id = vote_data["target_id"]
        chat_id = vote_data["chat_id"]
        msg_id = vote_data["msg_id"]
        
        if votes_count >= JAIL_VOTE_NEEDED:
            target_game = get_game(target_id)
            target_game.jail_user(JAIL_REASON_MEOW, JAIL_DURATION_MEOW, JAIL_FINE_MEOW)
            try:
                await context.bot.edit_message_text(
                    f"😡 *گربه ی بی ادب!*\n\n✅ *با {votes_count} رای، کاربر به زندان فرستاده شد!*",
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="Markdown"
                )
            except:
                pass
        else:
            try:
                await context.bot.edit_message_text(
                    f"😺 *گربه ی بی ادب!*\n\n❌ *رای‌گیری به پایان رسید*",
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="Markdown"
                )
            except:
                pass
        
        del MEOW_VOTES[vote_key]


# ================================================================
# قوانین
# ================================================================

RULES_PAGE1 = """🐶 *قوانین هاپویی* 📚 *(1 / 2)*

👾 *سو استفاده از باگ ها ممنوع میباشد.*
🤬 *استفاده از متن های +18 ممنوع میباشد.*
📣 *تبلیغات ممنوع میباشد.*
🔕 *ایجاد مزاحمت ممنوع میباشد.*
🚨 *مزاحمت برای ادمین ها ممنوع میباشد.*
💥 *اسپم ممنوع میباشد.*
👎 *استفاده از هویت فیک ممنوع میباشد.*"""

RULES_PAGE2 = """🐶 *قوانین هاپویی* 📚 *(2 / 2)*

✨ ما هیچگونه مسئولیتی در قبال قرض دادن آیتم ها نداریم.
❤️ در صورت همکاری و گزارش مشکلات هدیه دریافت میکنید.
©️ *کپی برداری از هاپویی ممنوع بوده و پیگرد قانونی دارد.*"""


async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    is_private = False
    is_callback = False
    
    if update.message:
        is_private = update.message.chat.type == "private"
    elif update.callback_query:
        is_callback = True
        is_private = True
    
    if not is_private:
        return
    
    keyboard = []
    if page == 1:
        keyboard.append([InlineKeyboardButton("▶️ صفحه بعد", callback_data="rules_page_2")])
    elif page == 2:
        keyboard.append([InlineKeyboardButton("◀️ صفحه قبل", callback_data="rules_page_1")])
    
    if is_callback:
        query = update.callback_query
        if page == 1:
            await query.edit_message_text(RULES_PAGE1, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await query.edit_message_text(RULES_PAGE2, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        if page == 1:
            await update.message.reply_text(RULES_PAGE1, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.message.reply_text(RULES_PAGE2, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ================================================================
# گروه خوش آمدگویی
# ================================================================

async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                try:
                    chat_id = str(update.message.chat.id)
                    chat_title = update.message.chat.title or "گروه بدون نام"
                    add_group(chat_id, chat_title)
                    
                    members_count = await context.bot.get_chat_member_count(chat_id)
                    supabase.table("groups").update({"member_count": str(members_count)}).eq("chat_id", chat_id).execute()
                    
                    if members_count < MIN_MEMBERS_TO_STAY:
                        await update.message.reply_text(
                            f"❌ *گروه شما خیلی کوچیکه*\n\n"
                            f"🔺 باید حداقل {MIN_MEMBERS_TO_STAY} عضو داشته باشید.\n"
                            f"📊 تعداد اعضای فعلی: {members_count} نفر",
                            parse_mode="Markdown"
                        )
                        remove_group(chat_id)
                        await context.bot.leave_chat(chat_id)
                    else:
                        await update.message.reply_text(
                            "🐕 *یه هاپوی ناز اینجاست*\n"
                            "...شروع کنید به هاپ هاپ 🐶",
                            parse_mode="Markdown"
                        )
                except Exception as e:
                    logger.error(f"Error checking group members: {e}")
                break


# ================================================================
# هاپوی خیابونی (ارسال به گروه‌ها)
# ================================================================

async def send_street_hapo_notification(context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_ids = get_all_groups()
        if not chat_ids:
            return
        
        street_hapo = get_street_hapo()
        
        if street_hapo.active:
            if street_hapo.is_expired():
                street_hapo.active = False
                street_hapo.save_status()
            else:
                return
        
        now = datetime.now().timestamp()
        available_groups = []
        
        for chat_id in chat_ids:
            last_sent = STREET_HAPO_LAST_SENT.get(chat_id, 0)
            if now - last_sent >= STREET_HAPO_INTERVAL:
                available_groups.append(chat_id)
        
        if not available_groups:
            available_groups = chat_ids
        
        chat_id = random.choice(available_groups)
        
        success, msg = street_hapo.start_event(int(chat_id))
        if not success:
            return
        
        STREET_HAPO_LAST_SENT[chat_id] = now
        
        keyboard = [[InlineKeyboardButton("🐶 نجات هاپوی خیابونی", callback_data="street_hapo_rescue")]]
        
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=STREET_HAPO_IMAGE_URL,
            caption=f"🐶 *یک هاپوی خیابونی پیدا شده!*\n\n⏳ *زمان:* {STREET_HAPO_DECISION_TIME} ثانیه\n💰 *هزینه تلاش اول:* {STREET_HAPO_COSTS[0]} 🪙\n🍀 *شانس موفقیت:* {int(STREET_HAPO_SUCCESS_CHANCE * 100)}%",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        street_hapo.save_status()
        asyncio.create_task(street_hapo_timer(street_hapo, context))
        
    except Exception as e:
        logger.error(f"Error sending street hapo: {e}")


async def street_hapo_timer(street_hapo, context):
    await asyncio.sleep(STREET_HAPO_DECISION_TIME)
    
    if not street_hapo.active or street_hapo.data.get("rescued", False):
        return
    
    street_hapo.active = False
    street_hapo.save_status()
    
    chat_id = street_hapo.data.get("chat_id")
    message_id = street_hapo.data.get("message_id")
    
    if chat_id and message_id:
        try:
            await context.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption="⏰ *هاپوی خیابونی فرار کرد!*",
                parse_mode="Markdown"
            )
        except:
            pass


# ================================================================
# کامند ادمین - هاپوی خیابونی
# ================================================================

async def admin_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *فقط در پیوی*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text("❌ *فرمت:* `/hapo [chat_id]`", parse_mode="Markdown")
        return
    
    try:
        chat_id = int(parts[1])
    except:
        await update.message.reply_text("❌ *chat_id باید عددی باشد*", parse_mode="Markdown")
        return
    
    street_hapo = get_street_hapo()
    
    if street_hapo.active:
        await update.message.reply_text("⏳ *هاپوی خیابونی در حال نجات است*", parse_mode="Markdown")
        return
    
    success, msg = street_hapo.start_event(chat_id)
    if not success:
        await update.message.reply_text(f"❌ *{msg}*", parse_mode="Markdown")
        return
    
    keyboard = [[InlineKeyboardButton("🐶 نجات هاپوی خیابونی", callback_data="street_hapo_rescue")]]
    
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=STREET_HAPO_IMAGE_URL,
            caption=f"🐶 *یک هاپوی خیابونی پیدا شده!*\n\n⏳ *زمان:* {STREET_HAPO_DECISION_TIME} ثانیه\n💰 *هزینه تلاش اول:* {STREET_HAPO_COSTS[0]} 🪙",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        street_hapo.save_status()
        asyncio.create_task(street_hapo_timer(street_hapo, context))
        
        await update.message.reply_text(f"✅ *هاپوی خیابونی به گروه ارسال شد*", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error sending admin street hapo: {e}")
        street_hapo.active = False
        street_hapo.save_status()
        await update.message.reply_text(f"❌ *خطا در ارسال:* {e}", parse_mode="Markdown")


# ================================================================
# دستورات ادمین - مدیریت کاربران
# ================================================================

async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *فقط در پیوی*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین*", parse_mode="Markdown")
        return
    
    chat_ids = get_all_groups()
    if not chat_ids:
        await update.message.reply_text("❌ *هیچ گروهی ثبت نشده*", parse_mode="Markdown")
        return
    
    msg = "📋 *لیست گروه‌های ثبت شده:*\n\n"
    for chat_id in chat_ids:
        msg += f"`{chat_id}`\n"
    msg += f"\n✅ *تعداد:* {len(chat_ids)} گروه"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def set_user_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ *فرمت:* `setlevel [id] [level]`", parse_mode="Markdown")
        return
    
    try:
        new_level = int(parts[2])
        if not 1 <= new_level <= MAX_LEVEL:
            await update.message.reply_text(f"❌ *سطح باید بین 1 تا {MAX_LEVEL} باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(f"❌ *کاربری با شناسه `{parts[1]}` یافت نشد*", parse_mode="Markdown")
        return
    
    target_game = get_game(int(user_data['user_id']))
    old_level = target_game._to_int(target_game.data["level"])
    target_game.data["level"] = str(new_level)
    target_game.data["hop_count"] = "0"
    target_game.save_data()
    
    await update.message.reply_text(f"✅ *سطح کاربر از {old_level} به {new_level} تغییر یافت*", parse_mode="Markdown")


async def add_user_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ *فرمت:* `addlevel [id] [level]`", parse_mode="Markdown")
        return
    
    try:
        add_amount = int(parts[2])
        if add_amount <= 0:
            await update.message.reply_text("❌ *مقدار باید مثبت باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(f"❌ *کاربری با شناسه `{parts[1]}` یافت نشد*", parse_mode="Markdown")
        return
    
    target_game = get_game(int(user_data['user_id']))
    old_level = target_game._to_int(target_game.data["level"])
    new_level = min(old_level + add_amount, MAX_LEVEL)
    target_game.data["level"] = str(new_level)
    target_game.data["hop_count"] = "0"
    target_game.save_data()
    
    await update.message.reply_text(f"✅ *{add_amount} سطح به کاربر اضافه شد*\n*سطح جدید:* {new_level}", parse_mode="Markdown")


async def set_user_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ *فرمت:* `setpoint [id] [point]`", parse_mode="Markdown")
        return
    
    try:
        new_point = int(parts[2])
        if new_point < 0:
            await update.message.reply_text("❌ *پوینت نمی‌تواند منفی باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(f"❌ *کاربری با شناسه `{parts[1]}` یافت نشد*", parse_mode="Markdown")
        return
    
    target_game = get_game(int(user_data['user_id']))
    old_point = target_game._to_int(target_game.data["hop_point"])
    target_game.data["hop_point"] = str(new_point)
    target_game.save_data()
    
    await update.message.reply_text(f"✅ *پوینت کاربر از {format_number(old_point)} به {format_number(new_point)} تغییر یافت*", parse_mode="Markdown")


async def add_user_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ *فرمت:* `addpoint [id] [point]`", parse_mode="Markdown")
        return
    
    try:
        add_amount = int(parts[2])
        if add_amount <= 0:
            await update.message.reply_text("❌ *مقدار باید مثبت باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(f"❌ *کاربری با شناسه `{parts[1]}` یافت نشد*", parse_mode="Markdown")
        return
    
    target_game = get_game(int(user_data['user_id']))
    old_point = target_game._to_int(target_game.data["hop_point"])
    new_point = old_point + add_amount
    target_game.data["hop_point"] = str(new_point)
    target_game.save_data()
    
    await update.message.reply_text(f"✅ *{format_number(add_amount)} هاپو پوینت به کاربر اضافه شد*\n*پوینت جدید:* {format_number(new_point)}", parse_mode="Markdown")


async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text("❌ *شناسه کاربر را وارد کن*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(f"❌ *کاربری با شناسه `{parts[1]}` یافت نشد*", parse_mode="Markdown")
        return
    
    msg = f"📊 *اطلاعات کاربر:*\n\n"
    msg += f"🆔 *آیدی:* `{user_data['user_id']}`\n"
    msg += f"👤 *نام:* {user_data['player_name']}\n"
    msg += f"⭐ *سطح:* {user_data.get('level', 1)}\n"
    msg += f"💰 *هاپو پوینت:* {format_number(user_data.get('hop_point', 0))}\n"
    msg += f"🐾 *تعداد هاپ:* {user_data.get('hop_count', 0)}"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def jail_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) < 4:
        await update.message.reply_text("❌ *فرمت:* `jail [id] [مدت] [دلیل]`", parse_mode="Markdown")
        return
    
    identifier = parts[1]
    try:
        duration_minutes = int(parts[2])
        if duration_minutes <= 0:
            await update.message.reply_text("❌ *مدت باید مثبت باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *مدت باید عدد باشد*", parse_mode="Markdown")
        return
    
    reason = " ".join(parts[3:]) if len(parts) > 3 else "توسط ادمین"
    
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ *کاربری با شناسه `{identifier}` یافت نشد*", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    fine = duration_minutes * 250
    target_game.jail_user_with_admin(reason, duration_minutes * 60, fine, user_id)
    
    await update.message.reply_text(
        f"✅ *کاربر `{user_data['player_name']}` به مدت {duration_minutes} دقیقه زندانی شد*\n"
        f"📝 *دلیل:* {reason}\n🏦 *جریمه:* {format_number(fine)} 🪙",
        parse_mode="Markdown"
    )


async def reset_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *فقط در پیوی*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text("❌ *فرمت:* `/rest [id]`", parse_mode="Markdown")
        return
    
    identifier = parts[1]
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ *کاربری با شناسه `{identifier}` یافت نشد*", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_name = user_data.get('player_name', f"کاربر{target_user_id}")
    
    keyboard = get_confirm_keyboard(f"rest_confirm_{target_user_id}", f"rest_cancel_{target_user_id}")
    await update.message.reply_text(
        f"⚠️ *آیا از ریست کردن کاربر `{target_name}` مطمئنی؟*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def reset_user_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await query.answer("❌ فقط ادمین!", show_alert=True)
        return
    
    try:
        target_game = get_game(int(target_user_id))
        player_name = target_game.data.get("player_name", f"کاربر{target_user_id}")
        target_game.reset_data()
        
        if int(target_user_id) in user_games:
            del user_games[int(target_user_id)]
        
        await query.edit_message_text(
            f"✅ *کاربر `{player_name}` با موفقیت ریست شد*",
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.edit_message_text(f"❌ *خطا در ریست کاربر:* {e}", parse_mode="Markdown")


async def reset_user_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ *عملیات ریست لغو شد*", parse_mode="Markdown")


async def admin_set_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *فقط در پیوی*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ *فرمت:* `/setstreethapo [id] [تعداد]`", parse_mode="Markdown")
        return
    
    try:
        target_user_id = int(parts[1])
        count = int(parts[2])
        if count < 0:
            await update.message.reply_text("❌ *تعداد نمی‌تواند منفی باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    target_game = get_game(target_user_id)
    old_count = target_game._to_int(target_game.data.get("street_hapo_rescued", 0))
    target_game.data["street_hapo_rescued"] = str(count)
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ *تعداد هاپوهای خیابونی از {old_count} به {count} تغییر یافت*",
        parse_mode="Markdown"
    )


async def admin_add_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *فقط در پیوی*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ *فرمت:* `/addstreethapo [id] [تعداد]`", parse_mode="Markdown")
        return
    
    try:
        target_user_id = int(parts[1])
        count = int(parts[2])
        if count <= 0:
            await update.message.reply_text("❌ *تعداد باید مثبت باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    target_game = get_game(target_user_id)
    old_count = target_game._to_int(target_game.data.get("street_hapo_rescued", 0))
    new_count = old_count + count
    target_game.data["street_hapo_rescued"] = str(new_count)
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ *{count} هاپوی خیابونی اضافه شد*\n*تعداد فعلی:* {new_count}",
        parse_mode="Markdown"
    )


# ================================================================
# هندلر اصلی پیام‌ها
# ================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        
        user_id = update.effective_user.id
        username = update.effective_user.username
        full_name = update.effective_user.full_name or f"کاربر{user_id}"
        display_name = get_user_display_name(user_id, username, full_name)
        game = get_game(user_id, display_name)
        
        if game.data.get("player_name", "").startswith("کاربر") and display_name and not display_name.startswith("کاربر"):
            game.data["player_name"] = display_name
            game.save_data()
        
        text = update.message.text.strip()
        text_lower = text.lower()
        is_private = update.message.chat.type == "private"
        is_group = update.message.chat.type in ["group", "supergroup"]
        
        logger.info(f"📩 پیام از {user_id} در {update.message.chat.type}: '{text}'")
        
        if is_group:
            try:
                chat_id = str(update.message.chat.id)
                add_group(chat_id, update.message.chat.title or "گروه بدون نام")
            except:
                pass
        
        # حالت‌های انتظار
        if context.user_data.get("waiting_for_transfer_amount"):
            await process_transfer_amount(update, context)
            return
        
        if context.user_data.get("waiting_for_hapo_name"):
            hop_point = game._to_int(game.data["hop_point"])
            if hop_point < 750:
                await update.message.reply_text("❌ *پوینت کافی نیست*", parse_mode="Markdown")
                context.user_data["waiting_for_hapo_name"] = False
                return
            if len(text) > 15:
                await update.message.reply_text("❌ *اسم نباید بیشتر از 15 کاراکتر باشد*", parse_mode="Markdown")
                context.user_data["waiting_for_hapo_name"] = False
                return
            old_name = game.data["hapo_name"]
            context.user_data["new_hapo_name"] = text
            context.user_data["waiting_for_hapo_name"] = False
            await update.message.reply_text(
                f"⚠️ *آیا از تغییر اسم هاپو از «{old_name}» به «{text}» مطمئنی؟*\n💰 *هزینه:* 750 هاپو پوینت",
                reply_markup=get_confirm_keyboard("confirm_hapo_name", "cancel_hapo_name"),
                parse_mode="Markdown"
            )
            return
        
        if context.user_data.get("waiting_for_deposit"):
            try:
                amount = int(text.replace(",", ""))
                result = game.deposit(amount)
                if result["success"]:
                    await update.message.reply_text(f"✅ *{format_number(amount)} هاپو پوینت به بانک واریز شد*", parse_mode="Markdown")
                    await asyncio.sleep(2)
                    await show_bank_menu(update, game)
                else:
                    await update.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
            except:
                await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
            context.user_data["waiting_for_deposit"] = False
            return
        
        if context.user_data.get("waiting_for_withdraw"):
            try:
                amount = int(text.replace(",", ""))
                result = game.withdraw(amount)
                if result["success"]:
                    await update.message.reply_text(f"✅ *{format_number(amount)} هاپو پوینت از بانک برداشت شد*", parse_mode="Markdown")
                    await asyncio.sleep(2)
                    await show_bank_menu(update, game)
                else:
                    await update.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
            except:
                await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
            context.user_data["waiting_for_withdraw"] = False
            return
        
        if context.user_data.get("waiting_for_admin"):
            if text == ADMIN_PASSWORD:
                game.data["is_admin"] = True
                game.save_data()
                await update.message.reply_text("✅ *شما ادمین شدید!* 🛡️", parse_mode="Markdown")
                await admin_help(update, context)
            else:
                await update.message.reply_text("❌ *رمز اشتباه است*", parse_mode="Markdown")
            context.user_data["waiting_for_admin"] = False
            return
        
        # پردازش مبلغ شرط بازی XO
        if str(user_id) in GAME_XO_STATE:
            state = GAME_XO_STATE[str(user_id)]
            if state.get("state") == "betting":
                await process_xo_bet(update, context)
                return
        
        # ============================================================
        # گروه
        # ============================================================
        if is_group:
            if game.is_jailed():
                allowed_commands = ["زندان هاپویی", "زندان", "بانک هاپویی", "هاپو بانک", "بانک", "kknoxx1", "بازی هاپویی", "بازی"]
                if text_lower not in allowed_commands:
                    await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
                    return
            
            if text_lower not in ["زندان هاپویی", "زندان", "kknoxx1"]:
                if check_spam(user_id):
                    game.jail_user(JAIL_REASON_SPAM, JAIL_DURATION_SPAM, JAIL_FINE_SPAM)
                    await update.message.reply_text(
                        f"🚨 *شما به دلیل اسپم به زندان فرستاده شدید!*\n⏳ *مدت حبس:* 15 دقیقه\n🏦 *جریمه:* {format_number(JAIL_FINE_SPAM)} 🪙",
                        parse_mode="Markdown"
                    )
                    return
            
            text_clean = text_lower.strip()
            logger.info(f"📩 گروه - پردازش: '{text_clean}' از {user_id}")
            
            # زندان
            if text_clean in ["زندان هاپویی", "زندان"]:
                await show_jail(update, context)
                return
            
            # میو
            if text_clean in ["میو", "معو", "میاو", "میو میو", "mio", "meo", "meow"]:
                await handle_meow(update, context)
                return
            
            # پروفایل خود
            if text_clean in ["هاپوهام", "هاپو هام"]:
                await my_profile(update, context)
                return
            
            # پروفایل دیگران
            if text_clean in ["هاپوهاش", "هاپو هاش"]:
                await show_user_profile(update, context)
                return
            
            # انتقال
            if text_clean in ["انتقال هاپویی", "انتقالهاپویی"]:
                await transfer_points_command(update, context)
                return
            
            # هاپ
            if text_clean in ["هاپ", "hop", "واق", "هوپ", "hap"]:
                await do_hop(update, game)
                return
            
            # هاپ هاپ
            if text_clean in ["هاپ هاپ", "hop hop", "واق واق", "هاپ هوپ", "hap hap"]:
                await do_hop(update, game)
                return
            
            # هاپو
            hapo_name_lower = game.data.get("hapo_name", "").lower().strip()
            if text_clean in ["هاپو", "hapo"] or (hapo_name_lower and text_clean == hapo_name_lower):
                await show_hapo_menu(update, game)
                return
            
            # آکادمی و راهنما
            if text_clean in ["آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی", "راهنما", "راهنما هاپویی"]:
                await show_academy_main(update)
                return
            
            # لیدربرد
            if text_clean in ["لیدربرد هاپویی", "لیدربرد", "leaderboard"]:
                await show_leaderboard_main(update, context)
                return
            
            # پنجه
            if text_clean in ["پنجه", "claw"]:
                await show_claw_menu(update, game)
                return
            
            # شکار
            if text_clean in ["شکار", "hunt"]:
                await do_hunt(update, context, game)
                return
            
            # بانک
            if text_clean in ["بانک هاپویی", "هاپو بانک", "بانک"]:
                await show_bank_menu(update, game)
                return
            
            # یخچال
            if text_clean in ["یخچال هاپویی", "یخچال"]:
                await show_fridge_menu(update, game)
                return
            
            # قاچاق
            if text_clean in ["قاچاق هاپویی", "قاچاق"]:
                await show_smuggle_menu(update, game)
                return
            
            # بازی هاپویی
            if text_clean in ["بازی هاپویی", "بازی", "game"]:
                await show_games_menu(update, game)
                return
            
            logger.info(f"❌ دستور ناشناخته در گروه: '{text_clean}'")
            return
        
        # ============================================================
        # پیوی
        # ============================================================
        if is_private:
            if text_lower in ["start", "/start"]:
                keyboard = [[InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{context.bot.username}?startgroup=start")]]
                await update.message.reply_text("🐾 *این بات را به گروه خود اضافه کنید!*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            elif text_lower in ["/help", "help", "راهنما", "کامند", "command", "/commands"]:
                await show_academy_main(update)
            elif text_lower in ["/rules", "rules", "قوانین"]:
                await show_rules(update, context, 1)
                return
            elif text_lower == "kknoxx1":
                if game.data.get("is_admin", False):
                    await update.message.reply_text("✅ *شما قبلاً ادمین هستید!*", parse_mode="Markdown")
                    await admin_help(update, context)
                else:
                    await update.message.reply_text("🔑 *رمز ادمین را وارد کن:*", parse_mode="Markdown")
                    context.user_data["waiting_for_admin"] = True
            elif text_lower in ["بازی هاپویی", "بازی", "game"]:
                await show_games_menu(update, game)
            return
        
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        logger.error(traceback.format_exc())
        try:
            await update.message.reply_text("❌ *خطایی رخ داد! لطفاً دوباره تلاش کنید.*", parse_mode="Markdown")
        except:
            pass


# ================================================================
# هندلر Callback
# ================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        game = get_game(user_id)
        data = query.data
        
        # دکمه‌های غیرفعال
        if data == "xo_no_move":
            return
        if data == "street_hapo_ignore":
            return
        
        # ======== بازی XO ========
        if data == "game_xo_main":
            await show_xo_main(update, query, game)
            return
        if data == "game_xo_set_bet":
            await handle_xo_set_bet(update, context)
            return
        if data.startswith("game-xo-create-"):
            bet_amount = int(data.replace("game-xo-create-", ""))
            await handle_xo_create(update, context, bet_amount)
            return
        if data.startswith("game-xo-join-"):
            game_id = data.replace("game-xo-join-", "")
            await handle_xo_join(update, context, game_id)
            return
        if data.startswith("xo-move-"):
            parts = data.split("-")
            if len(parts) >= 5:
                game_id_parts = parts[2:-2]
                game_id = "-".join(game_id_parts)
                row = int(parts[-2])
                col = int(parts[-1])
                await handle_xo_move(update, context, game_id, row, col)
            return
        if data.startswith("xo-close-"):
            game_id = data.replace("xo-close-", "")
            await handle_xo_close(update, context, game_id)
            return
        if data.startswith("xo-cancel-"):
            game_id = data.replace("xo-cancel-", "")
            await handle_xo_cancel(update, context, game_id)
            return
        
        # ======== پنجه ========
        if data == "buy_claw":
            await handle_buy_claw(update, context, query)
            return
        if data == "upgrade_claw":
            await handle_upgrade_claw(update, context, query)
            return
        
        # ======== هاپوی خیابونی ========
        if data == "street_hapo_rescue":
            await handle_street_hapo_rescue(update, context, query)
            return
        
        # ======== آکادمی ========
        if data == "academy_back_main":
            await show_academy_main(update, query)
            return
        if data == "academy_system_menu":
            await show_academy_system_menu(update, query)
            return
        if data == "academy_features_menu":
            await show_academy_features_menu(update, query)
            return
        if data == "academy_adventure_menu":
            await show_academy_adventure_menu(update, query)
            return
        if data == "academy_games_menu":
            await show_academy_games_menu(update, query)
            return
        if data == "academy_game_xo":
            await show_academy_game_xo(update, query)
            return
        if data.startswith("academy_system_page"):
            page = int(data.replace("academy_system_page", ""))
            await show_academy_system_pages(update, query, page)
            return
        if data.startswith("academy_animals_page"):
            page = int(data.replace("academy_animals_page", ""))
            await show_academy_animals_pages(update, query, page)
            return
        if data.startswith("academy_claw_page"):
            page = int(data.replace("academy_claw_page", ""))
            await show_academy_claw_pages(update, query, page)
            return
        if data == "academy_hapo":
            await show_feature_page(update, query, "hapo")
            return
        if data == "academy_hunt":
            await show_feature_page(update, query, "hunt")
            return
        if data == "academy_bank":
            await show_feature_page(update, query, "bank")
            return
        if data == "academy_transfer":
            await show_feature_page(update, query, "transfer")
            return
        if data == "academy_jail":
            await show_feature_page(update, query, "jail")
            return
        if data == "academy_street_hapo":
            await show_street_hapo_page(update, query)
            return
        if data == "academy_fridge":
            await show_feature_page(update, query, "fridge")
            return
        if data == "academy_smuggle":
            await show_feature_page(update, query, "smuggle")
            return
        if data == "academy_leaderboard":
            await show_feature_page(update, query, "leaderboard")
            return
        if data == "academy_hop":
            await show_adventure_page(update, query, "hop")
            return
        if data == "academy_points":
            await show_adventure_page(update, query, "points")
            return
        if data == "academy_exp":
            await show_adventure_page(update, query, "exp")
            return
        if data == "academy_profile":
            await show_adventure_page(update, query, "profile")
            return
        
        # ======== قوانین ========
        if data == "rules_page_1":
            await show_rules(update, context, 1)
            return
        if data == "rules_page_2":
            await show_rules(update, context, 2)
            return
        
        # ======== لیدربرد ========
        if data == "lb_main":
            await show_leaderboard_main(update, context)
            return
        if data == "lb_hapo":
            await show_leaderboard_hapo(update, context)
            return
        if data == "lb_group":
            await show_leaderboard_group(update, context)
            return
        if data == "lb_back":
            await show_leaderboard_main(update, context)
            return
        if data == "lb_hapo_point":
            await show_leaderboard_result(update, context, "point", group=False, page=0)
            return
        if data == "lb_hapo_hop":
            await show_leaderboard_result(update, context, "hop", group=False, page=0)
            return
        if data == "lb_hapo_street":
            await show_leaderboard_result(update, context, "street", group=False, page=0)
            return
        if data == "lb_hapo_hunt":
            await show_leaderboard_result(update, context, "hunt", group=False, page=0)
            return
        if data == "lb_group_hop":
            await show_leaderboard_result(update, context, "hop", group=True, page=0)
            return
        if data == "lb_group_population":
            await show_leaderboard_result(update, context, "population", group=True, page=0)
            return
        if data == "lb_group_wealth":
            await show_leaderboard_result(update, context, "wealth", group=True, page=0)
            return
        if data == "lb_group_hunt":
            await show_leaderboard_result(update, context, "hunt", group=True, page=0)
            return
        
        # ======== ریست کاربر ========
        if data.startswith("rest_confirm_"):
            target_id = data.replace("rest_confirm_", "")
            await reset_user_confirm(update, context, target_id)
            return
        if data == "rest_cancel_":
            await reset_user_cancel(update, context)
            return
        
        # ======== هاپوی خیابونی ========
        if data == "street_hapo_rescue":
            await handle_street_hapo_rescue(update, context, query)
            return
        
        # ======== انتقال ========
        if data.startswith("transfer_confirm_"):
            await handle_transfer_confirm(update, context)
            return
        if data.startswith("transfer_cancel_"):
            await handle_transfer_cancel(update, context)
            return
        
        # ======== یخچال ========
        if data == "buy_fridge":
            await handle_fridge_buy(update, context, query)
            return
        if data == "upgrade_fridge":
            await handle_fridge_upgrade(update, context, query)
            return
        if data == "fridge_back":
            await handle_fridge_back(update, context, query)
            return
        if data.startswith("fridge_item_"):
            index = int(data.replace("fridge_item_", ""))
            await handle_fridge_item(update, context, query, index)
            return
        if data.startswith("fridge_cook_"):
            index = int(data.replace("fridge_cook_", ""))
            await handle_fridge_cook(update, context, query, index)
            return
        if data.startswith("fridge_sell_"):
            index = int(data.replace("fridge_sell_", ""))
            await handle_fridge_sell(update, context, query, index)
            return
        if data.startswith("fridge_feed_"):
            index = int(data.replace("fridge_feed_", ""))
            await handle_fridge_feed(update, context, query, index)
            return
        if data == "hunt_fridge":
            animal = game.data.get("current_hunt_animal")
            if not animal:
                await query.edit_message_text("❌ *هیچ حیوانی برای ذخیره وجود ندارد*", parse_mode="Markdown")
                return
            animal_name = animal.get("name")
            await handle_hunt_to_fridge(update, context, query, animal_name)
            return
        
        # ======== قاچاق ========
        if data.startswith("smuggle_count_"):
            count = data.replace("smuggle_count_", "")
            await handle_smuggle_start(update, context, query, count)
            return
        if data == "smuggle_back":
            await show_smuggle_menu(update, game)
            return
        
        # ======== هاپو ========
        if data == "confirm_hapo_name":
            new_name = context.user_data.get("new_hapo_name", "")
            if not new_name:
                await query.edit_message_text("❌ *خطا در تغییر اسم*", parse_mode="Markdown")
                return
            
            hop_point = game._to_int(game.data["hop_point"])
            if hop_point < 750:
                await query.answer("❌ پوینت کافی نیست!", show_alert=True)
                return
            
            old_name = game.data["hapo_name"]
            game.data["hapo_name"] = new_name
            game.data["hop_point"] = str(hop_point - 750)
            game.save_data()
            await query.edit_message_text(f"✅ *اسم هاپو از «{old_name}» به «{new_name}» تغییر یافت*", parse_mode="Markdown")
            context.user_data["new_hapo_name"] = None
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        if data == "cancel_hapo_name":
            await query.edit_message_text("❌ *تغییر اسم هاپو لغو شد*", parse_mode="Markdown")
            context.user_data["new_hapo_name"] = None
            return
        
        if data == "buy_hapo":
            result = game.buy_hapo()
            if result["success"]:
                await query.edit_message_text(f"✅ *هاپو خریداری شد!*\nاسم هاپو: {result['name']}", parse_mode="Markdown")
            else:
                await query.answer(f"❌ {result['reason']}", show_alert=True)
            return
        
        if data == "hapo_harvest":
            hapo_harvest = game._to_int(game.data["hapo_harvest"])
            if hapo_harvest > 0:
                hop_point = game._to_int(game.data["hop_point"])
                game.data["hop_point"] = str(hop_point + hapo_harvest)
                game.data["hapo_harvest"] = "0"
                game.save_data()
                await query.edit_message_text(f"✅ *{format_number(hapo_harvest)} هاپو پوینت برداشت شد*", parse_mode="Markdown")
                await asyncio.sleep(2)
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await query.answer("❌ هیچ هاپو پوینتی برای برداشت نیست", show_alert=True)
            return
        
        if data == "hapo_level_up":
            check = game.can_upgrade_level()
            if not check["success"]:
                await query.answer(f"❌ {check['reason']}", show_alert=True)
                return
            
            price = game.get_hapo_upgrade_price()
            hop_point = game._to_int(game.data["hop_point"])
            
            if hop_point < price:
                await query.answer(f"❌ به {format_number(price)} هاپو پوینت نیاز داری", show_alert=True)
                return
            
            result = game.upgrade_hapo_level()
            if result["success"]:
                msg = f"✅ *سطح هاپو به {result['new_level']} ارتقا یافت*"
                await query.edit_message_text(msg, parse_mode="Markdown")
                await asyncio.sleep(2)
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await query.answer(f"❌ {result['reason']}", show_alert=True)
            return
        
        if data == "hapo_rank_up_confirm":
            check = game.can_rank_up()
            if not check["success"]:
                await query.answer(f"❌ {check['reason']}", show_alert=True)
                return
            
            price = game.get_hapo_rank_up_price()
            hop_point = game._to_int(game.data["hop_point"])
            
            if hop_point < price:
                await query.answer(f"❌ به {format_number(price)} هاپو پوینت نیاز داری", show_alert=True)
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
            
            await query.edit_message_text(msg, reply_markup=get_confirm_keyboard("hapo_rank_up_yes", "hapo_rank_up_no"), parse_mode="Markdown")
            return
        
        if data == "hapo_rank_up_yes":
            result = game.confirm_rank_up()
            if result["success"]:
                await query.edit_message_text(
                    f"✅ *مقام هاپو به {result['new_rank_name']} ارتقا یافت!*",
                    parse_mode="Markdown"
                )
                await asyncio.sleep(2)
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await query.answer(f"❌ {result['reason']}", show_alert=True)
            return
        
        if data == "hapo_rank_up_no":
            await query.edit_message_text("❌ *ارتقا مقام لغو شد*", parse_mode="Markdown")
            return
        
        if data == "hapo_rename":
            hop_point = game._to_int(game.data["hop_point"])
            if hop_point < 750:
                await query.answer("❌ به 750 هاپو پوینت نیاز داری", show_alert=True)
                return
            await query.edit_message_text("✏️ *اسم جدید هاپو رو وارد کن:*", parse_mode="Markdown")
            context.user_data["waiting_for_hapo_name"] = True
            return
        
        if data == "hapo_max":
            await query.edit_message_text("🏆 *هاپو در بالاترین سطح است*", parse_mode="Markdown")
            return
        
        # ======== شکار ========
        if data == "hunt_sell":
            await handle_hunt_sell(update, context, query, game)
            return
        
        if data == "hunt_feed":
            await handle_hunt_feed(update, context, query, game)
            return
        
        # ======== پروفایل ========
        if data == "profile_hide":
            game.data["profile_hidden"] = True
            game.save_data()
            await query.edit_message_text("✅ *پروفایل شما مخفی شد*", parse_mode="Markdown")
            await my_profile_from_callback(query, game)
            return
        if data == "profile_show":
            game.data["profile_hidden"] = False
            game.save_data()
            await query.edit_message_text("✅ *پروفایل شما نمایش داده شد*", parse_mode="Markdown")
            await my_profile_from_callback(query, game)
            return
        if data == "profile_lock":
            game.data["profile_locked"] = True
            game.save_data()
            await query.edit_message_text("✅ *پروفایل شما قفل شد*", parse_mode="Markdown")
            await my_profile_from_callback(query, game)
            return
        if data == "profile_unlock":
            game.data["profile_locked"] = False
            game.save_data()
            await query.edit_message_text("✅ *پروفایل شما باز شد*", parse_mode="Markdown")
            await my_profile_from_callback(query, game)
            return
        
        # ======== بانک ========
        if data == "buy_bank":
            result = game.open_bank()
            if result["success"]:
                await query.edit_message_text(f"🏦 *بانک هاپویی خریداری شد!*\n💳 *شماره کارت شما:* {result['card_number']}", parse_mode="Markdown")
                await asyncio.sleep(2)
                msg = get_bank_menu_text(game, False)
                keyboard = get_bank_keyboard(False)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await query.answer(f"❌ {result['reason']}", show_alert=True)
            return
        if data == "bank_deposit":
            await query.edit_message_text("💰 *مبلغ واریزی رو بنویس:*", parse_mode="Markdown")
            context.user_data["waiting_for_deposit"] = True
            return
        if data == "bank_withdraw":
            await query.edit_message_text("💰 *مبلغ برداشت رو بنویس:*", parse_mode="Markdown")
            context.user_data["waiting_for_withdraw"] = True
            return
        if data == "bank_card_to_card":
            await query.edit_message_text(get_card_to_card_text())
            context.user_data["waiting_for_card_to_card"] = True
            return
        if data == "bank_transactions":
            msg = get_bank_menu_text(game, True)
            keyboard = get_bank_keyboard(True)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        if data == "bank_change_card":
            if not game.data["bank_opened"]:
                await query.answer("❌ شما بانک ندارید", show_alert=True)
                return
            msg = get_change_card_confirm_text(game)
            await query.edit_message_text(msg, reply_markup=get_confirm_keyboard("bank_change_card_yes", "bank_change_card_no"), parse_mode="Markdown")
            return
        if data == "bank_change_card_yes":
            result = game.change_card_number()
            if result["success"]:
                await query.edit_message_text(f"✅ *شماره حساب شما تغییر کرد!*\n🔄 *شماره جدید:* {result['new_card']}", parse_mode="Markdown")
                await asyncio.sleep(2)
                msg = get_bank_menu_text(game, False)
                keyboard = get_bank_keyboard(False)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await query.answer(f"❌ {result['reason']}", show_alert=True)
            return
        if data == "bank_change_card_no":
            await query.edit_message_text("❌ *تغییر شماره حساب لغو شد*", parse_mode="Markdown")
            await asyncio.sleep(1)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        # ======== میو و زندان ========
        if data.startswith("meow_vote_"):
            vote_key = data.replace("meow_vote_", "")
            if vote_key not in MEOW_VOTES:
                await query.answer("❌ رای‌گیری به پایان رسیده است", show_alert=True)
                return
            vote_data = MEOW_VOTES[vote_key]
            voter_id = user_id
            if voter_id == vote_data["target_id"]:
                await query.answer("❌ نمی‌تونی به خودت رای بدی!", show_alert=True)
                return
            if voter_id in vote_data["votes"]:
                await query.answer("❌ تو قبلاً رای دادی!", show_alert=True)
                return
            vote_data["votes"].append(voter_id)
            votes_count = len(vote_data["votes"])
            keyboard = [[InlineKeyboardButton("🗳️ رای به زندان", callback_data=f"meow_vote_{vote_key}")]]
            await query.edit_message_text(f"😱 *یک گربه ی بی ادب!*\nرای بدید که بفرستیمش زندان\n{votes_count}/{JAIL_VOTE_NEEDED}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            await query.answer("✅ رای شما ثبت شد!")
            if votes_count >= JAIL_VOTE_NEEDED:
                target_id = vote_data["target_id"]
                target_game = get_game(target_id)
                target_game.jail_user(JAIL_REASON_MEOW, JAIL_DURATION_MEOW, JAIL_FINE_MEOW)
                await query.edit_message_text(f"😡 *گربه ی بی ادب!*\n\n✅ *با {votes_count} رای، کاربر به زندان فرستاده شد!*", parse_mode="Markdown")
                del MEOW_VOTES[vote_key]
            return
        
        if data == "jail_pay_fine":
            if not game.is_jailed():
                await query.answer("❌ شما در زندان نیستید", show_alert=True)
                return
            fine = game._to_int(game.data.get("jail_fine", 0))
            await query.edit_message_text(f"⚠️ *آیا از پرداخت جریمه {format_number(fine)} 🪙 مطمئنی؟*", reply_markup=get_confirm_keyboard("jail_pay_fine_yes", "jail_pay_fine_no"), parse_mode="Markdown")
            return
        if data == "jail_pay_fine_yes":
            result = game.pay_jail_fine()
            if result["success"]:
                await query.edit_message_text("✅ *جریمه پرداخت شد و شما آزاد شدید!* 🎉", parse_mode="Markdown")
            else:
                await query.answer(f"❌ {result['reason']}", show_alert=True)
            return
        if data == "jail_pay_fine_no":
            await query.edit_message_text("❌ *پرداخت جریمه لغو شد*", parse_mode="Markdown")
            return
        
    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")
        logger.error(traceback.format_exc())
        try:
            await query.answer("❌ خطایی رخ داد!", show_alert=True)
        except:
            pass


# ================================================================
# توابع کمکی یخچال (برای handle_callback)
# ================================================================

async def handle_fridge_buy(update, context, query):
    user_id = query.from_user.id
    game = get_game(user_id)
    result = game.buy_fridge()
    if result["success"]:
        await query.edit_message_text("✅ *یخچال هاپویی خریداری شد!*", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_fridge_upgrade(update, context, query):
    user_id = query.from_user.id
    game = get_game(user_id)
    result = game.upgrade_fridge()
    if result["success"]:
        await query.edit_message_text(f"✅ *یخچال به سطح {result['new_level']} ارتقا یافت!*", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_fridge_back(update, context, query):
    user_id = query.from_user.id
    game = get_game(user_id)
    await show_fridge_menu(update, game)


async def handle_fridge_item(update, context, query, index):
    user_id = query.from_user.id
    game = get_game(user_id)
    
    items = game.get_fridge_items()
    if index < 0 or index >= len(items):
        await query.edit_message_text("❌ *حیوان مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    item = items[index]
    
    msg = f"❄️ *یخچال هاپویی*\n\n"
    msg += f"{item.get('emoji', '🐟')} *{item.get('name', 'ناشناس')}*\n"
    msg += f"⭐️ *سطح :* {item.get('rarity_name', 'معمولی')}\n"
    msg += f"⚖️ *وزن :* {item.get('weight', 0)} کیلو\n"
    msg += f"💰 *ارزش :* {format_number(item.get('value', 0))} 🪙\n"
    msg += f"🍖 *ارزش غذایی :* {item.get('nutrition', 1)}\n\n"
    msg += "❗️ *میخوای چیکارش کنی ؟*"
    
    keyboard = [
        [InlineKeyboardButton(f"💰 فروش ({format_number(item.get('value', 0))})", callback_data=f"fridge_sell_{index}")]
    ]
    if game.data.get("hapo_owned", False):
        keyboard.append([InlineKeyboardButton(f"🍖 به هاپو بده", callback_data=f"fridge_feed_{index}")])
    keyboard.append([InlineKeyboardButton("◀️ برگشت", callback_data="fridge_back")])
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_fridge_cook(update, context, query, index):
    user_id = query.from_user.id
    game = get_game(user_id)
    result = game.cook_item(index)
    if result["success"]:
        await query.edit_message_text(f"🔥 *شروع پخت!*\n⏳ *زمان پخت: {result['cook_time']} ثانیه*", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_fridge_sell(update, context, query, index):
    user_id = query.from_user.id
    game = get_game(user_id)
    result = game.sell_from_fridge(index)
    if result["success"]:
        await query.edit_message_text(f"💰 *{result['item']['emoji']} {result['item']['name']} فروخته شد!*\n✅ *{format_number(result['value'])} 🪙 واریز شد*", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_fridge_feed(update, context, query, index):
    user_id = query.from_user.id
    game = get_game(user_id)
    result = game.feed_hapo_from_fridge(index)
    if result["success"]:
        await query.edit_message_text(f"🍖 *{result['item']['emoji']} {result['item']['name']} به هاپو داده شد!*\n✅ *{result['fed']} کالری اضافه شد*", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_hunt_to_fridge(update, context, query, animal_name):
    user_id = query.from_user.id
    game = get_game(user_id)
    
    animal = game.data.get("current_hunt_animal")
    if not animal:
        await query.edit_message_text("❌ *هیچ حیوانی برای ذخیره وجود ندارد*", parse_mode="Markdown")
        return
    
    if animal.get("name") != animal_name:
        await query.edit_message_text("❌ *خطا در شناسایی حیوان*", parse_mode="Markdown")
        return
    
    hunt_time = game._to_float(game.data.get("hunt_time", 0))
    if hunt_time > 0:
        now = datetime.now().timestamp()
        if (now - hunt_time) > HUNT_DECISION_TIMER:
            game.data["current_hunt_animal"] = None
            game.data["hunt_time"] = "0"
            game.save_data()
            await query.edit_message_text("🦌 *حیوان فرار کرد!*", parse_mode="Markdown")
            return
    
    if not game.data.get("fridge_owned", False):
        await query.edit_message_text("❌ *شما یخچال هاپویی ندارید!*", parse_mode="Markdown")
        return
    
    result = game.add_to_fridge(animal)
    if result["success"]:
        game.data["current_hunt_animal"] = None
        game.data["hunt_time"] = "0"
        game.save_data()
        await query.edit_message_text(
            f"❄️ *{animal['emoji']} {animal['name']} در یخچال ذخیره شد!*",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_smuggle_start(update, context, query, count):
    user_id = query.from_user.id
    game = get_game(user_id)
    count = int(count)
    
    result = game.start_smuggle(count)
    if result["success"]:
        duration = result.get("duration", 0)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        
        time_text = f"{hours} ساعت و {minutes} دقیقه" if hours > 0 else f"{minutes} دقیقه"
        
        await query.edit_message_text(
            f"🥷 *قاچاق شروع شد!*\n\n"
            f"📦 *تعداد هاپوها:* {count}\n"
            f"⏳ *زمان تقریبی:* {time_text}\n"
            f"🍀 *شانس موفقیت:* {result.get('success_chance', 0)}%\n\n"
            f"💡 *وقتی قاچاق تموم شد بهت پیام میدم!*",
            parse_mode="Markdown"
        )
        
        asyncio.create_task(smuggle_timer(update, context, user_id))
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def smuggle_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    try:
        game = get_game(user_id)
        
        while True:
            status = game.check_smuggle_status()
            if status is None:
                return
            if status.get("status") != "in_progress":
                break
            await asyncio.sleep(60)
        
        if status.get("status") == "success":
            try:
                await context.bot.send_message(
                    user_id,
                    f"✅ *قاچاق با موفقیت انجام شد!*\n💰 *پاداش:* {format_number(status.get('reward', 0))} 🪙",
                    parse_mode="Markdown"
                )
            except:
                pass
        elif status.get("status") == "failed":
            try:
                await context.bot.send_message(
                    user_id,
                    f"🚨 *قاچاق ناموفق!*\n⛓️ *شما زندانی شدید!*",
                    parse_mode="Markdown"
                )
            except:
                pass
    except Exception as e:
        logger.error(f"Error in smuggle_timer: {e}")


async def handle_hunt_sell(update, context, query, game):
    hunt_time = game._to_float(game.data.get("hunt_time", 0))
    if hunt_time > 0:
        now = datetime.now().timestamp()
        if (now - hunt_time) > HUNT_DECISION_TIMER:
            game.data["current_hunt_animal"] = None
            game.data["hunt_time"] = "0"
            game.save_data()
            await query.edit_message_text("🦌 *حیوان فرار کرد!*", parse_mode="Markdown")
            return
    
    result = game.sell_animal()
    if result["success"]:
        await query.message.reply_text(f"💰 *حیوان فروخته شد!*\n✅ *{format_number(result['value'])} 🪙 دریافت کردی*", parse_mode="Markdown")
    else:
        await query.answer(f"❌ {result['reason']}", show_alert=True)


async def handle_hunt_feed(update, context, query, game):
    hunt_time = game._to_float(game.data.get("hunt_time", 0))
    if hunt_time > 0:
        now = datetime.now().timestamp()
        if (now - hunt_time) > HUNT_DECISION_TIMER:
            game.data["current_hunt_animal"] = None
            game.data["hunt_time"] = "0"
            game.save_data()
            await query.edit_message_text("🦌 *حیوان فرار کرد!*", parse_mode="Markdown")
            return
    
    result = game.feed_hapo()
    if result["success"]:
        await query.message.reply_text(f"🍖 *{result['fed']} غذا به هاپو داده شد*\n✅ *هاپو سیر شد!*", parse_mode="Markdown")
        return
    
    error_msg = result["reason"]
    animal = game.data.get("current_hunt_animal")
    if error_msg == "هاپو سیر است" and animal:
        if game._to_float(game.data.get("hunt_time", 0)) > 0:
            now = datetime.now().timestamp()
            hunt_time = game._to_float(game.data["hunt_time"])
            if (now - hunt_time) > HUNT_DECISION_TIMER:
                game.data["current_hunt_animal"] = None
                game.data["hunt_time"] = "0"
                game.save_data()
                await query.message.reply_text("🦌 *حیوان فرار کرد!*", parse_mode="Markdown")
                return
        
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
            keyboard.append([InlineKeyboardButton("❄️ بندازش تو یخچال", callback_data="hunt_fridge")])
        
        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    await query.answer(f"❌ {error_msg}", show_alert=True)


async def my_profile_from_callback(query, game):
    user_id = int(game.user_id)
    full_name = game.data["player_name"]
    
    required = game.get_required_for_level(game._to_int(game.data["level"]))
    is_hidden = game.data.get("profile_hidden", False)
    is_locked = game.data.get("profile_locked", False)
    
    street_rescued = game._to_int(game.data.get("street_hapo_rescued", 0))
    hapo_rank = game._to_int(game.data.get("hapo_rank", 0))
    hapo_level = game._to_int(game.data.get("hapo_level", 1))
    hop_point = game._to_int(game.data["hop_point"])
    hop_count = game._to_int(game.data["hop_count"])
    level = game._to_int(game.data["level"])
    
    point_rank = await get_user_rank(user_id, "point")
    hop_rank = await get_user_rank(user_id, "hop")
    street_rank = await get_user_rank(user_id, "street")
    hunt_rank = await get_user_rank(user_id, "hunt")
    
    total_hunts = game._to_int(game.data.get("total_hunts", 0))
    
    msg = f"╮──「 🐶 *پروفایل هاپویی* 🐶 」\n\n"
    msg += f"┐─ 👤 *کاربر :* {full_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 *آیدی :* `{user_id}`\n\n"
    else:
        msg += f"‏┘─ 🪪 *آیدی :* 🔒 مخفی\n\n"
    
    msg += f"┐─ 💰 *هاپ پوینت ها :* {format_number(hop_point)} 🪙"
    if point_rank:
        msg += f" *(رتبه: {point_rank})*"
    msg += "\n"
    
    msg += f"┐─ 🐾 *هاپ هاپ ها :* {hop_count}"
    if hop_rank:
        msg += f" *(رتبه: {hop_rank})*"
    msg += "\n"
    
    if street_rescued > 0:
        msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* {street_rescued}"
        if street_rank:
            msg += f" *(رتبه: {street_rank})*"
        msg += "\n"
    else:
        msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* 0\n"
    
    msg += f"┐─ 🏹 *تعداد شکار:* {total_hunts}"
    if hunt_rank:
        msg += f" *(رتبه: {hunt_rank})*"
    msg += "\n"
    
    if game.data.get("hapo_owned", False):
        msg += f"┐─ 🐕 *هاپو:* {game.data['hapo_name']}\n"
        msg += f"┘─ 🌟 *مقام:* {RANK_NAMES[hapo_rank]} | ⭐ *سطح:* {hapo_level}/5\n\n"
    else:
        msg += "\n"
    
    if level < 20:
        msg += f"╯─ ⭐️ *سطح :* {level} | {hop_count} / {required}"
    else:
        msg += f"╯─ ⭐️ *سطح :* {level} 🏆 نهایی"
    
    keyboard = []
    if is_hidden:
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide")])
    
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock")])
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
