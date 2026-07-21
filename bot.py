# bot.py - فایل اصلی (ورودی برنامه)

import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TOKEN, STREET_HAPO_INTERVAL, USE_WEBHOOK, WEBHOOK_PORT, WEBHOOK_URL
from handlers import (
    start, help_command, handle_message, handle_callback, group_welcome,
    set_user_level, add_user_level, set_user_point, add_user_point, get_user_info,
    jail_user_command, send_street_hapo_notification, admin_street_hapo,
    list_groups, reset_user_command,
    admin_set_street_hapo, admin_add_street_hapo
)

# ================================================================
# تنظیمات لاگ
# ================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================================================================
# تابع اصلی
# ================================================================

def main():
    # drop_pending_updates=True برای جلوگیری از Conflict
    app = Application.builder().token(TOKEN).drop_pending_updates(True).build()
    
    # ======== دستورات عمومی ========
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # ======== دستورات ادمین ========
    app.add_handler(CommandHandler("setlevel", set_user_level))
    app.add_handler(CommandHandler("addlevel", add_user_level))
    app.add_handler(CommandHandler("setpoint", set_user_point))
    app.add_handler(CommandHandler("addpoint", add_user_point))
    app.add_handler(CommandHandler("userinfo", get_user_info))
    app.add_handler(CommandHandler("jail", jail_user_command))
    
    # ======== دستورات هاپوی خیابونی (فقط ادمین - فقط پیوی) ========
    app.add_handler(CommandHandler("hapo", admin_street_hapo))
    app.add_handler(CommandHandler("groups", list_groups))
    
    # ======== دستورات ادمین برای هاپوی خیابونی ========
    app.add_handler(CommandHandler("setstreethapo", admin_set_street_hapo))
    app.add_handler(CommandHandler("addstreethapo", admin_add_street_hapo))
    
    # ======== دستور ریست کاربر (فقط ادمین - فقط پیوی) ========
    app.add_handler(CommandHandler("rest", reset_user_command))
    
    # ======== هندلرهای پیام و کالبک ========
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    # ======== هاپوی خیابونی (JobQueue - هر ۶ ساعت) ========
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(send_street_hapo_notification, interval=STREET_HAPO_INTERVAL, first=10)
        logger.info("✅ هاپوی خیابونی: هر ۶ ساعت یکبار فعال شد")
    else:
        logger.warning("⚠️ JobQueue در دسترس نیست! هاپوی خیابونی فعال نخواهد شد.")
    
    # ======== اجرای ربات ========
    logger.info("🤖 بات HopDog با Supabase اجرا شد!")
    logger.info("⛓️ سیستم زندان هاپویی فعال است!")
    logger.info("👥 سیستم رای‌گیری میو فعال است!")
    logger.info("🐶 سیستم هاپوی خیابونی فعال است! (هر ۶ ساعت)")
    logger.info("❄️ سیستم یخچال هاپویی فعال است!")
    logger.info("🥷 سیستم قاچاق هاپویی فعال است!")
    logger.info("\n📋 دستورات ادمین (فقط در پیوی):")
    logger.info("  - /hapo [chat_id] : ارسال هاپوی خیابونی به گروه خاص")
    logger.info("  - /groups : لیست گروه‌های ثبت شده")
    logger.info("  - /rest [user_id/@username] : ریست کردن کامل یک کاربر")
    logger.info("  - /setlevel [id] [level] : تنظیم سطح کاربر")
    logger.info("  - /addlevel [id] [level] : اضافه کردن سطح کاربر")
    logger.info("  - /setpoint [id] [point] : تنظیم پوینت کاربر")
    logger.info("  - /addpoint [id] [point] : اضافه کردن پوینت کاربر")
    logger.info("  - /userinfo [id] : اطلاعات کاربر")
    logger.info("  - /jail [id] [minutes] [reason] : زندانی کردن کاربر")
    logger.info("  - /setstreethapo [id] [count] : تنظیم هاپوی خیابونی کاربر")
    logger.info("  - /addstreethapo [id] [count] : اضافه کردن هاپوی خیابونی به کاربر")
    
    # ======== انتخاب روش اجرا ========
    if USE_WEBHOOK and WEBHOOK_URL:
        # استفاده از Webhook برای Railway
        logger.info(f"🌐 استفاده از Webhook: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    else:
        # استفاده از Polling
        logger.info("🔄 استفاده از Polling")
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

if __name__ == "__main__":
    main()
