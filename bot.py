# bot.py - نسخه نهایی با هندلرهای درست

import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TOKEN

# فقط هندلرهای ضروری رو ایمپورت کن
from handlers import handle_message, handle_callback, start, help_command, group_welcome

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 راه‌اندازی بات...")
    
    app = Application.builder().token(TOKEN).build()
    
    # ============================================================
    # ثبت هندلرها - ترتیب مهم است!
    # ============================================================
    
    logger.info("📝 ثبت CommandHandler ها...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # ============================================================
    # هندلر گروه - این باید کار کنه!
    # ============================================================
    logger.info("📝 ثبت MessageHandler برای گروه...")
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUP,
        handle_message
    ))
    logger.info("✅ هندلر گروه ثبت شد")
    
    # ============================================================
    # هندلر پیوی
    # ============================================================
    logger.info("📝 ثبت MessageHandler برای پیوی...")
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE,
        handle_message
    ))
    logger.info("✅ هندلر پیوی ثبت شد")
    
    # ============================================================
    # هندلر کالبک
    # ============================================================
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # ============================================================
    # هندلر خوش‌آمدگویی
    # ============================================================
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    # ============================================================
    # اجرا
    # ============================================================
    logger.info("=" * 50)
    logger.info("🚀 بات آماده اجرا است!")
    logger.info("📋 هندلرهای ثبت شده:")
    logger.info("  ✅ /start")
    logger.info("  ✅ /help")
    logger.info("  ✅ پیام‌های گروه")
    logger.info("  ✅ پیام‌های پیوی")
    logger.info("  ✅ CallbackQuery")
    logger.info("  ✅ NEW_CHAT_MEMBERS")
    logger.info("=" * 50)
    
    logger.info("🔄 شروع Polling...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
