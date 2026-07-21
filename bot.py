# bot.py - فایل اصلی با لاگ‌های کامل برای دیباگ

import logging
import os
import sys
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TOKEN, STREET_HAPO_INTERVAL, USE_WEBHOOK, WEBHOOK_PORT, WEBHOOK_URL, ADMIN_PASSWORD
from handlers import (
    start, help_command, handle_message, handle_callback, group_welcome,
    set_user_level, add_user_level, set_user_point, add_user_point, get_user_info,
    jail_user_command, send_street_hapo_notification, admin_street_hapo,
    list_groups, reset_user_command,
    admin_set_street_hapo, admin_add_street_hapo, admin_help,
    show_rules, show_leaderboard_main, get_game
)

# ================================================================
# تنظیمات لاگ
# ================================================================

# تنظیم لاگ برای نمایش در کنسول با جزئیات کامل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# لاگ‌های دقیق‌تر برای کتابخانه‌های خاص
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# لاگر جداگانه برای ربات
bot_logger = logging.getLogger("HopDog")
bot_logger.setLevel(logging.DEBUG)

# اضافه کردن هندلر فایل برای ذخیره لاگ‌ها (اختیاری)
try:
    file_handler = logging.FileHandler('hopdog.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    bot_logger.addHandler(file_handler)
except Exception as e:
    logger.warning(f"⚠️ نمی‌توان فایل لاگ ایجاد کرد: {e}")


def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE, prefix="📩"):
    """تابع کمکی برای لاگ کردن پیام‌ها"""
    if not update or not update.message:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username or "بدون یوزرنیم"
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    chat_type = update.message.chat.type
    chat_id = update.message.chat.id
    text = update.message.text or "[غیرمتنی]"
    
    bot_logger.info(f"{prefix} پیام از {full_name} (@{username}) [ID:{user_id}] در {chat_type} (chat:{chat_id}): '{text[:100]}'")


def log_error(func_name, error):
    """تابع کمکی برای لاگ کردن خطاها"""
    bot_logger.error(f"❌ خطا در {func_name}: {error}")
    import traceback
    bot_logger.error(traceback.format_exc())


# ================================================================
# تابع مدیریت ورود ادمین
# ================================================================

async def handle_admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت ورود به پنل ادمین"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "بدون یوزرنیم"
        full_name = update.effective_user.full_name or f"کاربر{user_id}"
        
        bot_logger.info(f"🔑 درخواست ورود ادمین از {full_name} (@{username}) [ID:{user_id}]")
        
        game = get_game(user_id)
        
        if context.user_data.get("waiting_for_admin"):
            password = update.message.text.strip()
            bot_logger.info(f"🔐 رمز وارد شده توسط {user_id}: {'✅ درست' if password == ADMIN_PASSWORD else '❌ اشتباه'}")
            
            if password == ADMIN_PASSWORD:
                game.data["is_admin"] = True
                game.save_data()
                bot_logger.info(f"✅ کاربر {user_id} ادمین شد!")
                await update.message.reply_text("✅ *شما ادمین شدید!* 🛡️", parse_mode="Markdown")
                await admin_help(update, context)
            else:
                bot_logger.warning(f"⚠️ رمز اشتباه از {user_id}")
                await update.message.reply_text("❌ *رمز اشتباه است*", parse_mode="Markdown")
            context.user_data["waiting_for_admin"] = False
            return
        
        if game.data.get("is_admin", False):
            bot_logger.info(f"✅ کاربر {user_id} قبلاً ادمین است")
            await update.message.reply_text("✅ *شما قبلاً ادمین هستید!*", parse_mode="Markdown")
            await admin_help(update, context)
            return
        
        bot_logger.info(f"🔑 درخواست رمز ادمین از {user_id}")
        await update.message.reply_text("🔑 *لطفاً رمز ادمین را وارد کنید:*", parse_mode="Markdown")
        context.user_data["waiting_for_admin"] = True
        
    except Exception as e:
        log_error("handle_admin_login", e)
        await update.message.reply_text("❌ *خطا در ورود به پنل ادمین*", parse_mode="Markdown")


# ================================================================
# تابع اصلی
# ================================================================

def main():
    try:
        bot_logger.info("=" * 60)
        bot_logger.info("🚀 شروع راه‌اندازی بات HopDog")
        bot_logger.info(f"📅 زمان شروع: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        bot_logger.info("=" * 60)
        
        # چک کردن توکن
        if not TOKEN:
            bot_logger.error("❌ TOKEN تعریف نشده است!")
            sys.exit(1)
        
        bot_logger.info(f"🔑 توکن بات: {TOKEN[:10]}... (مخفی)")
        
        # drop_pending_updates=True برای جلوگیری از Conflict
        bot_logger.info("📡 ایجاد اپلیکیشن بات...")
        app = Application.builder().token(TOKEN).build()
        bot_logger.info("✅ اپلیکیشن ساخته شد")
        
        # ============================================================
        # دستورات عمومی (همه جا)
        # ============================================================
        bot_logger.info("📝 ثبت هندلرهای عمومی...")
        app.add_handler(CommandHandler("start", start))
        bot_logger.info("  ✅ /start")
        app.add_handler(CommandHandler("help", help_command))
        bot_logger.info("  ✅ /help")
        app.add_handler(CommandHandler("rules", show_rules))
        bot_logger.info("  ✅ /rules")
        
        # ============================================================
        # دستورات ادمین (فقط پیوی)
        # ============================================================
        bot_logger.info("📝 ثبت هندلرهای ادمین...")
        app.add_handler(CommandHandler("setlevel", set_user_level, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /setlevel")
        app.add_handler(CommandHandler("addlevel", add_user_level, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /addlevel")
        app.add_handler(CommandHandler("setpoint", set_user_point, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /setpoint")
        app.add_handler(CommandHandler("addpoint", add_user_point, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /addpoint")
        app.add_handler(CommandHandler("userinfo", get_user_info, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /userinfo")
        app.add_handler(CommandHandler("jail", jail_user_command, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /jail")
        app.add_handler(CommandHandler("hapo", admin_street_hapo, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /hapo")
        app.add_handler(CommandHandler("groups", list_groups, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /groups")
        app.add_handler(CommandHandler("rest", reset_user_command, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /rest")
        app.add_handler(CommandHandler("setstreethapo", admin_set_street_hapo, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /setstreethapo")
        app.add_handler(CommandHandler("addstreethapo", admin_add_street_hapo, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /addstreethapo")
        app.add_handler(CommandHandler("ahelp", admin_help, filters.ChatType.PRIVATE))
        bot_logger.info("  ✅ /ahelp")
        
        # ============================================================
        # ورود ادمین با kknoxx1 (فقط پیوی)
        # ============================================================
        bot_logger.info("📝 ثبت هندلر ورود ادمین...")
        app.add_handler(MessageHandler(
            filters.Regex(r'(?i)^kknoxx1$') & filters.ChatType.PRIVATE,
            handle_admin_login
        ))
        bot_logger.info("  ✅ kknoxx1")
        
        # ============================================================
        # هندلرهای پیام (همه پیام‌های متنی در گروه و پیوی)
        # ============================================================
        bot_logger.info("📝 ثبت هندلرهای پیام...")
        
        # هندلر گروه - با لاگ
        app.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.GROUP,
            handle_message
        ))
        bot_logger.info("  ✅ پیام‌های گروه")
        
        # هندلر پیوی - با لاگ
        app.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE,
            handle_message
        ))
        bot_logger.info("  ✅ پیام‌های پیوی")
        
        # ============================================================
        # هندلرهای کالبک و خوش‌آمدگویی
        # ============================================================
        bot_logger.info("📝 ثبت هندلرهای کالبک...")
        app.add_handler(CallbackQueryHandler(handle_callback))
        bot_logger.info("  ✅ CallbackQuery")
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
        bot_logger.info("  ✅ NEW_CHAT_MEMBERS")
        
        # ============================================================
        # هاپوی خیابونی
        # ============================================================
        bot_logger.info("📝 راه‌اندازی JobQueue...")
        job_queue = app.job_queue
        if job_queue:
            bot_logger.info(f"⏰ تنظیم هاپوی خیابونی هر {STREET_HAPO_INTERVAL//3600} ساعت")
            job_queue.run_repeating(send_street_hapo_notification, interval=STREET_HAPO_INTERVAL, first=10)
            bot_logger.info("✅ هاپوی خیابونی: هر ۶ ساعت یکبار فعال شد")
        else:
            bot_logger.warning("⚠️ JobQueue در دسترس نیست!")
        
        # ============================================================
        # اجرا
        # ============================================================
        bot_logger.info("=" * 60)
        bot_logger.info("🚀 ربات HopDog آماده اجرا است!")
        bot_logger.info("=" * 60)
        bot_logger.info("📋 ویژگی‌های فعال:")
        bot_logger.info("  🐾 سیستم هاپ هاپ")
        bot_logger.info("  ⛓️ سیستم زندان هاپویی")
        bot_logger.info("  👥 سیستم رای‌گیری میو")
        bot_logger.info("  🐶 سیستم هاپوی خیابونی (هر ۶ ساعت)")
        bot_logger.info("  ❄️ سیستم یخچال هاپویی")
        bot_logger.info("  🥷 سیستم قاچاق هاپویی")
        bot_logger.info("  🏆 سیستم لیدربرد هاپویی")
        bot_logger.info("  🏦 سیستم بانک هاپویی")
        bot_logger.info("  🐕 سیستم هاپو")
        bot_logger.info("  🦞 سیستم پنجه و شکار")
        bot_logger.info("=" * 60)
        
        # انتخاب روش اجرا
        if USE_WEBHOOK and WEBHOOK_URL:
            bot_logger.info(f"🌐 استفاده از Webhook: {WEBHOOK_URL}")
            bot_logger.info(f"🌐 پورت: {WEBHOOK_PORT}")
            bot_logger.info("🔄 شروع Webhook...")
            app.run_webhook(
                listen="0.0.0.0",
                port=WEBHOOK_PORT,
                webhook_url=f"{WEBHOOK_URL}/webhook",
                allowed_updates=Update.ALL_TYPES
            )
        else:
            bot_logger.info("🔄 استفاده از Polling")
            bot_logger.info("🔄 شروع Polling...")
            app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
    except Exception as e:
        bot_logger.error(f"❌ خطای fatal در main(): {e}")
        import traceback
        bot_logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    try:
        bot_logger.info("=" * 60)
        bot_logger.info(f"🐕 HopDog Bot v2.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        bot_logger.info("=" * 60)
        main()
    except KeyboardInterrupt:
        bot_logger.info("⏹️ ربات با Ctrl+C متوقف شد")
        sys.exit(0)
    except Exception as e:
        bot_logger.error(f"❌ خطا در اجرای اصلی: {e}")
        import traceback
        bot_logger.error(traceback.format_exc())
        sys.exit(1)
