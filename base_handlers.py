# base_handlers.py - توابع پایه (شروع، راهنما، قوانین، خوش‌آمدگویی، پیام‌ها)

import asyncio
import logging
import random
import traceback
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    ADMIN_PASSWORD, MIN_MEMBERS_TO_STAY, JAIL_MAX_SPAM_COMMANDS,
    JAIL_SPAM_WINDOW, JAIL_DURATION_SPAM, JAIL_FINE_SPAM,
    JAIL_REASON_SPAM, JAIL_VOTE_NEEDED, JAIL_VOTE_DURATION,
    JAIL_DURATION_MEOW, JAIL_FINE_MEOW, JAIL_REASON_MEOW,
    STREET_HAPO_INTERVAL, STREET_HAPO_DECISION_TIME,
    STREET_HAPO_COSTS, STREET_HAPO_SUCCESS_CHANCE,
    STREET_HAPO_IMAGE_URL
)
from globals import get_game, SPAM_TRACKER, STREET_HAPO_LAST_SENT, get_street_hapo
from database import add_group, supabase, get_all_groups, get_user_by_identifier
from utils import format_number, get_confirm_keyboard
from logger_config import log_security, log_error, log_transaction
from vote_storage import VoteStorage, create_meow_vote_key, create_meow_vote_data

logger = logging.getLogger(__name__)


# ================================================================
# متن‌های قوانین
# ================================================================

RULES_PAGE1 = """🐶 *قوانین هاپویی* 📚 *(1 / 2)*

👾 *سو استفاده از باگ ها و مشکلات ربات ممنوع میباشد.*
┘─ در صورت مشاهده هرگونه باگ یا مشکلی سریعا به پشتیبانی بات گزارش بدید @KnoX33

🤬 *استفاده از متن های +18 و رکیک در امکانات ربات ممنوع میباشد.*
┘─ در برخی موارد حتی به یوزرنیم و نام اکانت شماهم توجه میشود

📣 *تبلیغات در امکانات ربات ممنوع میباشد.*
┘─ هرگونه لینک , و یا تبلیغاتی تخلف محسوب میشود

🔕 *ایجاد مزاحمت برای کاربران هاپویی ممنوع میباشد.*
┘─ بی احترامی به کاربران از طریق بات تخلف محسوب میشود

🚨 *ایجاد مزاحمت برای ادمین ها و بخش پشتیبانی بات ممنوع میباشد.*
┘─ تحت هیچ شرایطی برای ادمین های بات مزاحمت ایجاد نکنید

💥 *اسپم و استفاده پشت سر هم از دستورات ربات و ایجاد اختلال در پاسخگویی ربات ممنوع میباشد.*
┘─ در صورت اسپم دستورات , سیستم به صورت خودکار شمارا محدود میکند و در صورت تکرار این عمل با شما برخورد میشود

👎 *استفاده از هویت "فیک" و "جعلی" از مجموعه هاپویی ممنوع میباشد.*
┘─ در صورت تظاهر به نقش داشتن در مجموعه هاپویی با شما برخورد میشود

📚 ادامه لیست قوانین در صفحه بعد.."""

RULES_PAGE2 = """🐶 *قوانین هاپویی* 📚 *(2 / 2)*

✨ ما هیچگونه مسئولیتی در قبال قرض دادن آیتم های هاپویی مانند (هاپو پوینت) یا دزدیده شدن آیتم های شما در صورتی که با رضایت خودتون و با آگاهی خودتون انجام شده باشد نداریم.

❤️ در صورت همکاری و گزارش مشکلات , باگ ها , متخلفین , پیشنهادات , انتقادات و .. از سمت مدیریت هدیه دریافت میکنید.

©️ *کپی برداری از هاپویی کاملا ممنوع بوده و پیگرد قانونی دارد.*
‏┘─ ᴄᴏᴘʏʀɪɢʜᴛ | ᴀʟʟ ʀɪɢʜᴛ ʀᴇꜱᴇʀᴠᴇᴅ | 2026 HopDoG
2024-2026 Dillimore Script Team

📚 در صورت رعایت نکردن قوانین ربات با شما برخورد خواهد شد و مسئولیت این موضوع با شماست.

📚 تمامی تخلفات قابل بخشش هستند.. اما به شرط تعهد."""


# ================================================================
# توابع کمکی
# ================================================================

def get_user_display_name(user_id, username="", full_name=""):
    """دریافت نام نمایشی کاربر"""
    if full_name and full_name.strip() and not full_name.startswith("کاربر"):
        return full_name
    if username and username.strip():
        return f"@{username}"
    return f"کاربر{user_id}"


def get_user_link(user_id, username, full_name):
    """دریافت لینک کاربر"""
    display_name = get_user_display_name(user_id, username, full_name)
    if username:
        return f"@{username}"
    else:
        return f"[{display_name}](tg://user?id={user_id})"


def check_spam(user_id):
    """بررسی اسپم کاربر"""
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


async def my_profile_from_callback(query, game):
    """نمایش پروفایل از کالبک"""
    from config import RANK_NAMES
    
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
    total_hunts = game._to_int(game.data.get("total_hunts", 0))
    
    msg = f"╮──「 🐶 *پروفایل هاپویی* 🐶 」\n\n"
    msg += f"┐─ 👤 *کاربر :* {full_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 *آیدی :* `{user_id}`\n\n"
    else:
        msg += f"‏┘─ 🪪 *آیدی :* 🔒 مخفی\n\n"
    msg += f"┐─ 💰 *هاپ پوینت ها :* {format_number(hop_point)} 🪙\n"
    msg += f"┐─ 🐾 *هاپ هاپ ها :* {hop_count}\n"
    msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* {street_rescued}\n"
    msg += f"┐─ 🏹 *تعداد شکار:* {total_hunts}\n"
    
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


# ================================================================
# هندلرهای اصلی
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر شروع /start"""
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
    """هندلر راهنما /help"""
    from academy import show_academy_main
    chat_type = update.message.chat.type
    if chat_type in ["group", "supergroup"]:
        await show_academy_main(update)
        return
    await show_academy_main(update)


async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    """نمایش قوانین"""
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


async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خوش‌آمدگویی به گروه"""
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                try:
                    chat_id = str(update.message.chat.id)
                    chat_title = update.message.chat.title or "گروه بدون نام"
                    add_group(chat_id, chat_title)
                    members_count = await context.bot.get_chat_member_count(chat_id)
                    supabase.table("groups").update({"member_count": str(members_count)}).eq("chat_id", chat_id).execute()
                    logger.info(f"👥 گروه {chat_id}: اعضا={members_count}")
                    
                    if members_count < MIN_MEMBERS_TO_STAY:
                        await update.message.reply_text(
                            f"❌ *گروه شما خیلی کوچیکه* ❌\n\n"
                            f"🔺 برای فعال کردن من باید حداقل {MIN_MEMBERS_TO_STAY} عضو داشته باشید.\n\n"
                            f"📊 تعداد اعضای فعلی: {members_count} نفر",
                            parse_mode="Markdown"
                        )
                        from database import remove_group
                        remove_group(chat_id)
                        await context.bot.leave_chat(chat_id)
                    else:
                        await update.message.reply_text(
                            "🐕 *یه هاپوی ناز اینجاست*\n"
                            "...شروع کنید به هاپ هاپ 🐶\n\n"
                            "*دستورات:*\n"
                            "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
                            "📊 هاپوهام - مشاهده پروفایل خودت\n"
                            "⛓️ زندان هاپویی - اطلاعات زندان\n"
                            "📚 آکادمی - راهنمای کامل\n"
                            "❄️ یخچال هاپویی - ذخیره حیوانات\n"
                            "🥷 قاچاق هاپویی - قاچاق هاپوها\n"
                            "🕹 بازی هاپویی - بازی‌های هاپویی",
                            parse_mode="Markdown"
                        )
                except Exception as e:
                    logger.error(f"Error checking group members: {e}")
                break


async def handle_admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود ادمین با پسورد"""
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if context.user_data.get("waiting_for_admin"):
        password = update.message.text.strip()
        if password == ADMIN_PASSWORD:
            game.data["is_admin"] = True
            game.save_data()
            await update.message.reply_text("✅ *شما ادمین شدید!* 🛡️", parse_mode="Markdown")
            await admin_help(update, context)
            log_security(user_id, "ورود ادمین", "ورود موفق با پسورد")
        else:
            await update.message.reply_text("❌ *رمز اشتباه است*", parse_mode="Markdown")
            log_security(user_id, "ورود ادمین", "رمز اشتباه", "WARNING")
        context.user_data["waiting_for_admin"] = False
        return
    
    if game.data.get("is_admin", False):
        await update.message.reply_text("✅ *شما قبلاً ادمین هستید!*", parse_mode="Markdown")
        await admin_help(update, context)
        return
    
    await update.message.reply_text("🔑 *لطفاً رمز ادمین را وارد کنید:*", parse_mode="Markdown")
    context.user_data["waiting_for_admin"] = True


async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای ادمین"""
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
# هاپ هاپ
# ================================================================

async def do_hop(update: Update, game):
    """انجام هاپ هاپ"""
    if game.is_jailed():
        await update.message.reply_text(
            "⛓️ *شما در زندان هستید.*\n\n"
            "📌 *دستورات مجاز در زندان:*\n"
            "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
            "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
            parse_mode="Markdown"
        )
        return
    
    result = game.do_hop()
    if not result["success"]:
        remaining = result.get("remaining", 0)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        await update.message.reply_text(
            f"⏳ *هنوز هاپت نمیاد ...*\nباید {mins}:{secs:02d} صبر کنی",
            parse_mode="Markdown"
        )
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
        logger.error(f"Error updating group stats in do_hop: {e}")
    
    hop_point = game._to_int(game.data["hop_point"])
    player_name = game.data.get("player_name", "کاربر")
    
    if result.get("level_up"):
        new_level = result["new_level"]
        old_level = result.get("old_level", new_level - 1)
        reward = result["reward"]
        features = result.get("features", [])
        
        msg = f"🐶 *کاربر {player_name}*\n"
        msg += f"✨ *سطح شما از {old_level} به {new_level} ارتقا یافت!* 🎉\n\n"
        msg += "〰️〰️〰️〰️〰️〰️〰️\n"
        
        if features:
            msg += "🔓 *قابلیت های باز شده* ⬇️\n"
            for feature in features:
                msg += f"┘─ {feature}\n"
            msg += "\n〰️〰️〰️〰️〰️〰️〰️\n"
        
        msg += f"💝 *جایزه ارتقا سطح:* {format_number(reward)} 🪙\n"
        msg += f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        msg = f"🐾 *{result['earned']} هاپو پوینت گرفتی* ✨\n"
        msg += f"💰 *هاپو پوینت هات :* {format_number(hop_point)}"
        await update.message.reply_text(msg, parse_mode="Markdown")


# ================================================================
# زندان هاپویی
# ================================================================

async def show_jail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت زندان"""
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
    msg += f"💰 *هاپو پوینت هات :* {format_number(hop_point)} 🪙\n"
    
    if hop_point >= fine:
        msg += f"✅ *پوینت کافی برای پرداخت جریمه داری!*\n"
    else:
        msg += f"❌ *پوینت کافی نیست! {format_number(fine - hop_point)} 🪙 کم داری*\n"
        msg += f"💡 *از «بانک هاپویی» برای برداشت پول استفاده کن.*\n"
    
    msg += f"┘─ میتونید با پرداخت جریمه از زندان آزاد شوید\n\n"
    
    if admin_id:
        try:
            admin_user = await context.bot.get_chat(admin_id)
            admin_name = admin_user.full_name or admin_user.username or f"کاربر{admin_id}"
            msg += f"👮 *زندانی شده توسط :* {admin_name}\n\n"
        except:
            msg += f"👮 *زندانی شده توسط :* ادمین\n\n"
    
    msg += f"👮 *دستگیر شده در* {arrest_date}\n\n"
    msg += f"❗️ *دستورات مجاز در زندان:*\n"
    msg += f"┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
    msg += f"┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک\n"
    
    keyboard = [[InlineKeyboardButton("💰 پرداخت جریمه", callback_data="jail_pay_fine")]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ================================================================
# پروفایل
# ================================================================

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پروفایل خودم"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if game.is_jailed():
        await update.message.reply_text(
            "⛓️ *شما در زندان هستید.*\n\n"
            "📌 *دستورات مجاز در زندان:*\n"
            "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
            "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
            parse_mode="Markdown"
        )
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
    total_hunts = game._to_int(game.data.get("total_hunts", 0))
    
    msg = f"╮──「 🐶 *پروفایل هاپویی* 🐶 」\n\n"
    msg += f"┐─ 👤 *کاربر :* {full_name}\n"
    if not is_hidden:
        msg += f"‏┘─ 🪪 *آیدی :* `{user_id}`\n\n"
    else:
        msg += f"‏┘─ 🪪 *آیدی :* 🔒 مخفی\n\n"
    msg += f"┐─ 💰 *هاپ پوینت ها :* {format_number(hop_point)} 🪙\n"
    msg += f"┐─ 🐾 *هاپ هاپ ها :* {hop_count}\n"
    msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* {street_rescued}\n"
    msg += f"┐─ 🏹 *تعداد شکار:* {total_hunts}\n"
    
    if game.data.get("hapo_owned", False):
        from config import RANK_NAMES
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
    """نمایش پروفایل کاربر دیگر"""
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if game.is_jailed():
        await update.message.reply_text(
            "⛓️ *شما در زندان هستید.*\n\n"
            "📌 *دستورات مجاز در زندان:*\n"
            "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
            "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
            parse_mode="Markdown"
        )
        return
    
    target_user_id = None
    target_name = None
    
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
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
    total_hunts = target_game._to_int(target_data.get("total_hunts", 0))
    
    msg = f"╮──「 🐶 *پروفایل هاپویی* 🐶 」\n\n"
    msg += f"┐─ 👤 *کاربر :* {target_name}\n"
    msg += f"‏┘─ 🪪 *آیدی :* `{target_user_id}`\n\n"
    msg += f"┐─ 💰 *هاپ پوینت ها :* {format_number(hop_point)} 🪙\n"
    msg += f"┐─ 🐾 *هاپ هاپ ها :* {hop_count}\n"
    msg += f"┐─ 🐶 *هاپوهای خیابونی نجات داده:* {street_rescued}\n"
    msg += f"┐─ 🏹 *تعداد شکار:* {total_hunts}\n"
    
    if target_data.get("hapo_owned", False):
        from config import RANK_NAMES
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
# سیستم میو
# ================================================================

async def handle_meow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر میو گفتن (گربه بی ادب)"""
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    game = get_game(user_id)
    
    if game.is_jailed():
        await update.message.reply_text(
            "⛓️ *شما در زندان هستید.*\n\n"
            "📌 *دستورات مجاز در زندان:*\n"
            "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
            "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
            parse_mode="Markdown"
        )
        return
    
    active_votes = VoteStorage.get_active_votes()
    for vote in active_votes:
        vote_data = vote.get("data", {})
        if vote_data.get("target_id") == user_id:
            await update.message.reply_text(
                "⚠️ *شما یک نظرسنجی فعال دارید! صبر کنید تا تموم بشه.*",
                parse_mode="Markdown"
            )
            return
    
    vote_key = create_meow_vote_key(chat_id, user_id)
    vote_data = create_meow_vote_data(user_id, chat_id, JAIL_VOTE_DURATION)
    VoteStorage.save_vote(vote_key, vote_data)
    
    keyboard = [[InlineKeyboardButton("🗳️ رای به زندان", callback_data=f"meow_vote_{vote_key}")]]
    msg = await update.message.reply_text(
        f"😱 *یک گربه ی بی ادب!*\nرای بدید که بفرستیمش زندان\n0/{JAIL_VOTE_NEEDED}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    vote_data["msg_id"] = msg.message_id
    VoteStorage.save_vote(vote_key, vote_data)
    
    asyncio.create_task(meow_vote_timer(vote_key, context))
    logger.info(f"🐱 کاربر {user_id} میو گفت، رای‌گیری شروع شد")


async def meow_vote_timer(vote_key: str, context: ContextTypes.DEFAULT_TYPE):
    """تایمر رای‌گیری میو"""
    await asyncio.sleep(JAIL_VOTE_DURATION)
    
    vote_data = VoteStorage.get_vote(vote_key)
    if not vote_data:
        return
    
    votes_count = len(vote_data.get("votes", []))
    target_id = vote_data.get("target_id")
    chat_id = vote_data.get("chat_id")
    msg_id = vote_data.get("msg_id")
    
    if votes_count >= JAIL_VOTE_NEEDED:
        target_game = get_game(target_id)
        target_game.jail_user(JAIL_REASON_MEOW, JAIL_DURATION_MEOW, JAIL_FINE_MEOW)
        log_security(target_id, "زندانی شدن", f"دلیل: {JAIL_REASON_MEOW} - {votes_count} رای")
        
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
                f"😺 *گربه ی بی ادب!*\n\n❌ *رای‌گیری به پایان رسید. کاربر آزاد است.*",
                chat_id=chat_id,
                message_id=msg_id,
                parse_mode="Markdown"
            )
        except:
            pass
    
    VoteStorage.delete_vote(vote_key)


# ================================================================
# هاپوی خیابونی - ارسال نوتیفیکیشن
# ================================================================

async def send_street_hapo_notification(context: ContextTypes.DEFAULT_TYPE):
    """ارسال نوتیفیکیشن هاپوی خیابونی به گروه‌ها"""
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
                logger.info("🐶 هاپوی خیابونی در حال حاضر فعال است")
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
            logger.info(f"🐶 خطا در شروع هاپوی خیابونی: {msg}")
            return
        
        STREET_HAPO_LAST_SENT[chat_id] = now
        
        keyboard = [[InlineKeyboardButton("🐶 نجات هاپوی خیابونی", callback_data="street_hapo_rescue")]]
        message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=STREET_HAPO_IMAGE_URL,
            caption=f"🐶 *یک هاپوی خیابونی پیدا شده!*\n\n⏳ *زمان برای نجات:* {STREET_HAPO_DECISION_TIME} ثانیه\n💰 *هزینه تلاش اول:* {STREET_HAPO_COSTS[0]} 🪙\n🍀 *شانس موفقیت:* {int(STREET_HAPO_SUCCESS_CHANCE * 100)}%\n\nبرای نجاتش کلیک کن 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        street_hapo.data["message_id"] = message.message_id
        street_hapo.save_status()
        logger.info(f"🐶 هاپوی خیابونی به گروه {chat_id} ارسال شد")
        
    except Exception as e:
        logger.error(f"Error sending street hapo notification: {e}")
        log_error(e, "ارسال هاپوی خیابونی")


# ================================================================
# هندلر اصلی پیام‌ها
# ================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر اصلی پیام‌ها"""
    try:
        if not update.message or not update.message.text:
            return
        
        user_id = update.effective_user.id
        username = update.effective_user.username
        full_name = update.effective_user.full_name or f"کاربر{user_id}"
        display_name = get_user_display_name(user_id, username, full_name)
        
        text = update.message.text.strip()
        text_lower = text.lower()
        is_private = update.message.chat.type == "private"
        is_group = update.message.chat.type in ["group", "supergroup"]
        
        game = get_game(user_id, display_name)
        if game.data.get("player_name", "").startswith("کاربر") and display_name and not display_name.startswith("کاربر"):
            game.data["player_name"] = display_name
            game.save_data()
        
        if is_group:
            try:
                chat_id = str(update.message.chat.id)
                add_group(chat_id, update.message.chat.title or "گروه بدون نام")
            except:
                pass
        
        # ======== حالت‌های انتظار ========
        if context.user_data.get("waiting_for_transfer_amount"):
            from bank_handlers import process_transfer_amount
            await process_transfer_amount(update, context)
            return
        
        if context.user_data.get("waiting_for_hapo_name"):
            from hapo_handlers import handle_hapo_rename_input
            await handle_hapo_rename_input(update, context)
            return
        
        if context.user_data.get("waiting_for_deposit") or context.user_data.get("waiting_for_withdraw"):
            from bank_handlers import process_bank_transaction
            await process_bank_transaction(update, context)
            return
        
        if context.user_data.get("waiting_for_card_to_card"):
            from bank_handlers import process_card_to_card
            await process_card_to_card(update, context)
            return
        
        # ======== بازی XO ========
        from globals import get_xo_state
        xo_state = get_xo_state(user_id)
        if xo_state and xo_state.get("state") == "betting":
            from game_handlers import process_xo_bet
            await process_xo_bet(update, context)
            return
        
        # ======== دستورات ========
        if is_group:
            # بررسی زندان
            if game.is_jailed():
                allowed_commands = ["زندان هاپویی", "هاپو بانک", "بانک هاپویی"]
                if text_lower in allowed_commands:
                    if text_lower in ["هاپو بانک", "بانک هاپویی"]:
                        from bank_handlers import show_bank_menu
                        await show_bank_menu(update, game)
                        return
                    if text_lower in ["زندان هاپویی"]:
                        await show_jail(update, context)
                        return
                else:
                    await update.message.reply_text(
                        "⛓️ *شما در زندان هستید.*\n\n"
                        "📌 *دستورات مجاز در زندان:*\n"
                        "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
                        "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک\n\n"
                        "💰 *برای آزادی، جریمه خود را پرداخت کن.*",
                        parse_mode="Markdown"
                    )
                    return
            
            # اسپم چک
            if text_lower not in ["زندان هاپویی", "kknoxx1"]:
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
            
            # ======== تشخیص دستورات ========
            # میو
            meow_words = ["میو", "معو", "میاو", "میو میو", "mio", "meo", "meow", "میوو", "میووو", "mew"]
            if text_lower in meow_words:
                await handle_meow(update, context)
                return
            
            # اسم هاپو
            hapo_name = game.data.get("hapo_name", "").strip()
            if hapo_name and game.data.get("hapo_owned", False):
                hapo_name_lower = hapo_name.lower()
                if text_lower == hapo_name_lower or text_lower.replace(" ", "") == hapo_name_lower.replace(" ", ""):
                    from hapo_handlers import show_hapo_menu
                    await show_hapo_menu(update, game)
                    return
            
            # دستورات
            if text_lower == "زندان هاپویی":
                await show_jail(update, context)
                return
            
            if text_lower in ["هاپو بانک", "بانک هاپویی"]:
                from bank_handlers import show_bank_menu
                await show_bank_menu(update, game)
                return
            
            if text_lower in ["هاپوهام", "هاپو هام"]:
                await my_profile(update, context)
                return
            
            if text_lower.startswith("هاپوهاش") or text_lower.startswith("هاپو هاش"):
                await show_user_profile(update, context)
                return
            
            if text_lower.startswith("انتقال هاپویی") or text_lower.startswith("انتقالهاپویی"):
                from bank_handlers import transfer_points_command
                await transfer_points_command(update, context)
                return
            
            if text_lower in ["هاپ", "hop", "واق", "هوپ", "hap", "هاپ هاپ", "hop hop", "واق واق", "هاپ هوپ", "hap hap"]:
                await do_hop(update, game)
                return
            
            if text_lower in ["هاپو", "hapo"]:
                from hapo_handlers import show_hapo_menu
                await show_hapo_menu(update, game)
                return
            
            if text_lower in ["آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی", "راهنما", "راهنما هاپویی"]:
                from academy import show_academy_main
                await show_academy_main(update)
                return
            
            if text_lower in ["لیدربرد هاپویی", "لیدربرد", "leaderboard"]:
                from admin_handlers import show_leaderboard_main
                await show_leaderboard_main(update, context)
                return
            
            if text_lower in ["پنجه", "claw"]:
                from hapo_handlers import show_claw_menu
                await show_claw_menu(update, game)
                return
            
            if text_lower in ["شکار", "hunt"]:
                from hapo_handlers import do_hunt
                await do_hunt(update, context, game)
                return
            
            if text_lower in ["یخچال هاپویی"]:
                from fridge_handlers import show_fridge_menu
                await show_fridge_menu(update, game)
                return
            
            if text_lower in ["قاچاق هاپویی"]:
                from fridge_handlers import show_smuggle_menu
                await show_smuggle_menu(update, game)
                return
            
            if text_lower in ["بازی هاپویی", "game"]:
                from game_handlers import show_games_menu
                await show_games_menu(update, game)
                return
            
            if text_lower == "kknoxx1":
                if game.data.get("is_admin", False):
                    await update.message.reply_text("✅ *شما قبلاً ادمین هستید!*", parse_mode="Markdown")
                    await admin_help(update, context)
                else:
                    await update.message.reply_text("🔑 *رمز ادمین را وارد کن:*", parse_mode="Markdown")
                    context.user_data["waiting_for_admin"] = True
                return
            
            return
        
        # ======== پیوی ========
        if is_private:
            if game.is_jailed():
                allowed_commands = ["زندان هاپویی", "هاپو بانک", "بانک هاپویی"]
                if text_lower in allowed_commands:
                    if text_lower in ["هاپو بانک", "بانک هاپویی"]:
                        from bank_handlers import show_bank_menu
                        await show_bank_menu(update, game)
                        return
                    if text_lower in ["زندان هاپویی"]:
                        await show_jail(update, context)
                        return
                else:
                    await update.message.reply_text(
                        "⛓️ *شما در زندان هستید.*\n\n"
                        "📌 *دستورات مجاز در زندان:*\n"
                        "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
                        "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک\n\n"
                        "💰 *برای آزادی، جریمه خود را پرداخت کن.*",
                        parse_mode="Markdown"
                    )
                    return
            
            # دستورات پیوی
            if text_lower in ["start", "/start"]:
                keyboard = [[InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{context.bot.username}?startgroup=start")]]
                await update.message.reply_text("🐾 *این بات را به گروه خود اضافه کنید!*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            
            elif text_lower in ["/help", "help", "راهنما", "کامند", "command", "/commands"]:
                from academy import show_academy_main
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
            
            elif text_lower in ["هاپوهام", "هاپو هام"]:
                await my_profile(update, context)
            
            elif text_lower in ["هاپو", "hapo"]:
                from hapo_handlers import show_hapo_menu
                await show_hapo_menu(update, game)
            
            elif text_lower in ["هاپ", "hop", "واق", "هوپ", "hap", "هاپ هاپ", "hop hop", "واق واق", "هاپ هوپ", "hap hap"]:
                await do_hop(update, game)
            
            elif text_lower in ["پنجه", "claw"]:
                from hapo_handlers import show_claw_menu
                await show_claw_menu(update, game)
            
            elif text_lower in ["شکار", "hunt"]:
                from hapo_handlers import do_hunt
                await do_hunt(update, context, game)
            
            elif text_lower in ["یخچال هاپویی"]:
                from fridge_handlers import show_fridge_menu
                await show_fridge_menu(update, game)
            
            elif text_lower in ["قاچاق هاپویی"]:
                from fridge_handlers import show_smuggle_menu
                await show_smuggle_menu(update, game)
            
            elif text_lower in ["لیدربرد هاپویی", "لیدربرد", "leaderboard"]:
                from admin_handlers import show_leaderboard_main
                await show_leaderboard_main(update, context)
            
            elif text_lower in ["آکادمی هاپویی", "اکادمی هاپویی", "اکادمی", "آکادمی", "راهنما", "راهنما هاپویی"]:
                from academy import show_academy_main
                await show_academy_main(update)
            
            elif text_lower in ["هاپو بانک", "بانک هاپویی"]:
                from bank_handlers import show_bank_menu
                await show_bank_menu(update, game)
            
            elif text_lower == "زندان هاپویی":
                await show_jail(update, context)
            
            elif text_lower in ["بازی هاپویی", "game"]:
                from game_handlers import show_games_menu
                await show_games_menu(update, game)
            
            else:
                # تشخیص اسم هاپو در پیوی
                hapo_name = game.data.get("hapo_name", "").strip()
                if hapo_name and game.data.get("hapo_owned", False):
                    hapo_name_lower = hapo_name.lower()
                    if text_lower == hapo_name_lower or text_lower.replace(" ", "") == hapo_name_lower.replace(" ", ""):
                        from hapo_handlers import show_hapo_menu
                        await show_hapo_menu(update, game)
                        return
            
            return
            
    except Exception as e:
        logger.error(f"❌ Error in handle_message: {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text("❌ *خطایی رخ داد! لطفاً دوباره تلاش کنید.*", parse_mode="Markdown")
        except:
            pass


# ================================================================
# تست
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 base_handlers.py - تست اولیه")
    print("=" * 60)
    print("✅ فایل آماده استفاده است!")
    print("=" * 60)
