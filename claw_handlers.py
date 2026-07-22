# claw_handlers.py - هندلرهای پنجه

import asyncio
import logging
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bank import format_number
from config import CLAW_IMAGES
from handlers_common import get_game

logger = logging.getLogger(__name__)


async def show_claw_menu(update, game):
    if game.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game._to_int(game.data["level"])
    if level < 2:
        await update.message.reply_text("🔒 *پنجه از سطح 2 باز میشود*", parse_mode="Markdown")
        return
    
    claw_level = game._to_int(game.data["claw_level"])
    
    if claw_level == 0:
        cost = game.get_claw_cost(1)
        keyboard = [[InlineKeyboardButton(f"🛒 خرید پنجه ({format_number(cost)})", callback_data="buy_claw")]]
        msg = f"🦞 *شما پنجه ندارید*\n\n💰 *هزینه خرید: {format_number(cost)} هاپو پوینت*\n⏳ *زمان استراحت: 60:00*\n🍀 *شانس شکار:*\n  ⚪ معمولی: 95%\n  🔵 کمیاب: 5%"
        
        try:
            await update.message.reply_photo(photo=CLAW_IMAGES[1], caption=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    claw_data = game.get_claw_data(claw_level)
    next_level = claw_level + 1
    next_data = game.get_claw_data(next_level)
    
    msg = f"🦞 *پنجه شما*\n⭐ *سطح:* {claw_level}\n⏳ *زمان استراحت:* {claw_data['cooldown']:02d}:00\n🍀 *شانس شکار:*\n  ⚪ معمولی: {claw_data['common']}%\n  🔵 کمیاب: {claw_data['uncommon']}%"
    
    if claw_data['epic'] > 0:
        msg += f"\n  🟣 حماسی: {claw_data['epic']}%"
    if claw_data['legendary'] > 0:
        msg += f"\n  🟡 افسانه‌ای: {claw_data['legendary']}%"
    
    keyboard = []
    if next_data:
        keyboard.append([InlineKeyboardButton(f"⬆️ سطح {next_level} ({format_number(next_data['cost'])})", callback_data="upgrade_claw")])
    
    try:
        await update.message.reply_photo(photo=CLAW_IMAGES[claw_level], caption=msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")


async def handle_buy_claw(update, context, query):
    user_id = query.from_user.id
    game = get_game(user_id)
    
    result = game.buy_claw()
    if result["success"]:
        await query.message.reply_text("✅ *پنجه خریداری شد!*", parse_mode="Markdown")
        await asyncio.sleep(1)
        
        claw_level = game._to_int(game.data["claw_level"])
        claw_data = game.get_claw_data(claw_level)
        next_level = claw_level + 1
        next_data = game.get_claw_data(next_level)
        
        msg = f"🦞 *پنجه شما*\n⭐ *سطح:* {claw_level}\n⏳ *زمان استراحت:* {claw_data['cooldown']:02d}:00\n🍀 *شانس شکار:*\n  ⚪ معمولی: {claw_data['common']}%\n  🔵 کمیاب: {claw_data['uncommon']}%"
        
        if claw_data['epic'] > 0:
            msg += f"\n  🟣 حماسی: {claw_data['epic']}%"
        if claw_data['legendary'] > 0:
            msg += f"\n  🟡 افسانه‌ای: {claw_data['legendary']}%"
        
        keyboard = []
        if next_data:
            keyboard.append([InlineKeyboardButton(f"⬆️ سطح {next_level} ({format_number(next_data['cost'])})", callback_data="upgrade_claw")])
        
        try:
            await query.message.reply_photo(photo=CLAW_IMAGES[claw_level], caption=msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
        except:
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
    else:
        await query.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_upgrade_claw(update, context, query):
    user_id = query.from_user.id
    game = get_game(user_id)
    
    result = game.upgrade_claw()
    if result["success"]:
        await query.message.reply_text(f"✅ *پنجه به سطح {result['new_level']} ارتقا یافت*", parse_mode="Markdown")
        await asyncio.sleep(1)
        
        claw_level = game._to_int(game.data["claw_level"])
        claw_data = game.get_claw_data(claw_level)
        next_level = claw_level + 1
        next_data = game.get_claw_data(next_level)
        
        msg = f"🦞 *پنجه شما*\n⭐ *سطح:* {claw_level}\n⏳ *زمان استراحت:* {claw_data['cooldown']:02d}:00\n🍀 *شانس شکار:*\n  ⚪ معمولی: {claw_data['common']}%\n  🔵 کمیاب: {claw_data['uncommon']}%"
        
        if claw_data['epic'] > 0:
            msg += f"\n  🟣 حماسی: {claw_data['epic']}%"
        if claw_data['legendary'] > 0:
            msg += f"\n  🟡 افسانه‌ای: {claw_data['legendary']}%"
        
        keyboard = []
        if next_data:
            keyboard.append([InlineKeyboardButton(f"⬆️ سطح {next_level} ({format_number(next_data['cost'])})", callback_data="upgrade_claw")])
        
        try:
            await query.message.reply_photo(photo=CLAW_IMAGES[claw_level], caption=msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
        except:
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
    else:
        await query.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
