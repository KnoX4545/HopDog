# bot.py - فایل اصلی (نسخه کامل با اصلاح ذخیره‌سازی یخچال)

import logging
import os
import asyncio
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import TOKEN, STREET_HAPO_INTERVAL, ADMIN_PASSWORD
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
from database import supabase

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
    """پاک‌سازی خودکار بازی‌های منقضی شده (هر ۱۰ ثانیه)"""
    try:
        game_manager.check_timeout()
        logger.info("🧹 پاک‌سازی خودکار بازی‌ها انجام شد")
    except Exception as e:
        logger.error(f"❌ خطا در پاک‌سازی بازی‌ها: {e}")
        log_error(e, "پاک‌سازی بازی‌ها")


async def cleanup_votes(context: ContextTypes.DEFAULT_TYPE):
    """پاک‌سازی خودکار رای‌های منقضی شده (هر ۳۰ ثانیه)"""
    try:
        count = VoteStorage.cleanup_expired()
        if count > 0:
            logger.info(f"🧹 {count} رای منقضی شده پاک شد")
    except Exception as e:
        logger.error(f"❌ خطا در پاک‌سازی رای‌ها: {e}")
        log_error(e, "پاک‌سازی رای‌ها")


async def cleanup_user_cache(context: ContextTypes.DEFAULT_TYPE):
    """پاک‌سازی خودکار کش کاربران منقضی شده (هر ۵ دقیقه)"""
    try:
        from globals import user_games, USER_CACHE_TIMESTAMPS, USER_CACHE_TTL
        import time
        
        now = time.time()
        expired_users = []
        
        for user_id, timestamp in USER_CACHE_TIMESTAMPS.items():
            if now - timestamp > USER_CACHE_TTL:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            if user_id in user_games:
                del user_games[user_id]
            if user_id in USER_CACHE_TIMESTAMPS:
                del USER_CACHE_TIMESTAMPS[user_id]
        
        if expired_users:
            logger.info(f"🧹 {len(expired_users)} کش کاربر منقضی شده پاک شد")
            
    except Exception as e:
        logger.error(f"❌ خطا در پاک‌سازی کش کاربران: {e}")
        log_error(e, "پاک‌سازی کش کاربران")


# ================================================================
# ✅ بازیابی و بررسی وضعیت یخچال (نسخه کامل)
# ================================================================

async def restore_fridge_cooking(context: ContextTypes.DEFAULT_TYPE):
    """بازیابی و بررسی وضعیت پخت حیوانات در یخچال هنگام راه‌اندازی بات"""
    try:
        import json
        from datetime import datetime
        
        logger.info("♻️ شروع بررسی وضعیت یخچال کاربران...")
        
        # دریافت همه کاربرانی که یخچال دارند
        response = supabase.table("users").select("user_id, fridge_items").eq("fridge_owned", True).execute()
        
        if not response.data:
            logger.info("ℹ️ هیچ کاربری با یخچال پیدا نشد")
            return
        
        restored_count = 0
        updated_users = []
        
        for user_data in response.data:
            user_id = user_data.get("user_id")
            fridge_items = user_data.get("fridge_items", [])
            
            # ======== تبدیل JSON به لیست ========
            if isinstance(fridge_items, str):
                try:
                    fridge_items = json.loads(fridge_items)
                except:
                    fridge_items = []
            
            if not isinstance(fridge_items, list):
                fridge_items = []
            
            changed = False
            now = datetime.now().timestamp()
            
            # ======== بررسی هر آیتم ========
            for item in fridge_items:
                # اگر در حال پخت است
                if item.get("cooking", False):
                    cook_start = item.get("cook_start", 0)
                    cook_time = item.get("cook_time", 0)
                    elapsed = now - cook_start
                    
                    logger.info(f"🔍 بررسی پخت {item.get('name', 'نامشخص')} - زمان گذشته: {elapsed:.0f}s / {cook_time}s")
                    
                    # اگر پخت تمام شده
                    if elapsed >= cook_time:
                        item["cooked"] = True
                        item["cooking"] = False
                        item["original_value"] = item.get("value", 0)
                        item["original_nutrition"] = item.get("nutrition", 1)
                        item["value"] = int(item["value"] * 10)  # 10 برابر
                        item["nutrition"] = item["nutrition"] * 2  # 2 برابر
                        changed = True
                        restored_count += 1
                        logger.info(f"♻️ پخت {item.get('name', 'نامشخص')} برای کاربر {user_id} کامل شد")
            
            # اگر تغییری کرده بود، ذخیره کن
            if changed:
                updated_users.append({
                    "user_id": user_id,
                    "fridge_items": json.dumps(fridge_items, ensure_ascii=False)
                })
        
        # ======== ذخیره تغییرات در دیتابیس ========
        for user in updated_users:
            supabase.table("users").update({
                "fridge_items": user["fridge_items"]
            }).eq("user_id", user["user_id"]).execute()
            logger.info(f"💾 یخچال کاربر {user['user_id']} به‌روزرسانی شد")
        
        if restored_count > 0:
            logger.info(f"♻️ {restored_count} آیتم پخت با موفقیت بازیابی شد")
        else:
            logger.info("ℹ️ هیچ آیتم پختی برای بازیابی وجود نداشت")
            
    except Exception as e:
        logger.error(f"❌ خطا در بازیابی وضعیت پخت: {e}")
        log_error(e, "بازیابی وضعیت پخت")


async def check_all_fridges(context: ContextTypes.DEFAULT_TYPE):
    """بررسی دوره‌ای وضعیت یخچال همه کاربران (هر ۵ دقیقه)"""
    try:
        import json
        from datetime import datetime
        
        response = supabase.table("users").select("user_id, fridge_items").eq("fridge_owned", True).execute()
        
        if not response.data:
            return
        
        updated_count = 0
        now = datetime.now().timestamp()
        
        for user_data in response.data:
            user_id = user_data.get("user_id")
            fridge_items = user_data.get("fridge_items", [])
            
            if isinstance(fridge_items, str):
                try:
                    fridge_items = json.loads(fridge_items)
                except:
                    fridge_items = []
            
            if not isinstance(fridge_items, list):
                fridge_items = []
            
            changed = False
            
            for item in fridge_items:
                if item.get("cooking", False):
                    cook_start = item.get("cook_start", 0)
                    cook_time = item.get("cook_time", 0)
                    elapsed = now - cook_start
                    
                    if elapsed >= cook_time:
                        item["cooked"] = True
                        item["cooking"] = False
                        item["original_value"] = item.get("value", 0)
                        item["original_nutrition"] = item.get("nutrition", 1)
                        item["value"] = int(item["value"] * 10)
                        item["nutrition"] = item["nutrition"] * 2
                        changed = True
                        updated_count += 1
                        logger.info(f"♻️ پخت {item.get('name', 'نامشخص')} برای کاربر {user_id} کامل شد (بررسی دوره‌ای)")
            
            if changed:
                supabase.table("users").update({
                    "fridge_items": json.dumps(fridge_items, ensure_ascii=False)
                }).eq("user_id", user_id).execute()
        
        if updated_count > 0:
            logger.info(f"♻️ {updated_count} آیتم پخت در بررسی دوره‌ای کامل شد")
            
    except Exception as e:
        logger.error(f"❌ خطا در بررسی دوره‌ای یخچال‌ها: {e}")


async def log_system_stats(context: ContextTypes.DEFAULT_TYPE):
    """لاگ آمار سیستم هر ساعت"""
    try:
        from database import get_all_groups
        from globals import get_memory_stats
        
        groups = get_all_groups()
        active_games = len(game_manager.games)
        active_users = len(game_manager.user_games)
        memory_stats = get_memory_stats()
        
        log_stats(active_users, active_games, len(groups))
        logger.info(
            f"📊 آمار: {active_users} کاربر فعال، {active_games} بازی، "
            f"{len(groups)} گروه، حافظه: {memory_stats['total']} آیتم"
        )
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
        
        if "Timeout" in str(error) or "Network" in str(error):
            logger.warning(f"⚠️ خطای شبکه/تایم‌اوت برای کاربر {user_id} - پیام ارسال نشد")
            return
        
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
    # ✅ بررسی و بازیابی وضعیت یخچال هنگام راه‌اندازی
    # ================================================================
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(restore_fridge_cooking(None))
        logger.info("✅ بررسی وضعیت یخچال انجام شد")
    except Exception as e:
        logger.error(f"❌ خطا در بررسی وضعیت یخچال: {e}")
    
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
        
        # ======== پاک‌سازی بازی‌ها (هر ۱۰ ثانیه) ========
        job_queue.run_repeating(cleanup_games, interval=10, first=5)
        logger.info("✅ پاک‌سازی خودکار بازی‌ها فعال شد (هر ۱۰ ثانیه)")
        
        # ======== پاک‌سازی رای‌ها (هر ۳۰ ثانیه) ========
        job_queue.run_repeating(cleanup_votes, interval=30, first=10)
        logger.info("✅ پاک‌سازی خودکار رای‌ها فعال شد (هر ۳۰ ثانیه)")
        
        # ======== پاک‌سازی کش کاربران (هر ۵ دقیقه) ========
        job_queue.run_repeating(cleanup_user_cache, interval=300, first=60)
        logger.info("✅ پاک‌سازی خودکار کش کاربران فعال شد (هر ۵ دقیقه)")
        
        # ======== ✅ بررسی دوره‌ای یخچال‌ها (هر ۵ دقیقه) ========
        job_queue.run_repeating(check_all_fridges, interval=300, first=30)
        logger.info("✅ بررسی دوره‌ای یخچال‌ها فعال شد (هر ۵ دقیقه)")
        
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
