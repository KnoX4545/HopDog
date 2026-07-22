# handlers.py - فایل اصلی (کوتاه شده)

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_PASSWORD
from handlers_common import get_game, get_street_hapo, GAME_XO_STATE
from game_handlers import (
    show_games_menu, show_xo_main, handle_xo_set_bet, 
    process_xo_bet, handle_xo_create, handle_xo_join,
    handle_xo_move, handle_xo_close, handle_xo_cancel
)
from claw_handlers import show_claw_menu, handle_buy_claw, handle_upgrade_claw
from street_handlers import handle_street_hapo_rescue

# ... بقیه importها از academy, bank, database و ...

logger = logging.getLogger(__name__)

# ================================================================
# توابع کمکی
# ================================================================

def get_confirm_keyboard(yes, no):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ بله", callback_data=yes),
         InlineKeyboardButton("❌ نه", callback_data=no)]
    ])


# ================================================================
# هندلر اصلی Callback
# ================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        game = get_game(user_id)
        data = query.data
        
        # ======== بازی XO ========
        if data == "game_xo_main":
            await show_xo_main(update, query, game)
            return
        if data == "game_xo_set_bet":
            await handle_xo_set_bet(update, context)
            return
        if data.startswith("game-xo-create-"):
            bet_amount = int(data.replace("game-xo-create-", ""))
            await handle_xo_create(update, context, bet_amount)
            return
        if data.startswith("game-xo-join-"):
            game_id = data.replace("game-xo-join-", "")
            await handle_xo_join(update, context, game_id)
            return
        if data.startswith("xo-move-"):
            parts = data.split("-")
            if len(parts) >= 5:
                game_id_parts = parts[2:-2]
                game_id = "-".join(game_id_parts)
                row = int(parts[-2])
                col = int(parts[-1])
                await handle_xo_move(update, context, game_id, row, col)
            return
        if data.startswith("xo-close-"):
            game_id = data.replace("xo-close-", "")
            await handle_xo_close(update, context, game_id)
            return
        if data.startswith("xo-cancel-"):
            game_id = data.replace("xo-cancel-", "")
            await handle_xo_cancel(update, context, game_id)
            return
        if data == "xo_no_move":
            return
        
        # ======== پنجه ========
        if data == "buy_claw":
            await handle_buy_claw(update, context, query)
            return
        if data == "upgrade_claw":
            await handle_upgrade_claw(update, context, query)
            return
        
        # ======== هاپوی خیابونی ========
        if data == "street_hapo_rescue":
            await handle_street_hapo_rescue(update, context, query)
            return
        
        # ======== بقیه بخش‌ها (آکادمی، بانک، هاپو، ...) ========
        # ... ادامه کدهای قبلی برای آکادمی، بانک، هاپو و ...
        
    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")


# ================================================================
# هندلر اصلی پیام‌ها
# ================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... کدهای قبلی handle_message ...
    # فقط بخش بازی رو اینجا اضافه کنید:
    
    if text_clean in ["بازی هاپویی", "بازی", "game"]:
        await show_games_menu(update, game)
        return
    
    if text_clean in ["پنجه", "claw"]:
        await show_claw_menu(update, game)
        return
