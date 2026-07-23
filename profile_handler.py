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


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
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
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
        return
    
    target_user_id = None
    target_name = None
    
    # روش 1: ریپلای
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    
    # روش 2: آیدی یا یوزرنیم در متن
    else:
        parts = update.message.text.split()
        if len(parts) >= 2:
            identifier = parts[1].strip()
            if identifier.startswith('@'):
                identifier = identifier[1:]
            
            if identifier.isdigit():
                target_user_id = int(identifier)
                target_data = get_user_by_identifier(str(target_user_id))
                if target_data:
                    target_name = target_data.get('player_name', f"کاربر{target_user_id}")
                else:
                    await update.message.reply_text(f"❌ *کاربری با آیدی `{identifier}` یافت نشد.*", parse_mode="Markdown")
                    return
            else:
                target_data = get_user_by_identifier(identifier)
                if target_data:
                    target_user_id = int(target_data['user_id'])
                    target_name = target_data.get('player_name', f"کاربر{target_user_id}")
                else:
                    await update.message.reply_text(f"❌ *کاربری با یوزرنیم `@{identifier}` یافت نشد.*", parse_mode="Markdown")
                    return
        else:
            await update.message.reply_text(
                "❌ *لطفاً کاربر مورد نظر را مشخص کن.*\n\n"
                "📌 *روش‌های مشخص کردن کاربر:*\n"
                "1️⃣ ریپلای روی پیام کاربر\n"
                "2️⃣ نوشتن آیدی عددی: `هاپوهاش 123456789`\n"
                "3️⃣ نوشتن یوزرنیم: `هاپوهاش @username`",
                parse_mode="Markdown"
            )
            return
    
    if target_user_id is None:
        await update.message.reply_text("❌ *کاربر مورد نظر یافت نشد.*", parse_mode="Markdown")
        return
    
    if target_user_id == user_id:
        await update.message.reply_text("🔄 *برای مشاهده پروفایل خودت از «هاپوهام» استفاده کن.*", parse_mode="Markdown")
        return
    
    target_game = get_game(target_user_id)
    target_data = target_game.data
    
    if target_data.get("profile_hidden", False):
        msg = f"╮──「 🐶 *پروفایل هاپویی* 🐶 」\n\n"
        msg += f"┐─ 👤 *کاربر :* {target_name}\n"
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
    msg += f"┐─ 👤 *کاربر :* {target_name}\n"
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

