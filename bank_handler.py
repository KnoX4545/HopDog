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


async def show_bank_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
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
        await update.message.reply_text("🏦 *بانک هاپویی*\n\n❌ *خطا در نمایش بانک. لطفاً دوباره تلاش کنید.*", parse_mode="Markdown")

async def transfer_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
        return
    
    level = game._to_int(game.data.get("level", 1))
    if level < TRANSFER_MIN_LEVEL_SENDER:
        await update.message.reply_text(f"❌ *برای انتقال هاپو پوینت باید سطح {TRANSFER_MIN_LEVEL_SENDER} باشی.*", parse_mode="Markdown")
        return
    
    if game.data.get("profile_locked", False):
        await update.message.reply_text("❌ *پروفایل شما قفل است. ابتدا آن را باز کن.*", parse_mode="Markdown")
        return
    
    if game.data.get("is_transferring", False):
        await update.message.reply_text("⏳ *شما در حال حاضر در حال انتقال هستید. لطفاً صبر کنید.*", parse_mode="Markdown")
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
            
            # بررسی عددی یا متنی
            if identifier.isdigit():
                # آیدی عددی
                target_user_id = int(identifier)
                target_data = get_user_by_identifier(str(target_user_id))
                if target_data:
                    target_name = target_data.get('player_name', f"کاربر{target_user_id}")
                else:
                    await update.message.reply_text(f"❌ *کاربری با آیدی `{identifier}` یافت نشد.*", parse_mode="Markdown")
                    return
            else:
                # یوزرنیم
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
                "2️⃣ نوشتن آیدی عددی: `انتقال هاپویی 123456789`\n"
                "3️⃣ نوشتن یوزرنیم: `انتقال هاپویی @username`\n\n"
                "💰 *سپس مبلغ مورد نظر را در مرحله بعد وارد کن.*",
                parse_mode="Markdown"
            )
            return
    
    if target_user_id is None:
        await update.message.reply_text("❌ *کاربر مورد نظر یافت نشد.*", parse_mode="Markdown")
        return
    
    if target_user_id == user_id:
        await update.message.reply_text("❌ *نمی‌تونی به خودت هاپو پوینت انتقال بدی!*", parse_mode="Markdown")
        return
    
    target_game = get_game(target_user_id)
    target_level = target_game._to_int(target_game.data.get("level", 1))
    if target_level < TRANSFER_MIN_LEVEL_RECEIVER:
        await update.message.reply_text(f"❌ *کاربر مقصد باید حداقل سطح {TRANSFER_MIN_LEVEL_RECEIVER} داشته باشد.*", parse_mode="Markdown")
        return
    
    if target_game.data.get("profile_locked", False):
        await update.message.reply_text("❌ *پروفایل کاربر مقصد قفل است.*", parse_mode="Markdown")
        return
    
    context.user_data["transfer_target_id"] = str(target_user_id)
    context.user_data["transfer_target_name"] = target_name
    context.user_data["waiting_for_transfer_amount"] = True
    
    hop_point = game._to_int(game.data.get("hop_point", 0))
    await update.message.reply_text(
        f"💰 *مبلغ مورد نظر برای انتقال به {target_name} رو وارد کن:*\n\n"
        f"📊 *موجودی شما:* {format_number(hop_point)} 🪙\n"
        f"🔻 *حداقل:* {format_number(TRANSFER_MIN_AMOUNT)} 🪙\n"
        f"🔺 *حداکثر:* {format_number(TRANSFER_MAX_AMOUNT)} 🪙\n\n"
        f"💡 *میتونی از اختصارات استفاده کنی:*\n"
        f"┘─ `1k` = 1,000 | `1.5k` = 1,500\n"
        f"┘─ `1m` = 1,000,000 | `1.5m` = 1,500,000\n"
        f"┘─ `1کا` = 1,000 | `1میل` = 1,000,000\n\n"
        f"💡 *فقط عدد یا اختصار رو تایپ کن و ارسال کن.*",
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
        await update.message.reply_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    text = update.message.text.strip()
    
    amount = parse_amount(text)
    if amount is None:
        await update.message.reply_text(
            "❌ *عدد معتبر وارد کن.*\n\n"
            "💡 *مثال:* `500` یا `1k` یا `1.5k` یا `1m`",
            parse_mode="Markdown"
        )
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ *مبلغ باید بیشتر از صفر باشد.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    target_id = context.user_data.get("transfer_target_id")
    target_name = context.user_data.get("transfer_target_name")
    
    if not target_id or not target_name:
        await update.message.reply_text("❌ *خطا در انتقال. لطفاً دوباره تلاش کن.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    try:
        target_id = int(target_id)
    except:
        await update.message.reply_text("❌ *خطا در شناسه کاربر مقصد.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    if amount < TRANSFER_MIN_AMOUNT:
        await update.message.reply_text(f"❌ *حداقل مبلغ انتقال {format_number(TRANSFER_MIN_AMOUNT)} هاپو پوینت است.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    if amount > TRANSFER_MAX_AMOUNT:
        await update.message.reply_text(f"❌ *حداکثر مبلغ انتقال {format_number(TRANSFER_MAX_AMOUNT)} هاپو پوینت است.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    hop_point = game._to_int(game.data.get("hop_point", 0))
    if hop_point < amount:
        await update.message.reply_text(f"❌ *موجودی کافی نیست. شما {format_number(hop_point)} هاپو پوینت داری.*", parse_mode="Markdown")
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
        f"⚠️ *آیا از انتقال {format_number(amount)} 🪙 به {target_name} مطمئنی؟*\n\n"
        f"💰 *مبلغ:* {format_number(amount)} 🪙\n"
        f"👤 *گیرنده:* {target_name}\n"
        f"📊 *موجودی شما پس از انتقال:* {format_number(hop_point - amount)} 🪙\n\n"
        f"❗️ *محدودیت‌ها:*\n"
        f"┘─ *حداقل:* {format_number(TRANSFER_MIN_AMOUNT)} 🪙\n"
        f"┘─ *حداکثر:* {format_number(TRANSFER_MAX_AMOUNT)} 🪙\n"
        f"┘─ *فاصله بین انتقال‌ها:* {TRANSFER_COOLDOWN} ثانیه",
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
        await query.edit_message_text("❌ *خطا در اطلاعات انتقال.*", parse_mode="Markdown")
        return
    try:
        target_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        await query.edit_message_text("❌ *خطا در اطلاعات انتقال.*", parse_mode="Markdown")
        return
    if game.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید و نمی‌توانید این کار را انجام دهید.*", parse_mode="Markdown")
        return
    hop_point = game._to_int(game.data.get("hop_point", 0))
    if hop_point < amount:
        await query.edit_message_text(f"❌ *موجودی کافی نیست. شما {format_number(hop_point)} هاپو پوینت داری.*", parse_mode="Markdown")
        return
    result = game.transfer_points(target_id, amount)
    if result["success"]:
        target_game = get_game(target_id)
        target_name = target_game.data.get("player_name", f"کاربر{target_id}")
        new_balance = game._to_int(game.data.get("hop_point", 0))
        await query.edit_message_text(
            f"✅ *انتقال موفقیت‌آمیز بود!*\n\n"
            f"💰 *{format_number(amount)} 🪙 به {target_name} انتقال یافت.*\n"
            f"📊 *موجودی شما:* {format_number(new_balance)} 🪙",
            parse_mode="Markdown"
        )
        try:
            target_new_balance = target_game._to_int(target_game.data.get("hop_point", 0))
            await context.bot.send_message(
                target_id,
                f"💰 *{full_name} مبلغ {format_number(amount)} 🪙 به شما انتقال داد!*\n"
                f"📊 *موجودی شما:* {format_number(target_new_balance)} 🪙",
                parse_mode="Markdown"
            )
        except:
            pass
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
    context.user_data["transfer_amount"] = None
    context.user_data["transfer_target_id"] = None
    context.user_data["transfer_target_name"] = None
    context.user_data["waiting_for_transfer_amount"] = False

async def handle_transfer_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ *انتقال لغو شد.*", parse_mode="Markdown")
    context.user_data["transfer_amount"] = None
    context.user_data["transfer_target_id"] = None
    context.user_data["transfer_target_name"] = None
    context.user_data["waiting_for_transfer_amount"] = False

