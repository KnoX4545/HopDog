# bot.py - فایل اصلی (نسخه کامل با اصلاحات نهایی)

import logging
import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import TOKEN, STREET_HAPO_INTERVAL, USE_WEBHOOK, WEBHOOK_PORT, WEBHOOK_URL, ADMIN_PASSWORD
from globals import get_game
from utils import parse_amount

from handlers import (
    start, help_command, handle_message, handle_callback, group_welcome,
    set_user_level, add_user_level, set_user_point, add_user_point, get_user_info,
    jail_user_command, send_street_hapo_notification, admin_street_hapo,
    list_groups, reset_user_command,
    admin_set_street_hapo, admin_add_street_hapo, admin_help,
    show_rules, show_leaderboard_main, handle_admin_login
)
from game_functions import game_manager
from vote_storage import VoteStorage
from logger_config import init_logging, log_transaction, log_security, log_game, log_db, log_error, log_stats

# ================================================================
# تنظیمات اولیه لاگ
# ================================================================

# مقداردهی لاگ‌ها
root_logger, transaction_logger, security_logger, game_logger, db_logger = init_logging()
logger = root_logger

# ================================================================
# توابع پاک‌سازی خودکار
# ================================================================

async def cleanup_games(context: ContextTypes.DEFAULT_TYPE):
    """پاک‌سازی خودکار بازی‌های منقضی شده"""
    try:
        game_manager.check_timeout()
        logger.info("🧹 پاک‌سازی خودکار بازی‌ها انجام شد")
    except Exception as e:
        logger.error(f"❌ خطا در پاک‌سازی بازی‌ها: {e}")
        log_error(e, "پاک‌سازی بازی‌ها")


async def cleanup_votes(context: ContextTypes.DEFAULT_TYPE):
    """پاک‌سازی خودکار رای‌های منقضی شده"""
    try:
        count = VoteStorage.cleanup_expired()
        if count > 0:
            logger.info(f"🧹 {count} رای منقضی شده پاک شد")
    except Exception as e:
        logger.error(f"❌ خطا در پاک‌سازی رای‌ها: {e}")
        log_error(e, "پاک‌سازی رای‌ها")


async def log_system_stats(context: ContextTypes.DEFAULT_TYPE):
    """لاگ آمار سیستم هر ساعت"""
    try:
        from database import get_all_groups
        groups = get_all_groups()
        active_games = len(game_manager.games)
        active_users = len(game_manager.user_games)
        
        log_stats(active_users, active_games, len(groups))
        logger.info(f"📊 آمار: {active_users} کاربر فعال، {active_games} بازی، {len(groups)} گروه")
    except Exception as e:
        logger.error(f"❌ خطا در لاگ آمار: {e}")
        log_error(e, "آمار سیستم")


# ================================================================
# مدیریت خطاهای عمومی
# ================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت خطاهای عمومی بات"""
    try:
        if update is None:
            logger.error(f"❌ خطا (بدون update): {context.error}")
            return
        
        user_id = "نامشخص"
        if update.effective_user:
            user_id = update.effective_user.id
        
        message = None
        if update.effective_message:
            message = update.effective_message
        elif update.callback_query and update.callback_query.message:
            message = update.callback_query.message
        
        error = context.error
        logger.error(f"❌ خطا در درخواست از {user_id}: {error}")
        log_error(error, f"درخواست از {user_id}", user_id if user_id != "نامشخص" else None)
        
        if message:
            try:
                await message.reply_text(
                    "❌ *خطایی رخ داد!*\n\n"
                    "لطفاً دوباره تلاش کنید. اگر مشکل ادامه داشت، به پشتیبانی اطلاع دهید.\n\n"
                    "📱 *پشتیبانی:* @KnoX33",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"❌ خطا در ارسال پیام خطا: {e}")
                
    except Exception as e:
        logger.error(f"❌ خطا در error_handler: {e}")


# ================================================================
# تابع اصلی
# ================================================================

def main():
    logger.info("=" * 60)
    logger.info("🚀 راه‌اندازی بات هاپویی (HopDog)")
    logger.info(f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🤖 نام بات: @HopDogQ")
    logger.info("=" * 60)
    
    # ======== ایجاد اپلیکیشن ========
    app = Application.builder().token(TOKEN).build()
    
    # ================================================================
    # دستورات عمومی
    # ================================================================
    logger.info("📝 ثبت دستورات عمومی...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", show_rules))
    logger.info("✅ دستورات عمومی ثبت شدند")
    
    # ================================================================
    # دستورات ادمین (فقط پیوی)
    # ================================================================
    logger.info("📝 ثبت دستورات ادمین...")
    app.add_handler(CommandHandler("setlevel", set_user_level, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("addlevel", add_user_level, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("setpoint", set_user_point, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("addpoint", add_user_point, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("userinfo", get_user_info, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("jail", jail_user_command, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("hapo", admin_street_hapo, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("groups", list_groups, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("rest", reset_user_command, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("setstreethapo", admin_set_street_hapo, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("addstreethapo", admin_add_street_hapo, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("ahelp", admin_help, filters.ChatType.PRIVATE))
    logger.info("✅ دستورات ادمین ثبت شدند")
    
    # ================================================================
    # ورود ادمین با پسورد
    # ================================================================
    app.add_handler(MessageHandler(
        filters.Regex(r'(?i)^kknoxx1$') & filters.ChatType.PRIVATE,
        handle_admin_login
    ))
    logger.info("🔑 ورود ادمین فعال شد")
    
    # ================================================================
    # هندلر پیام‌های گروه (با اولویت بالا)
    # ================================================================
    logger.info("📝 ثبت هندلر پیام‌های گروه...")
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS,
        handle_message
    ))
    logger.info("✅ هندلر گروه ثبت شد")
    
    # ================================================================
    # هندلر پیام‌های پیوی
    # ================================================================
    logger.info("📝 ثبت هندلر پیام‌های پیوی...")
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE,
        handle_message
    ))
    logger.info("✅ هندلر پیوی ثبت شد")
    
    # ================================================================
    # هندلرهای کالبک و خوش‌آمدگویی
    # ================================================================
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    logger.info("✅ هندلرهای کالبک و خوش‌آمدگویی ثبت شدند")
    
    # ================================================================
    # هندلر خطاها
    # ================================================================
    app.add_error_handler(error_handler)
    logger.info("✅ هندلر خطاها ثبت شد")
    
    # ================================================================
    # Job Queue (کارهای زمان‌بندی شده)
    # ================================================================
    job_queue = app.job_queue
    if job_queue:
        logger.info("⏰ تنظیم Job Queue...")
        
        # ======== هاپوی خیابونی (هر ۶ ساعت) ========
        job_queue.run_repeating(
            send_street_hapo_notification, 
            interval=STREET_HAPO_INTERVAL, 
            first=10
        )
        logger.info(f"✅ هاپوی خیابونی فعال شد (هر {STREET_HAPO_INTERVAL//3600} ساعت)")
        
        # ======== پاک‌سازی بازی‌ها (هر ۳۰ ثانیه) ========
        job_queue.run_repeating(cleanup_games, interval=30, first=5)
        logger.info("✅ پاک‌سازی خودکار بازی‌ها فعال شد (هر ۳۰ ثانیه)")
        
        # ======== پاک‌سازی رای‌ها (هر ۱ ساعت) ========
        job_queue.run_repeating(cleanup_votes, interval=3600, first=10)
        logger.info("✅ پاک‌سازی خودکار رای‌ها فعال شد (هر ۱ ساعت)")
        
        # ======== لاگ آمار سیستم (هر ۱ ساعت) ========
        job_queue.run_repeating(log_system_stats, interval=3600, first=60)
        logger.info("✅ لاگ آمار سیستم فعال شد (هر ۱ ساعت)")
        
    else:
        logger.warning("⚠️ JobQueue در دسترس نیست!")
    
    # ================================================================
    # راه‌اندازی و اجرا
    # ================================================================
    logger.info("=" * 60)
    logger.info("✅ بات آماده اجرا است!")
    logger.info("=" * 60)
    
    logger.info("🔄 استفاده از Polling")
    
    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"❌ خطا در اجرای بات: {e}")
        log_error(e, "اجرای اصلی بات")
        raise


# ================================================================
# ورود اصلی
# ================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 بات توسط کاربر متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")
        import traceback
        logger.error(traceback.format_exc())
