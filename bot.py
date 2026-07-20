# bot.py - فایل اصلی (ورودی برنامه)

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TOKEN, STREET_HAPO_INTERVAL
from handlers import (
    start, help_command, handle_message, handle_callback, group_welcome,
    set_user_level, add_user_level, set_user_point, add_user_point, get_user_info,
    jail_user_command, send_street_hapo_notification, admin_street_hapo, list_groups
)

logging.basicConfig(level=logging.INFO)

def main():
    app = Application.builder().token(TOKEN).build()
    
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
    
    # ======== هندلرهای پیام و کالبک ========
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    # ======== هاپوی خیابونی (JobQueue - هر ۶ ساعت) ========
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(send_street_hapo_notification, interval=STREET_HAPO_INTERVAL, first=10)
        logging.info("✅ هاپوی خیابونی: هر ۶ ساعت یکبار فعال شد")
    else:
        logging.warning("⚠️ JobQueue در دسترس نیست! هاپوی خیابونی فعال نخواهد شد.")
    
    # ======== شروع ربات ========
    print("🤖 بات HopDog با Supabase اجرا شد!")
    print("⛓️ سیستم زندان هاپویی فعال است!")
    print("👥 سیستم رای‌گیری میو فعال است!")
    print("🐶 سیستم هاپوی خیابونی فعال است! (هر ۶ ساعت)")
    print("📋 دستورات ادمین (فقط در پیوی):")
    print("  - /hapo [chat_id] : ارسال هاپوی خیابونی به گروه خاص")
    print("  - /groups : لیست گروه‌های ثبت شده")
    print("  - /setlevel [id] [level] : تنظیم سطح کاربر")
    print("  - /addlevel [id] [level] : اضافه کردن سطح کاربر")
    print("  - /setpoint [id] [point] : تنظیم پوینت کاربر")
    print("  - /addpoint [id] [point] : اضافه کردن پوینت کاربر")
    print("  - /userinfo [id] : اطلاعات کاربر")
    print("  - /jail [id] [minutes] [reason] : زندانی کردن کاربر")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
