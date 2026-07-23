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


def get_street_hapo():
    global street_hapo_instance
    if street_hapo_instance is None:
        street_hapo_instance = StreetHapo()
    return street_hapo_instance

async def show_hapo_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
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
        await update.message.reply_text("🐕 *هاپو*\n\n❌ *خطا در نمایش منوی هاپو. لطفاً دوباره تلاش کنید.*", parse_mode="Markdown")

async def do_hop(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
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
                logger.info(f"📊 گروه {chat_id}: هاپ={total_hops}, پوینت={total_points}")
    except Exception as e:
        logger.error(f"Error updating group stats in do_hop: {e}")
    hop_point = game._to_int(game.data["hop_point"])
    msg = f"🐾 *{result['earned']} هاپو پوینت گرفتی* ✨\n"
    msg += f"💰 *هاپو پوینت‌هات :* {format_number(hop_point)}"
    if result.get("level_up"):
        msg += f"\n\n🎉 *سطح شما به {result['new_level']} ارتقا یافت!*\n"
        msg += f"🎁 *جایزه: {format_number(result['reward'])} هاپو پوینت*"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def show_claw_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
        return
    level = game._to_int(game.data["level"])
    if level < 2:
        await update.message.reply_text("🔒 *پنجه از سطح 2 باز میشود*", parse_mode="Markdown")
        return
    claw_level = game._to_int(game.data["claw_level"])
    if claw_level == 0:
        cost = game.get_claw_cost(1)
        keyboard = [[InlineKeyboardButton(f"🛒 خرید پنجه ({format_number(cost)})", callback_data="buy_claw")]]
        msg = f"🦞 *شما پنجه ندارید*\n\n💰 *هزینه خرید: {format_number(cost)} هاپو پوینت*\n⏳ *زمان استراحت: 60:00*\n🍀 *شانس شکار:*\n  ⚪ معمولی: 95%\n  🔵 کمیاب: 5%"
        try:
            await update.message.reply_photo(photo=CLAW_IMAGES[1], caption=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
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
    try:
        await update.message.reply_photo(photo=CLAW_IMAGES[claw_level], caption=msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")

