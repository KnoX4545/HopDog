# street_handlers.py - هندلرهای هاپوی خیابونی

import asyncio
import logging
import random
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    STREET_HAPO_DECISION_TIME, STREET_HAPO_COSTS, STREET_HAPO_SUCCESS_CHANCE,
    STREET_HAPO_IMAGE_URL, STREET_HAPO_REWARD_MIN, STREET_HAPO_REWARD_MAX,
    STREET_HAPO_FAIL_MESSAGES, STREET_HAPO_MAX_ATTEMPTS
)
from handlers_common import get_game, get_street_hapo

logger = logging.getLogger(__name__)


async def handle_street_hapo_rescue(update, context, query):
    user_id = query.from_user.id
    game = get_game(user_id)
    
    if game.is_jailed():
        await query.answer("⛓️ شما در زندان هستید!", show_alert=True)
        return
    
    street_hapo = get_street_hapo()
    
    if not street_hapo.active:
        await query.answer("🐶 هیچ هاپوی خیابونی در دسترس نیست!", show_alert=True)
        await query.message.reply_text("🐶 *هیچ هاپوی خیابونی در دسترس نیست!*", parse_mode="Markdown")
        return
    
    if street_hapo.is_expired():
        street_hapo.active = False
        street_hapo.save_status()
        await query.answer("⏰ هاپوی خیابونی فرار کرد!", show_alert=True)
        await query.message.reply_text("⏰ *هاپوی خیابونی فرار کرد!*", parse_mode="Markdown")
        return
    
    if street_hapo.data.get("rescued", False):
        await query.answer("❌ این هاپوی خیابونی قبلاً نجات پیدا کرده!", show_alert=True)
        await query.message.reply_text("❌ *این هاپوی خیابونی قبلاً نجات پیدا کرده!*", parse_mode="Markdown")
        return
    
    attempts = street_hapo.data.get("attempts", 0)
    if attempts >= STREET_HAPO_MAX_ATTEMPTS:
        await query.answer("❌ همه شانس‌ها از دست رفته!", show_alert=True)
        await query.message.reply_text("❌ *همه شانس‌ها از دست رفته!* 😢", parse_mode="Markdown")
        return
    
    full_name = query.from_user.full_name or f"کاربر{user_id}"
    result = street_hapo.attempt_rescue(user_id, full_name, game)
    
    if result.get("success", False) and result.get("rescued", False):
        street_rescued = game._to_int(game.data.get("street_hapo_rescued", 0))
        
        msg = f"🎉 *{full_name} هاپوی خیابونی رو نجات داد!*\n\n💰 *{result['reward']} 🪙 جایزه گرفتی!*\n🐶 *تعداد نجات‌ها:* {street_rescued}\n🔄 *تلاش:* {result['attempt']}/{STREET_HAPO_MAX_ATTEMPTS}"
        
        await query.message.reply_text(msg, parse_mode="Markdown")
        
        try:
            await context.bot.send_message(user_id, f"🎉 *هاپوی خیابونی نجات داده شد!*\n💰 *{result['reward']} 🪙 واریز شد!*", parse_mode="Markdown")
        except:
            pass
        
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except:
            pass
        
    elif result.get("died", False):
        msg = f"💀 *{result['message']}*\n\n🔄 *تلاش:* {result['attempt']}/{STREET_HAPO_MAX_ATTEMPTS}"
        await query.message.reply_text(msg, parse_mode="Markdown")
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except:
            pass
        
    elif "پوینت کافی نیست" in str(result.get("reason", "")):
        await query.answer(result.get("reason", "خطا!"), show_alert=True)
        await query.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")

    elif result.get("success") is False and result.get("died") is False:
        remaining = result.get("remaining_attempts", 0)
        cost = street_hapo.get_attempt_cost()
        remaining_time = street_hapo.get_remaining_time()
        current_attempt = result.get("attempt", 0)
        
        msg = f"❌ *{result['message']}*\n\n🔄 *تلاش {current_attempt}/{STREET_HAPO_MAX_ATTEMPTS}*\n⏳ *زمان باقی‌مونده:* {remaining_time} ثانیه\n"
        keyboard = []
        if cost is not None and remaining > 0:
            keyboard.append([InlineKeyboardButton(f"🐶 تلاش مجدد ({cost} 🪙)", callback_data="street_hapo_rescue")])
            msg += f"💰 *هزینه تلاش بعدی:* {cost} 🪙"
        else:
            msg += f"❌ *همه شانس‌ها از دست رفته!*"
        
        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")

    else:
        await query.answer(result.get("reason", "خطا!"), show_alert=True)
