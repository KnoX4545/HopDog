# handlers.py - compatibility router for HopDog
# Re-exports old handler names so bot.py keeps working after refactor.

from core_handlers import *
from hapo_handler import *
from bank_handler import *
from profile_handler import *
from leaderboard_handler import *
from admin_handler import *
from callback_handler import *

# Backward compatibility functions moved/removed during refactor
# These prevent bot.py import crashes.

async def group_welcome(update, context):
    if update and getattr(update, "message", None):
        await update.message.reply_text("👋 خوش آمدید به HopDog")

async def send_street_hapo_notification(*args, **kwargs):
    return None

async def set_user_level(update, context):
    await update.message.reply_text("این دستور در حال انتقال به admin_handler است.")

async def add_user_level(update, context):
    await update.message.reply_text("این دستور در حال انتقال به admin_handler است.")

async def set_user_point(update, context):
    await update.message.reply_text("این دستور در حال انتقال به admin_handler است.")

async def add_user_point(update, context):
    await update.message.reply_text("این دستور در حال انتقال به admin_handler است.")

async def get_user_info(update, context):
    await update.message.reply_text("اطلاعات کاربر در حال آماده‌سازی است.")

async def list_groups(update, context):
    await update.message.reply_text("لیست گروه‌ها.")

