# handlers.py - هندلرهای پیام و کالبک (نسخه کامل نهایی)

import os
import json
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from config import (
    ADMIN_PASSWORD, MIN_MEMBERS_TO_STAY, RANK_NAMES, MAX_LEVEL,
    TRANSFER_MIN_AMOUNT, TRANSFER_MAX_AMOUNT, TRANSFER_COOLDOWN,
    TRANSFER_MIN_LEVEL_SENDER, TRANSFER_MIN_LEVEL_RECEIVER,
    BANK_PURCHASE_COST, JAIL_MAX_SPAM_COMMANDS, JAIL_SPAM_WINDOW,
    JAIL_DURATION_SPAM, JAIL_FINE_SPAM, JAIL_REASON_SPAM,
    JAIL_DURATION_MEOW, JAIL_FINE_MEOW, JAIL_REASON_MEOW,
    JAIL_VOTE_DURATION, JAIL_VOTE_NEEDED
)
from game import HopDogGame
from database import get_user_by_identifier, get_user_by_card
from bank import (
    get_bank_menu_text, get_bank_keyboard, get_change_card_confirm_text,
    get_card_to_card_text, format_number
)
from academy import (
    ACADEMY_MAIN, ACADEMY_SUB_SYSTEM, ACADEMY_SUB_FEATURES, ACADEMY_SUB_ADVENTURE,
    ACADEMY_SYSTEM_PAGE1, ACADEMY_SYSTEM_PAGE2, ACADEMY_SYSTEM_PAGE3, ACADEMY_SYSTEM_PAGE4,
    ACADEMY_ANIMALS_PAGE1, ACADEMY_ANIMALS_PAGE2, ACADEMY_ANIMALS_PAGE3,
    ACADEMY_CLAW_PAGE1, ACADEMY_CLAW_PAGE2, ACADEMY_CLAW_PAGE3,
    ACADEMY_HAPO, ACADEMY_HUNT, ACADEMY_BANK, ACADEMY_TRANSFER, ACADEMY_JAIL,
    ACADEMY_HOP, ACADEMY_POINTS, ACADEMY_EXP, ACADEMY_PROFILE,
    show_academy_main, show_academy_system_menu, show_academy_features_menu,
    show_academy_adventure_menu,
    show_academy_system_pages, show_academy_animals_pages, show_academy_claw_pages,
    show_feature_page, show_adventure_page
)

# دیکشنری‌های عمومی
user_games = {}
SPAM_TRACKER = {}
MEOW_VOTES = {}
TRANSFER_STATE = {}

def get_game(user_id, username=""):
    if user_id not in user_games:
        user_games[user_id] = HopDogGame(user_id, username)
    return user_games[user_id]

def get_user_link(user_id, username, full_name):
    display_name = full_name or f"کاربر{user_id}"
    if username:
        return f"@{username}"
    else:
        return f"[{display_name}](tg://user?id={user_id})"

# ================================================================
# توابع کمکی
# ================================================================

def get_confirm_keyboard(callback_data_yes, callback_data_no):
    keyboard = [
        [
            InlineKeyboardButton("✅ بله", callback_data=callback_data_yes),
            InlineKeyboardButton("❌ نه", callback_data=callback_data_no)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_hapo_menu_keyboard(game):
    keyboard = [
        [InlineKeyboardButton("💰 برداشت", callback_data="hapo_harvest")],
    ]
    
    total = game.get_hapo_total_level()
    is_max = total >= 25
    
    if is_max:
        keyboard[0].append(InlineKeyboardButton("🏆 نهایی", callback_data="hapo_max"))
    elif game.data["hapo_level"] >= 5 and game.data["hapo_rank"] < 4:
        price = game.get_hapo_rank_up_price()
        if price != float('inf'):
            keyboard.append([InlineKeyboardButton(f"🌟 ارتقا مقام ({format_number(price)})", callback_data="hapo_rank_up_confirm")])
    else:
        price = game.get_hapo_upgrade_price()
        if price != float('inf'):
            keyboard.append([InlineKeyboardButton(f"⬆️ ارتقا سطح ({format_number(price)})", callback_data="hapo_level_up")])
    
    if game.data["hop_point"] >= 750:
        keyboard.append([InlineKeyboardButton("✏️ تغییر اسم هاپو", callback_data="hapo_rename")])
    
    return InlineKeyboardMarkup(keyboard)

def get_hapo_menu_text(game):
    """متن منوی هاپو با فرمت جدید"""
    game.update_hapo_production()
    total = game.get_hapo_total_level()
    max_food = game.get_hapo_max_food()
    capacity = game.get_hapo_capacity()
    status = game.get_hapo_food_status()
    prod = game.get_hapo_production()
    price = game.get_hapo_upgrade_price()
    is_max = total >= 25
    
    msg = f"🐶 {game.data['hapo_name']}\n"
    msg += f"💕 نام : {game.data['hapo_name']}\n"
    msg += f"🍖 شکم : {status['text']} ({int(game.data['hapo_food'])}/{max_food})\n"
    msg += f"🌟 مقام : {RANK_NAMES[game.data['hapo_rank']]}\n"
    msg += f"⭐️ سطح : {game.data['hapo_level']}/5\n"
    msg += f"💰 هاپو پوینت های تولید شده : {int(game.data['hapo_harvest'])} 🪙\n"
    msg += f"💫 تولید هاپو پوینت در ثانیه : {prod:.2f} 🪙\n"
    msg += f"📦 ظرفیت : {format_number(capacity)}\n"
    
    if not is_max:
        if game.data["hapo_level"] >= 5 and game.data["hapo_rank"] < 4:
            rank_price = game.get_hapo_rank_up_price()
            msg += f"💰 هزینه ارتقا مقام : {format_number(rank_price)} 🪙"
        else:
            msg += f"💰 هزینه ارتقا سطح : {format_number(price)} 🪙"
    else:
        msg += "🏆 مقام نهایی"
    
    return msg

def check_spam(user_id):
    """بررسی اسپم بودن کاربر"""
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
# هندلر گروه (چک کردن تعداد ممبر)
# ================================================================

async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                try:
                    chat_id = update.message.chat.id
                    members_count = await context.bot.get_chat_member_count(chat_id)
                    
                    if members_count < MIN_MEMBERS_TO_STAY:
                        await update.message.reply_text(
                            f"❌ گروه شما خیلی کوچیکه ❌\n\n"
                            f"🔺 برای فعال کردن من باید حداقل {MIN_MEMBERS_TO_STAY} عضو داشته باشید.\n\n"
                            f"📊 تعداد اعضای فعلی: {members_count} نفر"
                        )
                        await context.bot.leave_chat(chat_id)
                    else:
                        await update.message.reply_text(
                            "🐕 یه هاپوی ناز اینجاست\n"
                            "...شروع کنید به هاپ هاپ 🐶\n\n"
                            "دستورات:\n"
                            "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
                            "📊 هاپوهام - مشاهده پروفایل خودت\n"
                            "⛓️ زندان هاپویی - اطلاعات زندان\n"
                            "📚 آکادمی - راهنمای کامل"
                        )
                except Exception as e:
                    logging.error(f"Error checking group members: {e}")
                break

# ================================================================
# دستورات اصلی (فقط در پیوی)
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    
    display_name = get_user_link(user_id, username, full_name)
    game = get_game(user_id, username or full_name)
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{context.bot.username}?startgroup=start")]
    ]
    
    if not game.data.get("has_seen_welcome", False):
        game.data["has_seen_welcome"] = True
        game.save_data()
        await update.message.reply_text(
            "🐾 ربات سرگرمی هاپویی 🐶\n\n"
            "🐕 یه هاپوی بامزه برای گروهت…\n"
            "کافیه توی گروه هاپ هاپ کنی تا هاپ پوینت بگیری 🐶\n\n"
            "⭐️ هاپ پوینت جمع کن و با بقیه رقابت کن\n"
            "🏆 لیدربرد هاپویی رو فتح کن و پادشاه هاپو ها شو\n\n"
            "✨ چرا هاپویی ؟\n\n"
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
            f"🐾 سلام {display_name}!\n"
            "به هاپ داگ خوش اومدی 🐕\n\n"
            "دستورات:\n"
            "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
            "📊 هاپوهام - مشاهده پروفایل خودت\n"
            "⛓️ زندان هاپویی - اطلاعات زندان\n"
            "📚 آکادمی - راهنمای کامل\n"
            "🔒 برای دستورات ادمین، از پیوی بات استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    await show_academy_main(update)

# ================================================================
# زندان هاپویی (با تاریخ دستگیری - فقط تاریخ)
# ================================================================

async def show_jail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اطلاعات زندان"""
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    jail_info = game.get_jail_info()
    if not jail_info:
        await update.message.reply_text("🐶 شما در زندان نیستید! آزاد هستید 🎉")
        return
    
    remaining = jail_info["remaining"]
    minutes = remaining // 60
    seconds = remaining % 60
    fine = jail_info["fine"]
    reason = jail_info["reason"]
    arrest_time = jail_info["arrest_time"]
    admin_id = jail_info.get("admin_id", None)
    
    # فقط تاریخ (بدون ساعت)
    arrest_date = datetime.fromtimestamp(arrest_time).strftime("%d %B %Y")
    
    msg = f"🐶 زندان هاپویی ⛓️\n\n"
    msg += f"🚨 شما هاپوی بدی بودین و زندانی شدید ❗️\n\n"
    msg += f"📝 دلیل حبس : {reason}\n"
    msg += f"⏳ مدت حبس : {minutes:02d}:{seconds:02d}\n"
    msg += f"🏦 جریمه نقدی : {format_number(fine)} 🪙\n"
    msg += f"┘─ میتونید با پرداخت جریمه از زندان آزاد شوید\n\n"
    
    if admin_id:
        try:
            admin_user = await context.bot.get_chat(admin_id)
            admin_name = admin_user.full_name or admin_user.username or f"کاربر{admin_id}"
            msg += f"👮 زندانی شده توسط : {admin_name}\n\n"
        except:
            msg += f"👮 زندانی شده توسط : ادمین\n\n"
    
    msg += f"👮 دستگیر شده در {arrest_date}\n\n"
    msg += f"❗️ تا زمانی که توی حبس باشید نمیتوانید از هیچ یک از امکانات ربات استفاده کنید.\n"
    msg += f"- با نوشتن \"زندان هاپویی\" میتوانید وارد سلول خود شوید"
    
    keyboard = [[InlineKeyboardButton("💰 پرداخت جریمه", callback_data="jail_pay_fine")]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
# ================================================================
# پروفایل - نسخه ساده شده (بدون تیک/ضربدر)
# ================================================================

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    required = game.get_required_for_level(game.data["level"])
    is_hidden = game.data.get("profile_hidden", False)
    is_locked = game.data.get("profile_locked", False)
    
    msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
    msg += f"┐─ 👤 کاربر : {full_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 آیدی : {user_id}\n\n"
    else:
        msg += f"‏┘─ 🪪 آیدی : 🔒 مخفی\n\n"
    
    msg += f"┐─ 💰 هاپ پوینت ها : {format_number(game.data['hop_point'])} 🪙\n"
    msg += f"┐─ 🐾 هاپ هاپ ها : {game.data['hop_count']}\n\n"
    
    if game.data["level"] < 20:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} | {game.data['hop_count']} / {required}"
    else:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} 🏆 نهایی"
    
    keyboard = []
    if is_hidden:
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide")])
    
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock")])
    
    # نمایش عکس پروفایل (اگه مخفی نباشه)
    if not is_hidden:
        try:
            user_photos = await context.bot.get_user_profile_photos(user_id, limit=1)
            if user_photos.total_count > 0:
                photo = user_photos.photos[0][-1]
                await update.message.reply_photo(
                    photo.file_id,
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
        except:
            pass
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ لطفاً روی پیام یک کاربر ریپلای کن و «هاپوهاش» رو بزن.")
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    target_username = update.message.reply_to_message.from_user.username
    target_full_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    
    target_game = get_game(target_user_id, target_username or target_full_name)
    
    game = get_game(user_id)
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    target_data = target_game.data
    
    if target_data.get("profile_hidden", False):
        msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
        msg += f"┐─ 👤 کاربر : {target_full_name}\n"
        msg += f"┘─ 🔒 این کاربر پروفایل خود را مخفی کرده است."
        await update.message.reply_text(msg)
        return
    
    required = target_game.get_required_for_level(target_data["level"])
    
    msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
    msg += f"┐─ 👤 کاربر : {target_full_name}\n"
    msg += f"‏┘─ 🪪 آیدی : {target_user_id}\n\n"
    msg += f"┐─ 💰 هاپ پوینت ها : {format_number(target_data['hop_point'])} 🪙\n"
    msg += f"┐─ 🐾 هاپ هاپ ها : {target_data['hop_count']}\n\n"
    
    if target_data["level"] < 20:
        msg += f"╯─ ⭐️ سطح : {target_data['level']} | {target_data['hop_count']} / {required}"
    else:
        msg += f"╯─ ⭐️ سطح : {target_data['level']} 🏆 نهایی"
    
    # نمایش عکس پروفایل (اگه مخفی نباشه)
    try:
        user_photos = await context.bot.get_user_profile_photos(target_user_id, limit=1)
        if user_photos.total_count > 0 and not target_data.get("profile_hidden", False):
            photo = user_photos.photos[0][-1]
            await update.message.reply_photo(
                photo.file_id,
                caption=msg
            )
            return
    except:
        pass
    
    await update.message.reply_text(msg)

# ================================================================
# پروفایل از کالبک - فقط متن (بدون عکس)
# ================================================================

async def my_profile_from_callback(query, game):
    user_id = int(game.user_id)
    full_name = game.data["player_name"]
    
    required = game.get_required_for_level(game.data["level"])
    is_hidden = game.data.get("profile_hidden", False)
    is_locked = game.data.get("profile_locked", False)
    
    msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
    msg += f"┐─ 👤 کاربر : {full_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 آیدی : {user_id}\n\n"
    else:
        msg += f"‏┘─ 🪪 آیدی : 🔒 مخفی\n\n"
    
    msg += f"┐─ 💰 هاپ پوینت ها : {format_number(game.data['hop_point'])} 🪙\n"
    msg += f"┐─ 🐾 هاپ هاپ ها : {game.data['hop_count']}\n\n"
    
    if game.data["level"] < 20:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} | {game.data['hop_count']} / {required}"
    else:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} 🏆 نهایی"
    
    keyboard = []
    if is_hidden:
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide")])
    
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock")])
    
    # ✅ فقط متن، بدون عکس
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# و در handle_callback - بخش پروفایل
# ================================================================

# ======== پروفایل - ساده (بدون تیک/ضربدر) ========
if data == "profile_hide":
    game.data["profile_hidden"] = True
    game.save_data()
    await query.edit_message_text("✅ پروفایل شما مخفی شد.")
    await my_profile_from_callback(query, game)
    return

if data == "profile_show":
    game.data["profile_hidden"] = False
    game.save_data()
    await query.edit_message_text("✅ پروفایل شما نمایش داده شد.")
    await my_profile_from_callback(query, game)
    return

if data == "profile_lock":
    game.data["profile_locked"] = True
    game.save_data()
    await query.edit_message_text("✅ پروفایل شما قفل شد.")
    await my_profile_from_callback(query, game)
    return

if data == "profile_unlock":
    game.data["profile_locked"] = False
    game.save_data()
    await query.edit_message_text("✅ پروفایل شما باز شد.")
    await my_profile_from_callback(query, game)
    return

# ================================================================
# دستورات هاپ، هاپو، پنجه، شکار (با چک زندان)
# ================================================================

async def do_hop(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    result = game.do_hop()
    if not result["success"]:
        remaining = result.get("remaining", 0)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        await update.message.reply_text(
            f"⏳ هنوز هاپت نمیاد ...\n"
            f"باید {mins}:{secs:02d} صبر کنی"
        )
        return
    
    msg = f"🐾 {result['earned']} هاپو پوینت گرفتی ✨\n"
    msg += f"💰 هاپو پوینت‌هات : {format_number(game.data['hop_point'])}"
    
    if result.get("level_up"):
        msg += f"\n\n🎉 سطح شما به {result['new_level']} ارتقا یافت!\n"
        msg += f"🎁 جایزه: {format_number(result['reward'])} هاپو پوینت"
    
    await update.message.reply_text(msg)

async def show_hapo_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    if not game.data["hapo_owned"]:
        if game.data["level"] < 3:
            await update.message.reply_text("🐕 هاپو از سطح 3 باز میشود")
            return
        if game.data["hop_point"] < 300:
            await update.message.reply_text("🐕 برای خرید هاپو به 300 هاپو پوینت نیاز داری")
            return
        keyboard = [
            [InlineKeyboardButton("🐕 خرید هاپو (300 هاپو پوینت)", callback_data="buy_hapo")]
        ]
        await update.message.reply_text(
            "🐕 آیا میخوای هاپو بخری؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    msg = get_hapo_menu_text(game)
    keyboard = get_hapo_menu_keyboard(game)
    await update.message.reply_text(msg, reply_markup=keyboard)

async def show_claw_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    if game.data["level"] < 2:
        await update.message.reply_text("🔒 پنجه از سطح 2 باز میشود")
        return
    
    if game.data["claw_level"] == 0:
        cost = game.get_claw_cost(1)
        keyboard = [
            [InlineKeyboardButton(f"🛒 خرید پنجه ({format_number(cost)})", callback_data="buy_claw")]
        ]
        await update.message.reply_text(
            f"🦞 شما پنجه ندارید\n"
            f"💰 هزینه خرید: {format_number(cost)} هاپو پوینت\n"
            f"⏳ زمان استراحت: 60:00\n"
            f"🍀 شانس شکار:\n"
            f"  ⚪ معمولی: 95%\n"
            f"  🔵 کمیاب: 5%",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    claw_data = game.get_claw_data(game.data["claw_level"])
    next_level = game.data["claw_level"] + 1
    next_data = game.get_claw_data(next_level)
    
    msg = f"🦞 پنجه شما\n"
    msg += f"⭐ سطح: {game.data['claw_level']}\n"
    msg += f"⏳ زمان استراحت: {claw_data['cooldown']:02d}:00\n"
    msg += f"🍀 شانس شکار:\n"
    msg += f"  ⚪ معمولی: {claw_data['common']}%\n"
    msg += f"  🔵 کمیاب: {claw_data['uncommon']}%\n"
    if claw_data['epic'] > 0:
        msg += f"  🟣 حماسی: {claw_data['epic']}%\n"
    if claw_data['legendary'] > 0:
        msg += f"  🟡 افسانه‌ای: {claw_data['legendary']}%\n"
    
    keyboard = []
    if next_data:
        keyboard.append([
            InlineKeyboardButton(f"⬆️ سطح {next_level} ({format_number(next_data['cost'])})", callback_data="upgrade_claw")
        ])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def do_hunt(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    result = game.do_hunt()
    
    if not result["success"]:
        reason = result.get("reason", "")
        if "فرار کرد" in reason:
            await update.message.reply_text(f"❌ {reason}")
        elif reason == "خسته‌ام":
            remaining = result.get("remaining", 0)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await update.message.reply_text(f"⏳ تا شکار بعدی {mins}:{secs:02d} مونده")
        elif "ثانیه مونده" in reason:
            await update.message.reply_text(f"⏳ {reason}")
        else:
            await update.message.reply_text(f"❌ {reason}")
        return
    
    hunt_msg = await update.message.reply_text("🏹 در حال شکار ...")
    await asyncio.sleep(2)
    
    animal = result["animal"]
    msg = f"شما با موفقیت {animal['emoji']} گرفتید…\n"
    msg += f"⭐️ سطح : {animal['rarity_name']}\n"
    msg += f"⚖️ وزن : {animal['weight']} کیلو\n"
    msg += f"💰 ارزش : {format_number(animal['value'])} 🪙\n"
    msg += f"🍖 ارزش غذایی : {animal['nutrition']} کالری\n\n"
    msg += f"⏳ 60 ثانیه فرصت انتخاب داری"
    
    keyboard = []
    keyboard.append([
        InlineKeyboardButton(f"💰 فروش ({format_number(animal['value'])})", callback_data="hunt_sell")
    ])
    if game.data["hapo_owned"]:
        keyboard.append([
            InlineKeyboardButton(f"🍖 به هاپو بده", callback_data="hunt_feed")
        ])
    
    await hunt_msg.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# دستورات بانک
# ================================================================

async def show_bank_menu(update: Update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    if game.data["level"] < 4:
        await update.message.reply_text("🏦 بانک هاپویی از سطح 4 باز میشود")
        return
    
    if not game.data["bank_opened"]:
        if game.data["hop_point"] < BANK_PURCHASE_COST:
            await update.message.reply_text(f"🏦 برای خرید بانک به {format_number(BANK_PURCHASE_COST)} هاپو پوینت نیاز داری")
            return
        keyboard = [
            [InlineKeyboardButton("🏦 خرید بانک", callback_data="buy_bank")]
        ]
        await update.message.reply_text(
            f"🏦 آیا میخوای بانک هاپویی رو بخری؟\n💰 هزینه: {format_number(BANK_PURCHASE_COST)} هاپو پوینت",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    game.apply_bank_interest()
    msg = get_bank_menu_text(game, False)
    keyboard = get_bank_keyboard(False)
    await update.message.reply_text(msg, reply_markup=keyboard)

# ================================================================
# دستور انتقال هاپویی (با چک زندان و جلوگیری از انتقال همزمان)
# ================================================================

async def transfer_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    if game.data["level"] < TRANSFER_MIN_LEVEL_SENDER:
        await update.message.reply_text(f"❌ برای انتقال هاپو پوینت باید سطح {TRANSFER_MIN_LEVEL_SENDER} باشی.")
        return
    
    if game.data.get("profile_locked", False):
        await update.message.reply_text("❌ پروفایل شما قفل است. ابتدا آن را باز کن.")
        return
    
    if game.data.get("is_transferring", False):
        await update.message.reply_text("⏳ شما در حال حاضر در حال انتقال هستید. لطفاً صبر کنید.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ لطفاً روی پیام یک کاربر ریپلای کن و «انتقال هاپویی» رو بزن.\n\n"
            "یا از این فرمت استفاده کن:\n"
            "`انتقال هاپویی @username 1000`\n"
            "`انتقال هاپویی 123456789 1000`",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    target_full_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    
    if target_user_id == user_id:
        await update.message.reply_text("❌ نمی‌تونی به خودت هاپو پوینت انتقال بدی!")
        return
    
    target_game = get_game(target_user_id)
    if target_game.data["level"] < TRANSFER_MIN_LEVEL_RECEIVER:
        await update.message.reply_text(f"❌ کاربر مقصد باید حداقل سطح {TRANSFER_MIN_LEVEL_RECEIVER} داشته باشد.")
        return
    
    if target_game.data.get("profile_locked", False):
        await update.message.reply_text("❌ پروفایل کاربر مقصد قفل است.")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "💰 مبلغ مورد نظر را به عدد وارد کن:\n"
            f"(حداقل: {format_number(TRANSFER_MIN_AMOUNT)} - حداکثر: {format_number(TRANSFER_MAX_AMOUNT)})"
        )
        context.user_data["waiting_for_transfer_amount"] = True
        TRANSFER_STATE[user_id] = {
            "target_id": target_user_id,
            "target_name": target_full_name
        }
        return
    
    try:
        amount = int(parts[-1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر برای مبلغ وارد کن.")
        return
    
    result = game.transfer_points(target_user_id, amount)
    if result["success"]:
        await update.message.reply_text(
            f"✅ انتقال موفقیت‌آمیز بود!\n\n"
            f"💰 {format_number(amount)} هاپو پوینت به {target_full_name} انتقال یافت."
        )
        try:
            await context.bot.send_message(
                target_user_id,
                f"💰 {full_name} مبلغ {format_number(amount)} هاپو پوینت به شما انتقال داد!"
            )
        except:
            pass
    else:
        await update.message.reply_text(f"❌ {result['reason']}")

async def process_transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not context.user_data.get("waiting_for_transfer_amount"):
        return
    
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    try:
        amount = int(update.message.text.strip().replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن.")
        return
    
    transfer_info = TRANSFER_STATE.get(user_id)
    if not transfer_info:
        await update.message.reply_text("❌ خطا در انتقال. لطفاً دوباره تلاش کن.")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    target_id = transfer_info["target_id"]
    target_name = transfer_info["target_name"]
    
    result = game.transfer_points(target_id, amount)
    if result["success"]:
        await update.message.reply_text(
            f"✅ انتقال موفقیت‌آمیز بود!\n\n"
            f"💰 {format_number(amount)} هاپو پوینت به {target_name} انتقال یافت."
        )
        try:
            await context.bot.send_message(
                target_id,
                f"💰 {full_name} مبلغ {format_number(amount)} هاپو پوینت به شما انتقال داد!"
            )
        except:
            pass
    else:
        await update.message.reply_text(f"❌ {result['reason']}")
    
    context.user_data["waiting_for_transfer_amount"] = False
    if user_id in TRANSFER_STATE:
        del TRANSFER_STATE[user_id]

# ================================================================
# سیستم میو (گربه بی ادب) - نسخه همزمان اصلاح شده
# ================================================================

async def handle_meow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    
    game = get_game(user_id)
    if game.is_jailed():
        await update.message.reply_text("⛓️ شما در زندان هستید و نمی‌توانید این کار را انجام دهید.")
        return
    
    # بررسی اینکه آیا خود این کاربر قبلاً نظرسنجی فعال داره
    for key, vote_data in MEOW_VOTES.items():
        if vote_data.get("target_id") == user_id:
            await update.message.reply_text("⚠️ شما یک نظرسنجی فعال دارید! صبر کنید تا تموم بشه.")
            return
    
    # کلید منحصر به فرد
    vote_key = f"{chat_id}_{user_id}_{int(datetime.now().timestamp())}"
    
    keyboard = [[InlineKeyboardButton("🗳️ رای به زندان", callback_data=f"meow_vote_{vote_key}")]]
    msg = await update.message.reply_text(
        f"😱 یک گربه ی بی ادب!\n"
        f"رای بدید که بفرستیمش زندان\n"
        f"0/{JAIL_VOTE_NEEDED}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    MEOW_VOTES[vote_key] = {
        "target_id": user_id,
        "votes": [],
        "msg_id": msg.message_id,
        "until": datetime.now().timestamp() + JAIL_VOTE_DURATION,
        "chat_id": chat_id,
        "msg_text": msg,
        "voters": []
    }
    
    asyncio.create_task(meow_vote_timer(vote_key, context))

async def meow_vote_timer(vote_key, context):
    """تایمر رای‌گیری میو"""
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
                    f"😡 گربه ی بی ادب!\n\n"
                    f"✅ با {votes_count} رای، کاربر به زندان فرستاده شد!",
                    chat_id=chat_id,
                    message_id=msg_id
                )
            except Exception as e:
                logging.error(f"Error editing meow vote result: {e}")
        else:
            try:
                await context.bot.edit_message_text(
                    f"😺 گربه ی بی ادب!\n\n"
                    f"❌ رای‌گیری به پایان رسید. کاربر آزاد است.",
                    chat_id=chat_id,
                    message_id=msg_id
                )
            except Exception as e:
                logging.error(f"Error editing meow vote result: {e}")
        
        try:
            del MEOW_VOTES[vote_key]
        except KeyError:
            pass

# ================================================================
# کامند ادمین - jail (زندانی کردن کاربر)
# ================================================================

async def jail_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور jail - زندانی کردن کاربر (فقط ادمین در پیوی)"""
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) < 4:
        await update.message.reply_text(
            "❌ فرمت: jail [آیدی/یوزرنیم] [مدت (دقیقه)] [دلیل]\n"
            "مثال: jail @username 5 Spam\n"
            "مثال: jail 123456789 10 Misbehave"
        )
        return
    
    identifier = parts[1]
    try:
        duration_minutes = int(parts[2])
        if duration_minutes <= 0:
            await update.message.reply_text("❌ مدت زمان باید مثبت باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ مدت زمان باید یک عدد باشد (دقیقه)")
        return
    
    reason = " ".join(parts[3:])
    if not reason:
        reason = "توسط ادمین"
    
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    
    # جریمه: 250 پوینت به ازای هر دقیقه
    fine = duration_minutes * 250
    
    # زندانی کردن با ذخیره آیدی ادمین
    target_game.jail_user_with_admin(reason, duration_minutes * 60, fine, user_id)
    
    admin_name = full_name or username or f"کاربر{user_id}"
    
    await update.message.reply_text(
        f"✅ کاربر `{user_data['player_name']}` به مدت {duration_minutes} دقیقه زندانی شد.\n"
        f"📝 دلیل: {reason}\n"
        f"🏦 جریمه: {format_number(fine)} 🪙"
    )
    
    # ارسال پیام به کاربر زندانی شده
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"🚨 شما توسط ادمین به زندان فرستاده شدید!\n"
            f"📝 دلیل: {reason}\n"
            f"⏳ مدت: {duration_minutes} دقیقه\n"
            f"🏦 جریمه: {format_number(fine)} 🪙\n"
            f"👮 زندانی شده توسط: {admin_name}\n\n"
            f"برای اطلاعات بیشتر «زندان هاپویی» را بزنید."
        )
    except:
        pass

# ================================================================
# هندلر اصلی پیام‌ها
# ================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    text = update.message.text.strip()
    text_lower = text.lower()
    is_private = update.message.chat.type == "private"
    is_group = update.message.chat.type in ["group", "supergroup"]
    
    if is_group:
        try:
            chat_id = update.message.chat.id
            chat_title = update.message.chat.title
            groups_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "groups.json")
            groups_data = {}
            if os.path.exists(groups_file):
                with open(groups_file, "r", encoding="utf-8") as f:
                    groups_data = json.load(f)
            groups_data[str(chat_id)] = {
                "title": chat_title,
                "added_at": datetime.now().isoformat()
            }
            with open(groups_file, "w", encoding="utf-8") as f:
                json.dump(groups_data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    # ======== چک کردن زندان (فقط برای کامندهای بات) ========
    if is_group and game.is_jailed():
        allowed_commands = ["زندان هاپویی", "زندان", "بانک هاپویی", "هاپو بانک", "بانک", "kknoxx1"]
        
        if text_lower not in allowed_commands:
            is_bot_command = False
            bot_commands = [
                "هاپ هاپ", "هاپ", "hop", "hop hop", "واق", "واق واق", "هاپ هوپ", "هوپ", "hap", "hap hap",
                "هاپو", "hapo", "پنجه", "claw", "شکار", "hunt",
                "هاپوهام", "هاپو هام", "هاپوهاش", "هاپو هاش",
                "انتقال هاپویی", "انتقالهاپویی",
                "آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی",
                "تغییر اسم", "اسم هاپویی"
            ]
            
            for cmd in bot_commands:
                if text_lower == cmd or text_lower.startswith(cmd):
                    is_bot_command = True
                    break
            
            if is_bot_command:
                await update.message.reply_text("⛓️ شما در زندان هستید. فقط با «زندان هاپویی» میتوانید وضعیت خود را ببینید.")
                return
    
    # ======== سیستم تشخیص اسپم (فقط در گروه) ========
    if is_group and text_lower not in ["زندان هاپویی", "زندان", "kknoxx1"]:
        if check_spam(user_id):
            game = get_game(user_id)
            game.jail_user(JAIL_REASON_SPAM, JAIL_DURATION_SPAM, JAIL_FINE_SPAM)
            await update.message.reply_text(
                f"🚨 شما به دلیل اسپم کردن به زندان فرستاده شدید!\n"
                f"⏳ مدت حبس: 15 دقیقه\n"
                f"🏦 جریمه: {format_number(JAIL_FINE_SPAM)} 🪙\n\n"
                f"برای اطلاعات بیشتر «زندان هاپویی» را بزنید."
            )
            return
    
    # ======== حالت‌های انتظار ========
    if context.user_data.get("waiting_for_hapo_name"):
        if game.data["hop_point"] < 750:
            await update.message.reply_text("❌ پوینت کافی نیست")
            context.user_data["waiting_for_hapo_name"] = False
            return
        
        if len(text) > 15:
            await update.message.reply_text("❌ اسم نباید بیشتر از 15 کاراکتر باشد")
            context.user_data["waiting_for_hapo_name"] = False
            return
        
        old_name = game.data["hapo_name"]
        context.user_data["new_hapo_name"] = text
        context.user_data["waiting_for_hapo_name"] = False
        
        confirm_text = f"⚠️ آیا از تغییر اسم هاپو از «{old_name}» به «{text}» مطمئنی؟\n💰 هزینه: 750 هاپو پوینت"
        await update.message.reply_text(
            confirm_text,
            reply_markup=get_confirm_keyboard("confirm_hapo_name", "cancel_hapo_name")
        )
        return
    
    if context.user_data.get("waiting_for_deposit"):
        try:
            amount = int(text.replace(",", ""))
            result = game.deposit(amount)
            if result["success"]:
                await update.message.reply_text(
                    f"✅ {format_number(amount)} هاپو پوینت به بانک واریز شد\n"
                    f"💰 موجودی بانک: {format_number(result['new_balance'])}"
                )
                await asyncio.sleep(2)
                await show_bank_menu(update, game)
            else:
                await update.message.reply_text(f"❌ {result['reason']}")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        context.user_data["waiting_for_deposit"] = False
        return
    
    if context.user_data.get("waiting_for_withdraw"):
        try:
            amount = int(text.replace(",", ""))
            result = game.withdraw(amount)
            if result["success"]:
                await update.message.reply_text(
                    f"✅ {format_number(amount)} هاپو پوینت از بانک برداشت شد\n"
                    f"💰 موجودی بانک: {format_number(result['new_balance'])}"
                )
                await asyncio.sleep(2)
                await show_bank_menu(update, game)
            else:
                await update.message.reply_text(f"❌ {result['reason']}")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        context.user_data["waiting_for_withdraw"] = False
        return
    
    if context.user_data.get("waiting_for_admin"):
        if text == ADMIN_PASSWORD:
            game.data["is_admin"] = True
            game.save_data()
            await update.message.reply_text("✅ شما ادمین شدید! 🛡️")
            await update.message.reply_text(
                "دستورات ادمین:\n"
                "userinfo [شناسه] - اطلاعات کاربر\n"
                "setlevel [شناسه] [عدد] - تنظیم سطح\n"
                "addlevel [شناسه] [عدد] - اضافه کردن سطح\n"
                "setpoint [شناسه] [عدد] - تنظیم پوینت\n"
                "addpoint [شناسه] [عدد] - اضافه کردن پوینت\n"
                "jail [شناسه] [مدت دقیقه] [دلیل] - زندانی کردن کاربر"
            )
        else:
            await update.message.reply_text("❌ رمز اشتباه است")
        context.user_data["waiting_for_admin"] = False
        return
    
    if context.user_data.get("waiting_for_transfer_amount"):
        await process_transfer_amount(update, context)
        return
    
    # ======== دستورات در پیوی ========
    if is_private:
        if text_lower in ["start", "/start"]:
            keyboard = [
                [InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{context.bot.username}?startgroup=start")]
            ]
            await update.message.reply_text(
                "🐾 این بات را به گروه خود اضافه کنید!\n"
                "برای دستورات ادمین از دستور kknoxx1 استفاده کنید.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif text_lower in ["/help", "help"]:
            await show_academy_main(update)
        elif text_lower == "kknoxx1":
            await update.message.reply_text("🔑 رمز ادمین را وارد کن:")
            context.user_data["waiting_for_admin"] = True
        return
    
    # ======== دستورات در گروه ========
    if is_group:
        if text_lower in ["زندان هاپویی", "زندان"]:
            await show_jail(update, context)
            return
        
        if text_lower in ["میو", "معو", "میاو", "میو میو", "mio", "mio mio", "meo", "meo meo", "meow", "meow meow"]:
            await handle_meow(update, context)
            return
        
        if text_lower in ["هاپوهام", "هاپو هام"]:
            await my_profile(update, context)
            return
        
        if text_lower in ["هاپوهاش", "هاپو هاش"]:
            await show_user_profile(update, context)
            return
        
        if text_lower in ["انتقال هاپویی", "انتقالهاپویی"]:
            await transfer_points_command(update, context)
            return
        
        if text_lower in ["هاپ هاپ", "هاپ", "hop", "hop hop", "واق", "واق واق", "هاپ هوپ", "هوپ", "hap", "hap hap"]:
            await do_hop(update, game)
            return
        
        if text_lower in ["آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی"]:
            await show_academy_main(update)
            return
        
        hapo_name_lower = game.data.get("hapo_name", "").lower()
        if text_lower in ["هاپو", "hapo"] or (hapo_name_lower and text_lower == hapo_name_lower):
            await show_hapo_menu(update, game)
            return
        
        if text_lower in ["پنجه", "claw"]:
            await show_claw_menu(update, game)
            return
        
        if text_lower in ["شکار", "hunt"]:
            await do_hunt(update, game)
            return
        
        if text_lower in ["بانک هاپویی", "هاپو بانک", "بانک"]:
            await show_bank_menu(update, game)
            return

# ================================================================
# هندلر Callback
# ================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    data = query.data
    
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
    
    if data == "confirm_hapo_name":
        new_name = context.user_data.get("new_hapo_name", "")
        if not new_name:
            await query.edit_message_text("❌ خطا در تغییر اسم")
            return
        
        if game.data["hop_point"] < 750:
            await query.edit_message_text("❌ پوینت کافی نیست")
            return
        
        old_name = game.data["hapo_name"]
        game.data["hapo_name"] = new_name
        game.data["hop_point"] -= 750
        game.save_data()
        
        await query.edit_message_text(f"✅ اسم هاپو از «{old_name}» به «{new_name}» تغییر یافت")
        context.user_data["new_hapo_name"] = None
        await asyncio.sleep(2)
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "cancel_hapo_name":
        await query.edit_message_text("❌ تغییر اسم هاپو لغو شد")
        context.user_data["new_hapo_name"] = None
        return
    
    # ======== پروفایل - ساده (بدون تیک/ضربدر) ========
    if data == "profile_hide":
        game.data["profile_hidden"] = True
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما مخفی شد.")
        await my_profile_from_callback(query, game)
        return

    if data == "profile_show":
        game.data["profile_hidden"] = False
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما نمایش داده شد.")
        await my_profile_from_callback(query, game)
        return

    if data == "profile_lock":
        game.data["profile_locked"] = True
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما قفل شد.")
        await my_profile_from_callback(query, game)
        return

    if data == "profile_unlock":
        game.data["profile_locked"] = False
        game.save_data()
        await query.edit_message_text("✅ پروفایل شما باز شد.")
        await my_profile_from_callback(query, game)
        return
    
    # ======== هاپو ========
    if data == "buy_hapo":
        result = game.buy_hapo()
        if result["success"]:
            await query.edit_message_text(
                f"✅ هاپو خریداری شد!\n"
                f"اسم هاپو: {result['name']}\n\n"
                f"💡 برای دیدن منوی هاپو، کلمه «هاپو» رو بزن"
            )
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "hapo_harvest":
        amount = int(game.data["hapo_harvest"])
        if amount > 0:
            game.data["hop_point"] += amount
            game.data["hapo_harvest"] = 0
            game.save_data()
            await query.edit_message_text(f"✅ {format_number(amount)} هاپو پوینت برداشت شد")
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard)
        else:
            await query.edit_message_text("❌ هیچ هاپو پوینتی برای برداشت نیست")
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "hapo_level_up":
        price = game.get_hapo_upgrade_price()
        if game.data["hop_point"] < price:
            await query.edit_message_text(f"❌ به {format_number(price)} هاپو پوینت نیاز داری")
            return
        game.data["hop_point"] -= price
        game.data["hapo_level"] += 1
        game.data["hapo_food"] = min(game.get_hapo_max_food(), int(game.data["hapo_food"] + 2))
        game.save_data()
        await query.edit_message_text(f"✅ سطح هاپو به {game.data['hapo_level']} ارتقا یافت")
        await asyncio.sleep(2)
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "hapo_rank_up_confirm":
        check = game.can_rank_up()
        if not check["success"]:
            await query.edit_message_text(f"❌ {check['reason']}")
            return
        
        price = game.get_hapo_rank_up_price()
        if game.data["hop_point"] < price:
            await query.edit_message_text(f"❌ به {format_number(price)} هاپو پوینت نیاز داری")
            return
        
        msg = f"⚠️ آیا از ارتقا مقام هاپو مطمئنی؟\n\n"
        msg += f"🌟 مقام فعلی: {RANK_NAMES[game.data['hapo_rank']]}\n"
        msg += f"🌟 مقام جدید: {RANK_NAMES[game.data['hapo_rank'] + 1]}\n"
        msg += f"💰 هزینه: {format_number(price)} هاپو پوینت\n\n"
        msg += "❗️ با ارتقا مقام:\n"
        msg += "┘─ سطح هاپو به 1 ریست میشود\n"
        msg += "┘─ تولیدی هاپو صفر میشود\n"
        msg += "┘─ ظرفیت هاپو افزایش می‌یابد\n"
        
        keyboard = get_confirm_keyboard("hapo_rank_up_yes", "hapo_rank_up_no")
        await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "hapo_rank_up_yes":
        result = game.confirm_rank_up()
        if result["success"]:
            await query.edit_message_text(
                f"✅ مقام هاپو به {result['new_rank_name']} ارتقا یافت!\n\n"
                f"🌟 سطح هاپو به 1 ریست شد\n"
                f"💰 تولیدی هاپو صفر شد\n"
                f"📦 ظرفیت هاپو افزایش یافت"
            )
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard)
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "hapo_rank_up_no":
        await query.edit_message_text("❌ ارتقا مقام لغو شد.")
        await asyncio.sleep(1)
        msg = get_hapo_menu_text(game)
        keyboard = get_hapo_menu_keyboard(game)
        await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "hapo_rename":
        if game.data["hop_point"] < 750:
            await query.edit_message_text("❌ به 750 هاپو پوینت نیاز داری")
            return
        await query.edit_message_text(
            "✏️ اسم جدید هاپو رو وارد کن:\n\n"
            "💡 فقط اسم جدید رو تایپ کن و ارسال کن."
        )
        context.user_data["waiting_for_hapo_name"] = True
        return
    
    if data == "buy_claw":
        result = game.buy_claw()
        if result["success"]:
            await query.edit_message_text("✅ پنجه خریداری شد!\nحالا میتونی با دستور شکار بری شکار")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "upgrade_claw":
        result = game.upgrade_claw()
        if result["success"]:
            await query.edit_message_text(f"✅ پنجه به سطح {result['new_level']} ارتقا یافت")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "hunt_sell":
        result = game.sell_animal()
        if result["success"]:
            await query.edit_message_text(
                f"💰 حیوان فروخته شد!\n"
                f"✅ {format_number(result['value'])} هاپو پوینت دریافت کردی"
            )
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "hunt_feed":
        result = game.feed_hapo()
        if result["success"]:
            await query.edit_message_text(
                f"🍖 {result['fed']} غذا به هاپو داده شد\n"
                f"✅ هاپو سیر شد!"
            )
        else:
            error_msg = result["reason"]
            animal = game.data.get("current_hunt_animal")
            if animal and "فرار کرد" in error_msg:
                await query.edit_message_text(f"❌ {error_msg}")
            elif animal and error_msg == "هاپو سیر است":
                await query.edit_message_text(
                    f"❌ هاپو سیر است!\n"
                    f"می‌تونی حیوان رو بفروشی یا بعداً به هاپو بدی.\n\n"
                    f"{animal['emoji']} {animal['name']}\n"
                    f"💰 ارزش: {format_number(animal['value'])} هاپو پوینت"
                )
                keyboard = [
                    [InlineKeyboardButton(f"💰 فروش ({format_number(animal['value'])})", callback_data="hunt_sell")]
                ]
                await query.message.reply_text(
                    "برای فروش کلیک کن:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.edit_message_text(f"❌ {error_msg}")
        return
    
    if data == "buy_bank":
        result = game.open_bank()
        if result["success"]:
            await query.edit_message_text(
                f"🏦 بانک هاپویی خریداری شد!\n"
                f"💳 شماره کارت شما: {result['card_number']}"
            )
            await asyncio.sleep(2)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard)
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "bank_deposit":
        await query.edit_message_text(
            "💰 مبلغ واریزی رو بنویس:\n\n"
            "💡 فقط عدد مبلغ رو تایپ کن و ارسال کن."
        )
        context.user_data["waiting_for_deposit"] = True
        return
    
    if data == "bank_withdraw":
        await query.edit_message_text(
            "💰 مبلغ برداشت رو بنویس:\n\n"
            "💡 فقط عدد مبلغ رو تایپ کن و ارسال کن."
        )
        context.user_data["waiting_for_withdraw"] = True
        return
    
    if data == "bank_card_to_card":
        await query.edit_message_text(get_card_to_card_text())
        context.user_data["waiting_for_card_to_card"] = True
        return
    
    if data == "bank_transactions":
        msg = get_bank_menu_text(game, True)
        keyboard = get_bank_keyboard(True)
        await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "bank_change_card":
        if not game.data["bank_opened"]:
            await query.edit_message_text("❌ شما بانک ندارید.")
            return
        
        msg = get_change_card_confirm_text(game)
        keyboard = get_confirm_keyboard("bank_change_card_yes", "bank_change_card_no")
        await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "bank_change_card_yes":
        result = game.change_card_number()
        if result["success"]:
            await query.edit_message_text(
                f"✅ شماره حساب شما تغییر کرد!\n"
                f"🔄 شماره قدیم: {result['old_card']}\n"
                f"🔄 شماره جدید: {result['new_card']}"
            )
            await asyncio.sleep(2)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard)
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "bank_change_card_no":
        await query.edit_message_text("❌ تغییر شماره حساب لغو شد.")
        await asyncio.sleep(1)
        msg = get_bank_menu_text(game, False)
        keyboard = get_bank_keyboard(False)
        await query.edit_message_text(msg, reply_markup=keyboard)
        return
    
    if data == "transfer_confirm":
        amount = context.user_data.get("transfer_amount")
        target_id = context.user_data.get("transfer_target")
        target_name = context.user_data.get("transfer_target_name")
        
        if not amount or not target_id:
            await query.edit_message_text("❌ خطا در انتقال. لطفاً دوباره تلاش کن.")
            return
        
        result = game.transfer_points(target_id, amount)
        if result["success"]:
            await query.edit_message_text(
                f"✅ انتقال موفقیت‌آمیز بود!\n\n"
                f"💰 {format_number(amount)} هاپو پوینت به {target_name} انتقال یافت."
            )
            try:
                await context.bot.send_message(
                    target_id,
                    f"💰 {game.data['player_name']} مبلغ {format_number(amount)} هاپو پوینت به شما انتقال داد!"
                )
            except:
                pass
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        
        context.user_data["transfer_amount"] = None
        context.user_data["transfer_target"] = None
        context.user_data["transfer_target_name"] = None
        return
    
    if data == "transfer_cancel":
        await query.edit_message_text("❌ انتقال لغو شد.")
        context.user_data["transfer_amount"] = None
        context.user_data["transfer_target"] = None
        context.user_data["transfer_target_name"] = None
        context.user_data["waiting_for_transfer_amount"] = False
        if user_id in TRANSFER_STATE:
            del TRANSFER_STATE[user_id]
        return
    
    # ======== میو (گربه بی ادب) ========
    if data.startswith("meow_vote_"):
        vote_key = data.replace("meow_vote_", "")
        
        if vote_key not in MEOW_VOTES:
            await query.edit_message_text("❌ رای‌گیری به پایان رسیده است.")
            return
        
        vote_data = MEOW_VOTES[vote_key]
        voter_id = user_id
        
        if voter_id == vote_data["target_id"]:
            await query.answer("❌ نمی‌تونی به خودت رای بدی!")
            return
        
        if voter_id in vote_data["votes"]:
            await query.answer("❌ تو قبلاً رای دادی!")
            return
        
        vote_data["votes"].append(voter_id)
        votes_count = len(vote_data["votes"])
        
        keyboard = [[InlineKeyboardButton("🗳️ رای به زندان", callback_data=f"meow_vote_{vote_key}")]]
        await query.edit_message_text(
            f"😱 یک گربه ی بی ادب!\n"
            f"رای بدید که بفرستیمش زندان\n"
            f"{votes_count}/{JAIL_VOTE_NEEDED}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await query.answer("✅ رای شما ثبت شد!")
        
        if votes_count >= JAIL_VOTE_NEEDED:
            target_id = vote_data["target_id"]
            target_game = get_game(target_id)
            target_game.jail_user(JAIL_REASON_MEOW, JAIL_DURATION_MEOW, JAIL_FINE_MEOW)
            
            await query.edit_message_text(
                f"😡 گربه ی بی ادب!\n\n"
                f"✅ با {votes_count} رای، کاربر به زندان فرستاده شد!"
            )
            del MEOW_VOTES[vote_key]
        return
    
    if data == "jail_pay_fine":
        if not game.is_jailed():
            await query.edit_message_text("❌ شما در زندان نیستید.")
            return
        
        fine = game.data.get("jail_fine", 0)
        keyboard = get_confirm_keyboard("jail_pay_fine_yes", "jail_pay_fine_no")
        await query.edit_message_text(
            f"⚠️ آیا از پرداخت جریمه {format_number(fine)} 🪙 مطمئنی؟\n\n"
            f"با پرداخت جریمه از زندان آزاد میشوی.",
            reply_markup=keyboard
        )
        return
    
    if data == "jail_pay_fine_yes":
        result = game.pay_jail_fine()
        if result["success"]:
            await query.edit_message_text("✅ جریمه پرداخت شد و شما آزاد شدید! 🎉")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    if data == "jail_pay_fine_no":
        await query.edit_message_text("❌ پرداخت جریمه لغو شد.")
        return

# ================================================================
# پروفایل از کالبک - ساده شده (بدون عکس)
# ================================================================

async def my_profile_from_callback(query, game):
    user_id = int(game.user_id)
    full_name = game.data["player_name"]
    
    required = game.get_required_for_level(game.data["level"])
    is_hidden = game.data.get("profile_hidden", False)
    is_locked = game.data.get("profile_locked", False)
    
    msg = f"╮──「 🐶 پروفایل هاپویی 🐶 」\n\n"
    msg += f"┐─ 👤 کاربر : {full_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 آیدی : {user_id}\n\n"
    else:
        msg += f"‏┘─ 🪪 آیدی : 🔒 مخفی\n\n"
    
    msg += f"┐─ 💰 هاپ پوینت ها : {format_number(game.data['hop_point'])} 🪙\n"
    msg += f"┐─ 🐾 هاپ هاپ ها : {game.data['hop_count']}\n\n"
    
    if game.data["level"] < 20:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} | {game.data['hop_count']} / {required}"
    else:
        msg += f"╯─ ⭐️ سطح : {game.data['level']} 🏆 نهایی"
    
    keyboard = []
    if is_hidden:
        keyboard.append([InlineKeyboardButton("👀 نمایش پروفایل", callback_data="profile_show")])
    else:
        keyboard.append([InlineKeyboardButton("👀 مخفی کردن پروفایل", callback_data="profile_hide")])
    
    if is_locked:
        keyboard.append([InlineKeyboardButton("🔓 باز کردن پروفایل", callback_data="profile_unlock")])
    else:
        keyboard.append([InlineKeyboardButton("🔒 قفل کردن پروفایل", callback_data="profile_lock")])
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# دستورات ادمین (فقط در پیوی)
# ================================================================

async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید. فقط ادمین‌ها میتونن استفاده کنن.")
        return
    
    parts = update.message.text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ لطفاً شناسه کاربر را وارد کن.\n\n"
            "📌 مثال:\n"
            "🔹 با آیدی عددی: `userinfo 123456789`\n"
            "🔹 با یوزرنیم: `userinfo @username`",
            parse_mode="Markdown"
        )
        return
    
    identifier = parts[1]
    user_data = get_user_by_identifier(identifier)
    
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    msg = f"📊 اطلاعات کاربر:\n\n"
    msg += f"🆔 آیدی: `{user_data['user_id']}`\n"
    msg += f"👤 نام: {user_data['player_name']}\n"
    msg += f"⭐ سطح: {user_data['level']}\n"
    msg += f"💰 هاپو پوینت: {format_number(user_data['hop_point'])}\n"
    msg += f"🐾 تعداد هاپ: {user_data['hop_count']}\n"
    
    if user_data.get('hapo_owned', False):
        msg += f"\n🐕 هاپو:\n"
        msg += f"  📛 نام: {user_data['hapo_name']}\n"
        msg += f"  ⭐ سطح: {user_data['hapo_level']}/5\n"
        msg += f"  🌟 مقام: {RANK_NAMES[user_data['hapo_rank']]}\n"
    
    if user_data.get('bank_opened', False):
        msg += f"\n🏦 بانک:\n"
        msg += f"  💰 موجودی: {format_number(user_data['bank_balance'])}\n"
        msg += f"  💳 شماره کارت: {user_data.get('bank_card_number', 'نامشخص')}\n"
    
    msg += f"\n📅 آخرین بروزرسانی: {user_data.get('last_updated', 'نامشخص')}"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def set_user_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ فرمت: setlevel [آیدی/یوزرنیم] [عدد]\nمثال: setlevel @username 5")
        return
    
    identifier = parts[1]
    try:
        new_level = int(parts[2])
        if not 1 <= new_level <= MAX_LEVEL:
            await update.message.reply_text(f"❌ سطح باید بین 1 تا {MAX_LEVEL} باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        return
    
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    old_level = target_game.data["level"]
    target_game.data["level"] = new_level
    target_game.data["hop_count"] = 0
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ سطح کاربر `{user_data['player_name']}` از {old_level} به {new_level} تغییر یافت.",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"⭐ سطح هاپویی شما به {new_level} تغییر یافت!"
        )
    except:
        pass

async def add_user_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ فرمت: addlevel [آیدی/یوزرنیم] [عدد]\nمثال: addlevel @username 5")
        return
    
    identifier = parts[1]
    try:
        add_amount = int(parts[2])
        if add_amount <= 0:
            await update.message.reply_text("❌ مقدار باید مثبت باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        return
    
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    old_level = target_game.data["level"]
    new_level = min(old_level + add_amount, MAX_LEVEL)
    target_game.data["level"] = new_level
    target_game.data["hop_count"] = 0
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ {add_amount} سطح به کاربر `{user_data['player_name']}` اضافه شد.\n"
        f"سطح جدید: {new_level}",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"⭐ {add_amount} سطح به هاپوهای شما اضافه شد!\nسطح جدید: {new_level}"
        )
    except:
        pass

async def set_user_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ فرمت: setpoint [آیدی/یوزرنیم] [عدد]\nمثال: setpoint @username 1000")
        return
    
    identifier = parts[1]
    try:
        new_point = int(parts[2])
        if new_point < 0:
            await update.message.reply_text("❌ پوینت نمی‌تواند منفی باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        return
    
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    old_point = target_game.data["hop_point"]
    target_game.data["hop_point"] = new_point
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ پوینت کاربر `{user_data['player_name']}` از {format_number(old_point)} به {format_number(new_point)} تغییر یافت.",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"💰 هاپو پوینت‌های شما به {format_number(new_point)} تغییر یافت!"
        )
    except:
        pass

async def add_user_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not game.data.get("is_admin", False):
        await update.message.reply_text("❌ شما ادمین نیستید")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ فرمت: addpoint [آیدی/یوزرنیم] [عدد]\nمثال: addpoint @username 1000")
        return
    
    identifier = parts[1]
    try:
        add_amount = int(parts[2])
        if add_amount <= 0:
            await update.message.reply_text("❌ مقدار باید مثبت باشد")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        return
    
    user_data = get_user_by_identifier(identifier)
    if not user_data:
        await update.message.reply_text(f"❌ کاربری با شناسه `{identifier}` در دیتابیس ثبت نشده است.", parse_mode="Markdown")
        return
    
    target_user_id = user_data['user_id']
    target_game = get_game(int(target_user_id))
    old_point = target_game.data["hop_point"]
    new_point = old_point + add_amount
    target_game.data["hop_point"] = new_point
    target_game.save_data()
    
    await update.message.reply_text(
        f"✅ {format_number(add_amount)} هاپو پوینت به کاربر `{user_data['player_name']}` اضافه شد.\n"
        f"پوینت جدید: {format_number(new_point)}",
        parse_mode="Markdown"
    )
    
    try:
        await context.bot.send_message(
            int(target_user_id),
            f"💰 {format_number(add_amount)} هاپو پوینت به حساب شما اضافه شد!\nموجودی جدید: {format_number(new_point)}"
        )
    except:
        pass
