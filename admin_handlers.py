# admin_handlers.py - هندلرهای ادمین هاپویی

import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    MAX_LEVEL, RANK_NAMES, FRIDGE_CAPACITY, LEADERBOARD_MAX_USERS,
    LEADERBOARD_MAX_GROUPS, STREET_HAPO_DECISION_TIME, STREET_HAPO_COSTS,
    STREET_HAPO_SUCCESS_CHANCE, STREET_HAPO_IMAGE_URL, JAIL_VOTE_NEEDED
)
from globals import get_game, refresh_user_cache, clear_user_game, get_street_hapo
from database import get_all_groups, get_user_by_identifier, supabase
from utils import format_number, parse_amount, get_confirm_keyboard
from logger_config import log_security, log_transaction, log_error
from base_handlers import get_user_display_name, get_user_link

logger = logging.getLogger(__name__)


# ================================================================
# متن‌های لیدربرد
# ================================================================

LEADERBOARD_MAIN = """🏆 *لیدربرد هاپویی* 🐶

❗️ لطفا لیدربرد را انتخاب کنید ⬇️

🏆 برترین هاپو ها
🏰 برترین گروه ها"""

LEADERBOARD_HAPO = """🏆 *لیدربرد برترین هاپو ها* 🐶

❗️ لطفا نوع لیدربرد را انتخاب کنید ⬇️

🪙 لیدربرد هاپو پوینت : ثروتمند ترین هاپو های هاپویی با بیشترین هاپ پوینت
🐾 لیدربرد هاپ هاپ : پر سر و صدا ترین هاپو های هاپویی با بیشترین هاپ هاپ
🐶 لیدربرد هاپو های خیابونی : مهربون ترین هاپو ها با بیشترین هاپوی خیابونی
🏹 لیدربرد شکار : بهترین شکارچی های هاپویی با بیشترین شکار"""

LEADERBOARD_GROUP = """🏆 *لیدربرد گروهی هاپویی* 🐶

❗️ لطفا نوع لیدربرد را انتخاب کنید ⬇️

🐾 لیدربرد هاپ هاپ : پر سر و صدا ترین گروه های هاپویی با بیشترین هاپ هاپ
👥 لیدربرد جمعیت : پر جمعیت ترین گروه های هاپویی با بیشترین هاپو
🏦 لیدربرد خزانه : ثروتمند ترین گروه های هاپویی با بیشترین جمع داراییه اعضا
🏹 لیدربرد بازار شکار : بهترین بازار حیوان با بیشترین تعداد شکار"""


# ================================================================
# توابع کمکی لیدربرد
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


# ================================================================
# نمایش لیدربرد
# ================================================================

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


# ================================================================
# دستورات ادمین
# ================================================================

async def set_user_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم سطح کاربر - با به‌روزرسانی کش"""
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ *فرمت:* `setlevel [آیدی/یوزرنیم] [عدد]`\n*مثال:* `setlevel @username 5`",
            parse_mode="Markdown"
        )
        return
    
    try:
        new_level = int(parts[2])
        if not 1 <= new_level <= MAX_LEVEL:
            await update.message.reply_text(
                f"❌ *سطح باید بین 1 تا {MAX_LEVEL} باشد*",
                parse_mode="Markdown"
            )
            return
    except:
        await update.message.reply_text("❌ *لطفاً یک عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(
            f"❌ *کاربری با شناسه `{parts[1]}` در دیتابیس ثبت نشده است.*",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = int(user_data['user_id'])
    target_game = get_game(target_user_id)
    old_level = target_game._to_int(target_game.data["level"])
    target_game.data["level"] = str(new_level)
    target_game.data["hop_count"] = "0"
    target_game.save_data()
    
    # ✅ به‌روزرسانی کش
    refresh_user_cache(target_user_id)
    
    log_security(user_id, "تغییر سطح", f"کاربر {target_user_id}: {old_level} → {new_level}")
    
    await update.message.reply_text(
        f"✅ *سطح کاربر `{user_data['player_name']}` از {old_level} به {new_level} تغییر یافت.*",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            target_user_id,
            f"⭐ *سطح هاپویی شما به {new_level} تغییر یافت!*",
            parse_mode="Markdown"
        )
    except:
        pass


async def add_user_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن سطح به کاربر"""
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ *فرمت:* `addlevel [آیدی/یوزرنیم] [عدد]`\n*مثال:* `addlevel @username 5`",
            parse_mode="Markdown"
        )
        return
    
    try:
        add_amount = int(parts[2])
        if add_amount <= 0:
            await update.message.reply_text("❌ *مقدار باید مثبت باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *لطفاً یک عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(
            f"❌ *کاربری با شناسه `{parts[1]}` در دیتابیس ثبت نشده است.*",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = int(user_data['user_id'])
    target_game = get_game(target_user_id)
    old_level = target_game._to_int(target_game.data["level"])
    new_level = min(old_level + add_amount, MAX_LEVEL)
    target_game.data["level"] = str(new_level)
    target_game.data["hop_count"] = "0"
    target_game.save_data()
    
    refresh_user_cache(target_user_id)
    
    log_security(user_id, "افزایش سطح", f"کاربر {target_user_id}: +{add_amount} → {new_level}")
    
    await update.message.reply_text(
        f"✅ *{add_amount} سطح به کاربر `{user_data['player_name']}` اضافه شد.*\n*سطح جدید:* {new_level}",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            target_user_id,
            f"⭐ *{add_amount} سطح به هاپوهای شما اضافه شد!*\n*سطح جدید:* {new_level}",
            parse_mode="Markdown"
        )
    except:
        pass


async def set_user_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم پوینت کاربر"""
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ *فرمت:* `setpoint [آیدی/یوزرنیم] [عدد]`\n*مثال:* `setpoint @username 1000`\n*مثال:* `setpoint @username 1k`",
            parse_mode="Markdown"
        )
        return
    
    new_point = parse_amount(parts[2])
    if new_point is None:
        await update.message.reply_text(
            "❌ *عدد معتبر وارد کن.*\n\n💡 *مثال:* `1000` یا `1k` یا `1m`",
            parse_mode="Markdown"
        )
        return
    if new_point < 0:
        await update.message.reply_text("❌ *پوینت نمی‌تواند منفی باشد*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(
            f"❌ *کاربری با شناسه `{parts[1]}` در دیتابیس ثبت نشده است.*",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = int(user_data['user_id'])
    target_game = get_game(target_user_id)
    old_point = target_game._to_int(target_game.data["hop_point"])
    target_game.data["hop_point"] = str(new_point)
    target_game.save_data()
    
    refresh_user_cache(target_user_id)
    
    log_security(user_id, "تنظیم پوینت", f"کاربر {target_user_id}: {old_point} → {new_point}")
    
    await update.message.reply_text(
        f"✅ *پوینت کاربر `{user_data['player_name']}` از {format_number(old_point)} به {format_number(new_point)} تغییر یافت.*",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            target_user_id,
            f"💰 *هاپو پوینت‌های شما به {format_number(new_point)} تغییر یافت!*",
            parse_mode="Markdown"
        )
    except:
        pass


async def add_user_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن پوینت به کاربر"""
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ *فرمت:* `addpoint [آیدی/یوزرنیم] [عدد]`\n*مثال:* `addpoint @username 1000`\n*مثال:* `addpoint @username 1k`",
            parse_mode="Markdown"
        )
        return
    
    add_amount = parse_amount(parts[2])
    if add_amount is None:
        await update.message.reply_text(
            "❌ *عدد معتبر وارد کن.*\n\n💡 *مثال:* `1000` یا `1k` یا `1m`",
            parse_mode="Markdown"
        )
        return
    if add_amount <= 0:
        await update.message.reply_text("❌ *مقدار باید مثبت باشد*", parse_mode="Markdown")
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(
            f"❌ *کاربری با شناسه `{parts[1]}` در دیتابیس ثبت نشده است.*",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = int(user_data['user_id'])
    target_game = get_game(target_user_id)
    old_point = target_game._to_int(target_game.data["hop_point"])
    new_point = old_point + add_amount
    target_game.data["hop_point"] = str(new_point)
    target_game.save_data()
    
    refresh_user_cache(target_user_id)
    
    log_security(user_id, "افزایش پوینت", f"کاربر {target_user_id}: +{add_amount} → {new_point}")
    
    await update.message.reply_text(
        f"✅ *{format_number(add_amount)} هاپو پوینت به کاربر `{user_data['player_name']}` اضافه شد.*\n*پوینت جدید:* {format_number(new_point)}",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            target_user_id,
            f"💰 *{format_number(add_amount)} هاپو پوینت به حساب شما اضافه شد!*\n*موجودی جدید:* {format_number(new_point)}",
            parse_mode="Markdown"
        )
    except:
        pass


async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت اطلاعات کاربر"""
    if update.message.chat.type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text(
            "❌ *شما دسترسی به این دستور ندارید. فقط ادمین‌ها میتونن استفاده کنن.*",
            parse_mode="Markdown"
        )
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ *لطفاً شناسه کاربر را وارد کن.*\n\n📌 *مثال:*\n🔹 با آیدی عددی: `userinfo 123456789`\n🔹 با یوزرنیم: `userinfo @username`",
            parse_mode="Markdown"
        )
        return
    
    user_data = get_user_by_identifier(parts[1])
    if not user_data:
        await update.message.reply_text(
            f"❌ *کاربری با شناسه `{parts[1]}` در دیتابیس ثبت نشده است.*",
            parse_mode="Markdown"
        )
        return
    
    hop_point = int(float(user_data.get("hop_point", 0)))
    hop_count = int(float(user_data.get("hop_count", 0)))
    level = int(float(user_data.get("level", 1)))
    hapo_rank = int(float(user_data.get("hapo_rank", 0)))
    hapo_level = int(float(user_data.get("hapo_level", 1)))
    bank_balance = int(float(user_data.get("bank_balance", 0)))
    street_rescued = int(float(user_data.get("street_hapo_rescued", 0)))
    fridge_owned = user_data.get("fridge_owned", False)
    fridge_level = int(float(user_data.get("fridge_level", 1)))
    
    msg = f"📊 *اطلاعات کاربر:*\n\n"
    msg += f"🆔 *آیدی:* `{user_data['user_id']}`\n"
    msg += f"👤 *نام:* {user_data['player_name']}\n"
    msg += f"⭐ *سطح:* {level}\n"
    msg += f"💰 *هاپو پوینت:* {format_number(hop_point)}\n"
    msg += f"🐾 *تعداد هاپ:* {hop_count}\n"
    
    if user_data.get('hapo_owned', False):
        msg += f"\n🐕 *هاپو:*\n"
        msg += f"  📛 *نام:* {user_data['hapo_name']}\n"
        msg += f"  ⭐ *سطح:* {hapo_level}/5\n"
        msg += f"  🌟 *مقام:* {RANK_NAMES[hapo_rank]}"
    
    if user_data.get('bank_opened', False):
        msg += f"\n\n🏦 *بانک:*\n"
        msg += f"  💰 *موجودی:* {format_number(bank_balance)}\n"
        msg += f"  💳 *شماره کارت:* {user_data.get('bank_card_number', 'نامشخص')}"
    
    if fridge_owned:
        msg += f"\n\n❄️ *یخچال:*\n"
        msg += f"  ⭐ *سطح:* {fridge_level}\n"
        msg += f"  📦 *ظرفیت:* {FRIDGE_CAPACITY.get(fridge_level, 1)}"
    
    msg += f"\n\n🐶 *هاپوی خیابونی نجات داده:* {street_rescued}"
    msg += f"\n\n📅 *آخرین بروزرسانی:* {user_data.get('last_updated', 'نامشخص')}"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def jail_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """زندانی کردن کاربر توسط ادمین"""
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما ادمین نیستید*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) < 4:
        await update.message.reply_text(
            "❌ *فرمت:* `jail [آیدی/یوزرنیم] [مدت (دقیقه)] [دلیل]`\n*مثال:* `jail @username 5 Spam`",
            parse_mode="Markdown"
        )
        return
    
    identifier = parts[1]
    try:
        duration_minutes = int(parts[2])
        if duration_minutes <= 0:
            await update.message.reply_text("❌ *مدت زمان باید مثبت باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *مدت زمان باید یک عدد باشد (دقیقه)*", parse_mode="Markdown")
        return
    
    reason = " ".join(parts[3:]) if len(parts) > 3 else "توسط ادمین"
    
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(
            f"❌ *کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.*",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    fine = duration_minutes * 250
    
    target_game.jail_user_with_admin(reason, duration_minutes * 60, fine, user_id)
    admin_name = full_name or username or f"کاربر{user_id}"
    
    refresh_user_cache(int(target_user_id))
    
    log_security(user_id, "زندانی کردن", f"کاربر {target_user_id}: {duration_minutes} دقیقه - {reason}")
    
    await update.message.reply_text(
        f"✅ *کاربر `{user_data['player_name']}` به مدت {duration_minutes} دقیقه زندانی شد.*\n"
        f"📝 *دلیل:* {reason}\n🏦 *جریمه:* {format_number(fine)} 🪙",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"🚨 *شما توسط ادمین به زندان فرستاده شدید!*\n"
            f"📝 *دلیل:* {reason}\n"
            f"⏳ *مدت:* {duration_minutes} دقیقه\n"
            f"🏦 *جریمه:* {format_number(fine)} 🪙\n"
            f"👮 *زندانی شده توسط:* {admin_name}\n\n"
            f"💡 *برای اطلاع از وضعیت زندان، «زندان هاپویی» را بزنید.*",
            parse_mode="Markdown"
        )
    except:
        pass


async def reset_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ریست کردن کاربر"""
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *این دستور فقط در پیوی بات قابل استفاده است!*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین میتونه از این دستور استفاده کنه!*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ *فرمت:* `/rest [user_id یا @username]`\n*مثال:* `/rest 123456789`",
            parse_mode="Markdown"
        )
        return
    
    identifier = parts[1]
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(
            f"❌ *کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.*",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = user_data['user_id']
    target_name = user_data.get('player_name', f"کاربر{target_user_id}")
    
    keyboard = get_confirm_keyboard(f"rest_confirm_{target_user_id}", "rest_cancel")
    await update.message.reply_text(
        f"⚠️ *آیا از ریست کردن کاربر `{target_name}` مطمئنی؟*\n\n"
        f"🆔 *آیدی:* `{target_user_id}`\n\n"
        f"❗️ *این کار **همه** اطلاعات کاربر رو به حالت اولیه برمیگردونه.*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def reset_user_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id):
    """تایید ریست کاربر"""
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.callback_query.answer("❌ فقط ادمین!")
        return
    
    try:
        target_game = get_game(int(target_user_id))
        player_name = target_game.data.get("player_name", f"کاربر{target_user_id}")
        
        log_security(user_id, "ریست کاربر", f"کاربر {target_user_id}")
        log_transaction(user_id, "ریست کاربر", 0, f"کاربر {target_user_id}")
        
        target_game.reset_data()
        clear_user_game(int(target_user_id))
        
        await update.callback_query.edit_message_text(
            f"✅ *کاربر `{player_name}` با موفقیت ریست شد!*\n\n"
            f"🆔 *آیدی:* `{target_user_id}`\n"
            f"👤 *نام:* {target_game.data['player_name']}\n\n"
            f"📊 *همه اطلاعات به حالت اولیه برگشت.*",
            parse_mode="Markdown"
        )
        
        try:
            await context.bot.send_message(
                int(target_user_id),
                f"🔒 *حساب هاپویی شما توسط ادمین ریست شد!*\n\n"
                f"📊 *همه اطلاعات شما به حالت اولیه برگشت.*\n"
                f"💰 *هاپو پوینت:* 0\n"
                f"⭐ *سطح:* 1\n\n"
                f"💡 *دوباره از ابتدا شروع کن!* 🐶",
                parse_mode="Markdown"
            )
        except:
            pass
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ *خطا در ریست کاربر:* {e}", parse_mode="Markdown")


async def reset_user_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو ریست کاربر"""
    await update.callback_query.edit_message_text("❌ *عملیات ریست لغو شد.*", parse_mode="Markdown")


async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لیست گروه‌های ثبت شده"""
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *این دستور فقط در پیوی بات قابل استفاده است!*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین میتونه از این دستور استفاده کنه!*", parse_mode="Markdown")
        return
    
    chat_ids = get_all_groups()
    if not chat_ids:
        await update.message.reply_text("❌ *هیچ گروهی در دیتابیس ثبت نشده!*", parse_mode="Markdown")
        return
    
    msg = "📋 *لیست گروه‌های ثبت شده:*\n\n"
    for chat_id in chat_ids:
        msg += f"`{chat_id}`\n"
    msg += f"\n✅ *تعداد:* {len(chat_ids)} گروه"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


# ================================================================
# هاپوی خیابونی (ادمین)
# ================================================================

async def admin_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال هاپوی خیابونی توسط ادمین"""
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *این دستور فقط در پیوی بات قابل استفاده است!*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین میتونه از این دستور استفاده کنه!*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ *فرمت:* `/hapo [chat_id]`\n*مثال:* `/hapo -1003708381360`",
            parse_mode="Markdown"
        )
        return
    
    try:
        chat_id = int(parts[1])
    except:
        await update.message.reply_text("❌ *chat_id باید عددی باشد!*", parse_mode="Markdown")
        return
    
    street_hapo = get_street_hapo()
    if street_hapo.active:
        if street_hapo.is_expired():
            street_hapo.active = False
            street_hapo.save_status()
        else:
            await update.message.reply_text("⏳ *هم اکنون یک هاپوی خیابونی در حال نجات است!*", parse_mode="Markdown")
            return
    
    success, msg = street_hapo.start_event(chat_id)
    if not success:
        await update.message.reply_text(f"❌ *{msg}*", parse_mode="Markdown")
        return
    
    keyboard = [[InlineKeyboardButton("🐶 نجات هاپوی خیابونی", callback_data="street_hapo_rescue")]]
    try:
        message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=STREET_HAPO_IMAGE_URL,
            caption=f"🐶 *یک هاپوی خیابونی پیدا شده!*\n\n⏳ *زمان برای نجات:* {STREET_HAPO_DECISION_TIME} ثانیه\n💰 *هزینه تلاش اول:* {STREET_HAPO_COSTS[0]} 🪙\n🍀 *شانس موفقیت:* {int(STREET_HAPO_SUCCESS_CHANCE * 100)}%\n\nبرای نجاتش کلیک کن 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        street_hapo.data["message_id"] = message.message_id
        street_hapo.save_status()
        
        log_security(user_id, "ارسال هاپوی خیابونی", f"به گروه {chat_id}")
        
        await update.message.reply_text(f"✅ *هاپوی خیابونی به گروه با chat_id `{parts[1]}` ارسال شد!*", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending admin street hapo: {e}")
        street_hapo.active = False
        street_hapo.save_status()
        await update.message.reply_text(f"❌ *خطا در ارسال:* {e}", parse_mode="Markdown")


async def admin_set_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم تعداد هاپوی خیابونی کاربر"""
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *این دستور فقط در پیوی بات قابل استفاده است!*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین میتونه از این دستور استفاده کنه!*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ *فرمت:* `/setstreethapo [user_id] [تعداد]`\n*مثال:* `/setstreethapo 123456789 5`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(parts[1])
        count = int(parts[2])
        if count < 0:
            await update.message.reply_text("❌ *تعداد نمی‌تواند منفی باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *لطفاً یک عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    target_game = get_game(target_user_id)
    old_count = target_game._to_int(target_game.data.get("street_hapo_rescued", 0))
    target_game.data["street_hapo_rescued"] = str(count)
    target_game.save_data()
    
    refresh_user_cache(target_user_id)
    
    log_security(user_id, "تنظیم هاپوی خیابونی", f"کاربر {target_user_id}: {old_count} → {count}")
    
    await update.message.reply_text(
        f"✅ *تعداد هاپوهای خیابونی کاربر `{target_game.data.get('player_name', 'کاربر')}` از {old_count} به {count} تغییر یافت.*",
        parse_mode="Markdown"
    )


async def admin_add_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزایش تعداد هاپوی خیابونی کاربر"""
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("❌ *این دستور فقط در پیوی بات قابل استفاده است!*", parse_mode="Markdown")
        return
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *فقط ادمین میتونه از این دستور استفاده کنه!*", parse_mode="Markdown")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ *فرمت:* `/addstreethapo [user_id] [تعداد]`\n*مثال:* `/addstreethapo 123456789 5`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(parts[1])
        count = int(parts[2])
        if count <= 0:
            await update.message.reply_text("❌ *تعداد باید مثبت باشد*", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *لطفاً یک عدد معتبر وارد کن*", parse_mode="Markdown")
        return
    
    target_game = get_game(target_user_id)
    old_count = target_game._to_int(target_game.data.get("street_hapo_rescued", 0))
    new_count = old_count + count
    target_game.data["street_hapo_rescued"] = str(new_count)
    target_game.save_data()
    
    refresh_user_cache(target_user_id)
    
    log_security(user_id, "افزایش هاپوی خیابونی", f"کاربر {target_user_id}: +{count} → {new_count}")
    
    await update.message.reply_text(
        f"✅ *{count} هاپوی خیابونی به کاربر `{target_game.data.get('player_name', 'کاربر')}` اضافه شد.*\n"
        f"*تعداد فعلی:* {new_count}",
        parse_mode="Markdown"
    )
