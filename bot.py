# bot.py - فایل اصلی (ورودی برنامه)

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TOKEN, STREET_HAPO_INTERVAL
from handlers import (
    start, help_command, handle_message, handle_callback, group_welcome,
    set_user_level, add_user_level, set_user_point, add_user_point, get_user_info,
    jail_user_command, send_street_hapo_notification
)

logging.basicConfig(level=logging.INFO)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # دستورات ادمین
    app.add_handler(CommandHandler("setlevel", set_user_level))
    app.add_handler(CommandHandler("addlevel", add_user_level))
    app.add_handler(CommandHandler("setpoint", set_user_point))
    app.add_handler(CommandHandler("addpoint", add_user_point))
    app.add_handler(CommandHandler("userinfo", get_user_info))
    app.add_handler(CommandHandler("jail", jail_user_command))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    # ======== هاپوی خیابونی ========
    # ارسال هر ۶ ساعت
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(send_street_hapo_notification, interval=STREET_HAPO_INTERVAL, first=10)
        logging.info("✅ هاپوی خیابونی: هر ۶ ساعت یکبار فعال شد")
    
    print("🤖 بات HopDog با Supabase اجرا شد!")
    print("⛓️ سیستم زندان هاپویی فعال است!")
    print("👥 سیستم رای‌گیری میو فعال است!")
    print("🐶 سیستم هاپوی خیابونی فعال است! (هر ۶ ساعت)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
