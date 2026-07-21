# bot.py - فایل اصلی (نسخه کامل با هندلرهای ادمین)

import logging
import os
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def handle_admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت ورود به پنل ادمین"""
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if context.user_data.get("waiting_for_admin"):
        password = update.message.text.strip()
        if password == ADMIN_PASSWORD:
            game.data["is_admin"] = True
            game.save_data()
            await update.message.reply_text("✅ *شما ادمین شدید!* 🛡️", parse_mode="Markdown")
            await admin_help(update, context)
        else:
            await update.message.reply_text("❌ *رمز اشتباه است*", parse_mode="Markdown")
        context.user_data["waiting_for_admin"] = False
        return
    
    if game.data.get("is_admin", False):
        await update.message.reply_text("✅ *شما قبلاً ادمین هستید!*", parse_mode="Markdown")
        await admin_help(update, context)
        return
    
    await update.message.reply_text("🔑 *لطفاً رمز ادمین را وارد کنید:*", parse_mode="Markdown")
    context.user_data["waiting_for_admin"] = True


def main():
    logger.info("🚀 راه‌اندازی بات HopDog...")
    
    app = Application.builder().token(TOKEN).build()
    
    # ============================================================
    # دستورات عمومی
    # ============================================================
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", show_rules))
    
    # ============================================================
    # ⭐⭐⭐ دستورات ادمین (باید قبل از handle_message ثبت بشن) ⭐⭐⭐
    # ============================================================
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
    
    # ============================================================
    # ورود ادمین با kknoxx1
    # ============================================================
    app.add_handler(MessageHandler(
        filters.Regex(r'(?i)^kknoxx1$') & filters.ChatType.PRIVATE,
        handle_admin_login
    ))
    
    # ============================================================
    # هندلر پیام‌های گروه
    # ============================================================
    logger.info("📝 ثبت هندلر پیام‌های گروه...")
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS,
        handle_message
    ))
    logger.info("✅ هندلر گروه ثبت شد")
    
    # ============================================================
    # هندلر پیام‌های پیوی (باید آخر باشه تا دستورات ادمین رو intercept نکنه)
    # ============================================================
    logger.info("📝 ثبت هندلر پیام‌های پیوی...")
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE,
        handle_message
    ))
    logger.info("✅ هندلر پیوی ثبت شد")
    
    # ============================================================
    # هندلرهای کالبک و خوش‌آمدگویی
    # ============================================================
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))
    
    # ============================================================
    # هاپوی خیابونی
    # ============================================================
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(send_street_hapo_notification, interval=STREET_HAPO_INTERVAL, first=10)
        logger.info("✅ هاپوی خیابونی فعال شد")
    else:
        logger.warning("⚠️ JobQueue در دسترس نیست!")
    
    # ============================================================
    # اجرا
    # ============================================================
    logger.info("=" * 50)
    logger.info("🚀 بات آماده اجرا است!")
    logger.info("=" * 50)
    
    if USE_WEBHOOK and WEBHOOK_URL:
        logger.info(f"🌐 استفاده از Webhook: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            allowed_updates=Update.ALL_TYPES
        )
    else:
        logger.info("🔄 استفاده از Polling")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


if __name__ == "__main__":
    main()
