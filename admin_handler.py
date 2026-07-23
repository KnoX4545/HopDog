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


async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        return
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ *شما دسترسی به این دستور ندارید. فقط ادمین‌ها میتونن استفاده کنن.*", parse_mode="Markdown")
        return
    help_text = (
        "🛡️ *دستورات ادمین هاپویی*\n\n"
        "📊 *مدیریت کاربران:*\n"
        "`/userinfo [id]` - اطلاعات کاربر\n"
        "`/setlevel [id] [level]` - تنظیم سطح\n"
        "`/addlevel [id] [level]` - اضافه کردن سطح\n"
        "`/setpoint [id] [point]` - تنظیم پوینت (میتونی از اختصارات استفاده کنی: 1k, 1m)\n"
        "`/addpoint [id] [point]` - اضافه کردن پوینت (میتونی از اختصارات استفاده کنی: 1k, 1m)\n"
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

async def jail_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("❌ *فرمت:* `jail [آیدی/یوزرنیم] [مدت (دقیقه)] [دلیل]`\n*مثال:* `jail @username 5 Spam`", parse_mode="Markdown")
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
        await update.message.reply_text(f"❌ *کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.*", parse_mode="Markdown")
        return
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    fine = duration_minutes * 250
    target_game.jail_user_with_admin(reason, duration_minutes * 60, fine, user_id)
    admin_name = full_name or username or f"کاربر{user_id}"
    await update.message.reply_text(
        f"✅ *کاربر `{user_data['player_name']}` به مدت {duration_minutes} دقیقه زندانی شد.*\n"
        f"📝 *دلیل:* {reason}\n🏦 *جریمه:* {format_number(fine)} 🪙",
        parse_mode="Markdown"
    )
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"🚨 *شما توسط ادمین به زندان فرستاده شدید!*\n📝 *دلیل:* {reason}\n⏳ *مدت:* {duration_minutes} دقیقه\n🏦 *جریمه:* {format_number(fine)} 🪙\n👮 *زندانی شده توسط:* {admin_name}\n\nبرای اطلاعات بیشتر «زندان هاپویی» را بزنید.",
            parse_mode="Markdown"
        )
    except:
        pass

async def reset_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("❌ *فرمت:* `/rest [user_id یا @username]`\n*مثال:* `/rest 123456789`", parse_mode="Markdown")
        return
    identifier = parts[1]
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ *کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.*", parse_mode="Markdown")
        return
    target_user_id = user_data['user_id']
    target_name = user_data.get('player_name', f"کاربر{target_user_id}")
    keyboard = get_confirm_keyboard(f"rest_confirm_{target_user_id}", f"rest_cancel_{target_user_id}")
    await update.message.reply_text(
        f"⚠️ *آیا از ریست کردن کاربر `{target_name}` مطمئنی؟*\n\n🆔 *آیدی:* `{target_user_id}`\n\n❗️ *این کار **همه** اطلاعات کاربر رو به حالت اولیه برمیگردونه.*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def reset_user_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id):
    user_id = update.effective_user.id
    game = get_game(user_id)
    if not game.data.get("is_admin", False):
        await update.callback_query.answer("❌ فقط ادمین!")
        return
    try:
        target_game = get_game(int(target_user_id))
        player_name = target_game.data.get("player_name", f"کاربر{target_user_id}")
        target_game.reset_data()
        if int(target_user_id) in user_games:
            del user_games[int(target_user_id)]
        await update.callback_query.edit_message_text(
            f"✅ *کاربر `{player_name}` با موفقیت ریست شد!*\n\n🆔 *آیدی:* `{target_user_id}`\n👤 *نام:* {target_game.data['player_name']}\n\n📊 *همه اطلاعات به حالت اولیه برگشت.*",
            parse_mode="Markdown"
        )
        try:
            await context.bot.send_message(
                int(target_user_id),
                f"🔒 *حساب هاپویی شما توسط ادمین ریست شد!*\n\n📊 *همه اطلاعات شما به حالت اولیه برگشت.*\n💰 *هاپو پوینت:* 0\n⭐ *سطح:* 1\n\n💡 *دوباره از ابتدا شروع کن!* 🐶",
                parse_mode="Markdown"
            )
        except:
            pass
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ *خطا در ریست کاربر:* {e}", parse_mode="Markdown")

async def reset_user_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("❌ *عملیات ریست لغو شد.*", parse_mode="Markdown")

async def admin_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("❌ *فرمت:* `/hapo [chat_id]`\n*مثال:* `/hapo -1003708381360`", parse_mode="Markdown")
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
        asyncio.create_task(street_hapo_timer(street_hapo, context))
        await update.message.reply_text(f"✅ *هاپوی خیابونی به گروه با chat_id `{parts[1]}` ارسال شد!*", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending admin street hapo: {e}")
        street_hapo.active = False
        street_hapo.save_status()
        await update.message.reply_text(f"❌ *خطا در ارسال:* {e}", parse_mode="Markdown")

async def admin_set_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("❌ *فرمت:* `/setstreethapo [user_id] [تعداد]`\n*مثال:* `/setstreethapo 123456789 5`", parse_mode="Markdown")
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
    await update.message.reply_text(
        f"✅ *تعداد هاپوهای خیابونی کاربر `{target_game.data.get('player_name', 'کاربر')}` از {old_count} به {count} تغییر یافت.*",
        parse_mode="Markdown"
    )

async def admin_add_street_hapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("❌ *فرمت:* `/addstreethapo [user_id] [تعداد]`\n*مثال:* `/addstreethapo 123456789 5`", parse_mode="Markdown")
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
    await update.message.reply_text(
        f"✅ *{count} هاپوی خیابونی به کاربر `{target_game.data.get('player_name', 'کاربر')}` اضافه شد.*\n"
        f"*تعداد فعلی:* {new_count}",
        parse_mode="Markdown"
    )

