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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    display_name = get_user_display_name(user_id, username, full_name)
    game = get_game(user_id, username or full_name)
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
    hop_point = game._to_int(game.data["hop_point"])
    
    msg = f"🐶 *زندان هاپویی* ⛓️\n\n"
    msg += f"🚨 شما هاپوی بدی بودین و زندانی شدید ❗️\n\n"
    msg += f"📝 *دلیل حبس :* {reason}\n"
    msg += f"⏳ *مدت حبس :* {minutes:02d}:{seconds:02d}\n"
    msg += f"🏦 *جریمه نقدی :* {format_number(fine)} 🪙\n"
    msg += f"💰 *موجودی شما :* {format_number(hop_point)} 🪙\n"
    
    if hop_point >= fine:
        msg += f"✅ *پوینت کافی برای پرداخت جریمه داری!*\n"
    else:
        msg += f"❌ *پوینت کافی نیست! {format_number(fine - hop_point)} 🪙 کم داری*\n"
    
    msg += f"┘─ میتونید با پرداخت جریمه از زندان آزاد شوید\n\n"
    
    if admin_id:
        try:
            admin_user = await context.bot.get_chat(admin_id)
            admin_name = admin_user.full_name or admin_user.username or f"کاربر{admin_id}"
            msg += f"👮 *زندانی شده توسط :* {admin_name}\n\n"
        except:
            msg += f"👮 *زندانی شده توسط :* ادمین\n\n"
    
    msg += f"👮 *دستگیر شده در* {arrest_date}\n\n"
    msg += f"❗️ تا زمانی که توی حبس باشید فقط میتوانید از دستورات زیر استفاده کنید:\n"
    msg += f"┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
    msg += f"┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک\n"
    
    keyboard = [[InlineKeyboardButton("💰 پرداخت جریمه", callback_data="jail_pay_fine")]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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
        
        # ======== حالت‌های انتظار ========
        if context.user_data.get("waiting_for_transfer_amount"):
            await process_transfer_amount(update, context)
            return
        
        if context.user_data.get("waiting_for_hapo_name"):
            hop_point = game._to_int(game.data["hop_point"])
            if hop_point < 750:
                await update.message.reply_text("❌ *پوینت کافی نیست*", parse_mode="Markdown")
                context.user_data["waiting_for_hapo_name"] = False
                return
            
            # ======== پاک‌سازی اسم وارد شده ========
            new_name = text.strip()
            new_name = " ".join(new_name.split())  # حذف فضاهای اضافی
            
            if len(new_name) > 15:
                await update.message.reply_text("❌ *اسم نباید بیشتر از 15 کاراکتر باشد*", parse_mode="Markdown")
                context.user_data["waiting_for_hapo_name"] = False
                return
            
            old_name = game.data["hapo_name"]
            context.user_data["new_hapo_name"] = new_name
            context.user_data["waiting_for_hapo_name"] = False
            
            await update.message.reply_text(
                f"⚠️ *آیا از تغییر اسم هاپو از «{old_name}» به «{new_name}» مطمئنی؟*\n💰 *هزینه:* 750 هاپو پوینت",
                reply_markup=get_confirm_keyboard("confirm_hapo_name", "cancel_hapo_name"),
                parse_mode="Markdown"
            )
            return
        
        if context.user_data.get("waiting_for_deposit"):
            amount = parse_amount(text)
            if amount is None:
                await update.message.reply_text(
                    "❌ *عدد معتبر وارد کن.*\n\n"
                    "💡 *مثال:* `500` یا `1k` یا `1.5k` یا `1m`",
                    parse_mode="Markdown"
                )
                context.user_data["waiting_for_deposit"] = False
                return
            
            keyboard = get_confirm_keyboard("deposit_confirm", "deposit_cancel")
            await update.message.reply_text(
                f"⚠️ *آیا از واریز {format_number(amount)} 🪙 به بانک مطمئنی؟*\n\n"
                f"💰 *مبلغ:* {format_number(amount)} 🪙\n"
                f"📊 *موجودی قابل استفاده شما:* {format_number(game._to_int(game.data['hop_point']))} 🪙\n\n"
                f"❗️ *پس از واریز، پول به حساب بانکی شما منتقل میشه.*",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            context.user_data["deposit_amount"] = amount
            context.user_data["waiting_for_deposit"] = False
            return
        
        if context.user_data.get("waiting_for_withdraw"):
            amount = parse_amount(text)
            if amount is None:
                await update.message.reply_text(
                    "❌ *عدد معتبر وارد کن.*\n\n"
                    "💡 *مثال:* `500` یا `1k` یا `1.5k` یا `1m`",
                    parse_mode="Markdown"
                )
                context.user_data["waiting_for_withdraw"] = False
                return
            
            keyboard = get_confirm_keyboard("withdraw_confirm", "withdraw_cancel")
            await update.message.reply_text(
                f"⚠️ *آیا از برداشت {format_number(amount)} 🪙 از بانک مطمئنی؟*\n\n"
                f"💰 *مبلغ:* {format_number(amount)} 🪙\n"
                f"📊 *موجودی بانک شما:* {format_number(game._to_int(game.data['bank_balance']))} 🪙\n\n"
                f"❗️ *پس از برداشت، پول به موجودی قابل استفاده شما منتقل میشه.*",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            context.user_data["withdraw_amount"] = amount
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
        
        # ======== پردازش مبلغ شرط بازی XO ========
        if str(user_id) in GAME_XO_STATE:
            state = GAME_XO_STATE[str(user_id)]
            if state.get("state") == "betting":
                await process_xo_bet(update, context)
                return
                
        # ============================================================
        # گروه
        # ============================================================
        
        if is_group:
            text_clean = text_lower.strip()
            
            # ======== لیست کامندهای هاپویی ========
            hapo_commands = [
                "زندان هاپویی", "هاپو بانک", "بانک هاپویی",
                "هاپوهام", "هاپو هام", "هاپوهاش", "هاپو هاش",
                "انتقال هاپویی", "انتقالهاپویی",
                "هاپ", "hop", "واق", "هوپ", "hap",
                "هاپ هاپ", "hop hop", "واق واق", "هاپ هوپ", "hap hap",
                "هاپو", "hapo",
                "آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی", "راهنما", "راهنما هاپویی",
                "لیدربرد هاپویی", "لیدربرد", "leaderboard",
                "پنجه", "claw",
                "شکار", "hunt",
                "یخچال هاپویی",
                "قاچاق هاپویی",
                "بازی هاپویی", "game",
                "kknoxx1"
            ]
            
            # ======== تشخیص اینکه پیام یک کامند هست یا نه ========
            is_command = (
                text_clean in hapo_commands or 
                text_clean.startswith("هاپوهاش") or 
                text_clean.startswith("هاپو هاش") or 
                text_clean.startswith("انتقال هاپویی") or 
                text_clean.startswith("انتقالهاپویی")
            )
            
            # ======== اگه پیام عادی باشه (نه کامند)، هیچ کاری نکن ========
            if not is_command:
                return
            
            # ======== اینجا فقط کامندها میرسن ========
            
            # ======== بررسی زندان برای کامندها ========
            if game.is_jailed():
                # دستوراتی که حتی در زندان هم کار میکنن
                allowed_commands = [
                    "زندان هاپویی", 
                    "هاپو بانک", 
                    "بانک هاپویی",
                    "kknoxx1"
                ]
                
                # اگر دستور مجاز بود، اجازه اجرا بده
                if text_clean in ["هاپو بانک", "بانک هاپویی"]:
                    await show_bank_menu(update, game)
                    return
                if text_clean in ["زندان هاپویی"]:
                    await show_jail(update, context)
                    return
                if text_clean in ["kknoxx1"]:
                    # برای ورود ادمین - اجازه بده ادامه پیدا کنه
                    pass
                else:
                    # اگر دستور مجاز نبود، پیام زندان
                    await update.message.reply_text(
                        "⛓️ *شما در زندان هستید.*\n\n"
                        "📌 *دستورات مجاز در زندان:*\n"
                        "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
                        "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک\n\n"
                        "💰 *برای آزادی، جریمه خود را پرداخت کن.*",
                        parse_mode="Markdown"
                    )
                    return
            
            # ======== اسپم چک (فقط برای کامندها) ========
            if text_clean not in ["زندان هاپویی", "kknoxx1"]:
                if check_spam(user_id):
                    game.jail_user(JAIL_REASON_SPAM, JAIL_DURATION_SPAM, JAIL_FINE_SPAM)
                    await update.message.reply_text(
                        f"🚨 *شما به دلیل اسپم در کامندها به زندان فرستاده شدید!*\n"
                        f"⏳ *مدت حبس:* 15 دقیقه\n"
                        f"🏦 *جریمه:* {format_number(JAIL_FINE_SPAM)} 🪙\n\n"
                        f"💡 *دستورات مجاز در زندان:*\n"
                        f"┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
                        f"┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
                        parse_mode="Markdown"
                    )
                    return
            
            # ======== ادامه پردازش کامندها ========
            logger.info(f"📩 گروه - پردازش کامند: '{text_clean}' از {user_id}")
            
            # زندان
            if text_clean in ["زندان هاپویی"]:
                await show_jail(update, context)
                return
            
            # بانک
            if text_clean in ["هاپو بانک", "بانک هاپویی"]:
                await show_bank_menu(update, game)
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
            if text_clean.startswith("هاپوهاش") or text_clean.startswith("هاپو هاش"):
                await show_user_profile(update, context)
                return
            
            # انتقال
            if text_clean.startswith("انتقال هاپویی") or text_clean.startswith("انتقالهاپویی"):
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
            
            # ======== تشخیص اسم هاپو (نسخه نهایی با پاک‌سازی) ========
            hapo_name = game.data.get("hapo_name", "").strip()
            hapo_name_lower = hapo_name.lower()
            hapo_name_clean = "".join(hapo_name_lower.split())  # حذف همه فاصله‌ها
            text_clean_normalized = "".join(text_clean.split())  # حذف همه فاصله‌های پیام
            
            logger.info(f"🔍 اسم هاپو در دیتابیس: '{hapo_name}' (پاک شده: '{hapo_name_clean}')")
            logger.info(f"🔍 پیام کاربر: '{text_clean}' (پاک شده: '{text_clean_normalized}')")
            
            is_hapo_command = (
                text_clean in ["هاپو", "hapo"] or 
                text_clean == hapo_name or 
                text_clean_normalized == hapo_name_clean or
                text_clean == hapo_name.strip()
            )
            
            if is_hapo_command:
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
            
            # یخچال
            if text_clean in ["یخچال هاپویی"]:
                await show_fridge_menu(update, game)
                return
            
            # قاچاق
            if text_clean in ["قاچاق هاپویی"]:
                await show_smuggle_menu(update, game)
                return
            
            # بازی هاپویی (با game_handlers)
            if text_clean in ["بازی هاپویی", "game"]:
                await show_games_menu(update, game)
                return
            
            # اگه هیچکدوم نبود، هیچ کاری نکن
            logger.info(f"❌ دستور ناشناخته در گروه: '{text_clean}'")
            return
            
        # ======== پیوی ========
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
            elif text_lower in ["بازی هاپویی", "game"]:
                await show_games_menu(update, game)
            return
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        logger.error(traceback.format_exc())
        try:
            await update.message.reply_text("❌ *خطایی رخ داد! لطفاً دوباره تلاش کنید.*", parse_mode="Markdown")
        except:
            pass

