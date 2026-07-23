# handlers.py - هندلرهای پیام و کالبک (نسخه نهایی کامل)

import os
import json
import asyncio
import logging
import random
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
from game import HopDogGame, StreetHapo
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

# ================================================================
# Import بازی‌ها (با GAME_XO_STATE)
# ================================================================

from utils import parse_amount, get_confirm_keyboard, get_game
from game_functions import game_manager
from game_handlers import (
    show_games_menu, show_xo_main, handle_xo_set_bet, process_xo_bet,
    handle_xo_create, handle_xo_join, handle_xo_move,
    handle_xo_close, handle_xo_cancel,
    GAME_XO_STATE
)

# ================================================================
# دیکشنری‌های عمومی
# ================================================================

user_games = {}
SPAM_TRACKER = {}
MEOW_VOTES = {}
TRANSFER_STATE = {}
STREET_HAPO_LAST_SENT = {}
street_hapo_instance = None

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================================================================
# توابع کمکی
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

