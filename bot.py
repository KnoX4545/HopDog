# bot.py - فایل اصلی (ورودی برنامه)

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TOKEN
from handlers import (
    start, help_command, handle_message, handle_callback, group_welcome,
    set_user_level, add_user_level, set_user_point, add_user_point, get_user_info
)

logging.basicConfig(level=logging.INFO)

def main():
    app = Application.builder().token(TOKEN).build()
    
    # دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # دستورات ادمین
    app.add_handler(CommandHandler("setlevel", set_user_level))
    app.add_handler(CommandHandler("addlevel", add_user_level))
    app.add_handler(CommandHandler("setpoint", set_user_point))
    app.add_handler(CommandHandler("addpoint", add_user_point))
    app.add_handler(CommandHandler("userinfo", get_user_info))
    
    # هندلرها
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    print("🤖 بات HopDog با Supabase اجرا شد!")
    print("⛓️ سیستم زندان هاپویی فعال است!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
