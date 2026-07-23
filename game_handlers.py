# game_handlers.py - هندلرهای بازی هاپویی (نسخه کامل با اختصارات)

import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import GAME_REQUIRED_LEVEL, GAME_HOST_REQUIRED_LEVEL
from game_functions import game_manager, get_xo_board_keyboard, get_xo_game_text
from bank import format_number
from utils import parse_amount, get_confirm_keyboard 
from handlers import get_game

logger = logging.getLogger(__name__)

# ================================================================
# دیکشنری حالت‌های بازی
# ================================================================

GAME_XO_STATE = {}
GAME_MESSAGES = {}  # برای ذخیره message_id بازی‌ها


# ================================================================
# توابع کمکی
# ================================================================

def save_game_message(chat_id, message_id, game_id):
    """ذخیره پیام بازی برای ویرایش بعدی"""
    key = f"{chat_id}_{game_id}"
    GAME_MESSAGES[key] = message_id


def get_game_message(chat_id, game_id):
    """دریافت پیام ذخیره شده بازی"""
    key = f"{chat_id}_{game_id}"
    return GAME_MESSAGES.get(key)


def clear_game_message(chat_id, game_id):
    """پاک کردن پیام ذخیره شده بازی"""
    key = f"{chat_id}_{game_id}"
    if key in GAME_MESSAGES:
        del GAME_MESSAGES[key]


async def update_game_message(update, context, game_id: str, user_id: int):
    """به‌روزرسانی پیام بازی (همون پیام رو ویرایش کن)"""
    query = update.callback_query
    game = game_manager.get_game(game_id)
    
    if not game:
        await query.edit_message_text("❌ *بازی مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    msg = get_xo_game_text(game)
    keyboard = get_xo_board_keyboard(game, user_id)
    
    await query.edit_message_text(
        msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ================================================================
# منوی اصلی بازی‌ها
# ================================================================

async def show_games_menu(update: Update, game_obj):
    """نمایش منوی اصلی بازی‌ها - با بررسی بازی فعال"""
    user_id = int(game_obj.user_id)
    
    if game_obj.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < GAME_REQUIRED_LEVEL:
        await update.message.reply_text(f"🕹 *بازی‌های هاپویی از سطح {GAME_REQUIRED_LEVEL} باز میشود*", parse_mode="Markdown")
        return
    
    # ======== بررسی بازی فعال ========
    user_game = game_manager.get_user_game(user_id)
    if user_game:
        msg = get_xo_game_text(user_game)
        keyboard = get_xo_board_keyboard(user_game, user_id)
        
        sent_msg = await update.message.reply_text(
            msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        save_game_message(update.message.chat.id, sent_msg.message_id, user_game.game_id)
        return
    
    # ======== منوی اصلی ========
    msg = "🕹 *بازی های هاپویی* 🐶\n\n❗️ لطفا بازی مورد نظر را انتخاب کنید ⬇️\n\n🧩 بازی میویی XO\n┘─ محدودیت بازیکن : 2 هاپو"
    keyboard = [[InlineKeyboardButton("🧩 بازی XO", callback_data="game_xo_main")]]
    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ================================================================
# منوی بازی XO
# ================================================================

async def show_xo_main(update, query=None, game_obj=None):
    """نمایش منوی اصلی بازی XO - با ویرایش همون پیام"""
    if query:
        user_id = query.from_user.id
        game_obj = get_game(user_id)
        chat_id = query.message.chat.id
        message_id = query.message.message_id
    else:
        return
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < GAME_REQUIRED_LEVEL:
        await query.edit_message_text(f"🕹 *بازی XO از سطح {GAME_REQUIRED_LEVEL} باز میشود*", parse_mode="Markdown")
        return
    
    user_id = int(game_obj.user_id)
    
    user_game = game_manager.get_user_game(user_id)
    if user_game:
        msg = get_xo_game_text(user_game)
        keyboard = get_xo_board_keyboard(user_game, user_id)
        
        await query.edit_message_text(
            msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        save_game_message(chat_id, message_id, user_game.game_id)
        return
    
    on_cooldown, remaining = game_manager.is_on_cooldown(user_id)
    if on_cooldown:
        minutes = remaining // 60
        seconds = remaining % 60
        await query.edit_message_text(
            f"⏳ *به جیبت استراحت بده!*\n\n"
            f"💤 {minutes} دقیقه و {seconds} ثانیه دیگه میتونی بازی کنی\n\n"
            f"🐶 هاپوها هم نیاز به استراحت دارن!",
            parse_mode="Markdown"
        )
        return
    
    if str(user_id) in GAME_XO_STATE:
        state = GAME_XO_STATE[str(user_id)]
        if state.get("state") == "betting":
            msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
            msg += "💰 *مبلغ ورودی : درحال تعیین*\n\n❓ لطفا مبلغ ورودی را در جواب همین پنل وارد کنید\n┘─ مثال : 500\n┘─ مثال : 1k\n┘─ مثال : 1.5m"
            await query.edit_message_text(msg, parse_mode="Markdown")
            return
    
    msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
    msg += "💰 *مبلغ ورودی : تعیین نشده ❌*"
    keyboard = [[InlineKeyboardButton("💰 تعیین مبلغ ورودی", callback_data="game_xo_set_bet")]]
    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ================================================================
# تعیین مبلغ شرط
# ================================================================

async def handle_xo_set_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر تعیین مبلغ شرط - ویرایش همون پیام"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    game_obj = get_game(user_id)
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < GAME_HOST_REQUIRED_LEVEL:
        await query.edit_message_text(f"❌ *برای ساخت میز بازی به سطح {GAME_HOST_REQUIRED_LEVEL} نیاز داری.*", parse_mode="Markdown")
        return
    
    GAME_XO_STATE[str(user_id)] = {"state": "betting"}
    
    msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
    msg += "💰 *مبلغ ورودی : درحال تعیین*\n\n❓ لطفا مبلغ ورودی را در جواب همین پنل وارد کنید\n┘─ مثال : 500\n┘─ مثال : 1k\n┘─ مثال : 1.5m"
    await query.edit_message_text(msg, parse_mode="Markdown")


async def process_xo_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مبلغ شرط وارد شده - با پشتیبانی از اختصارات"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game_obj = get_game(user_id, username or full_name)
    
    if str(user_id) not in GAME_XO_STATE:
        return
    
    state = GAME_XO_STATE[str(user_id)]
    if state.get("state") != "betting":
        return
    
    text = update.message.text.strip()
    
    # ======== تبدیل اختصارات به عدد ========
    bet_amount = parse_amount(text)
    if bet_amount is None:
        await update.message.reply_text(
            "❌ *عدد معتبر وارد کن.*\n\n"
            "💡 *مثال:* `500` یا `1k` یا `1.5k` یا `1m`",
            parse_mode="Markdown"
        )
        return
    
    if bet_amount < 50:
        await update.message.reply_text(f"❌ *حداقل مبلغ {50} هاپو پوینت است*", parse_mode="Markdown")
        return
    if bet_amount > 1000000:
        await update.message.reply_text(f"❌ *حداکثر مبلغ {1000000} هاپو پوینت است*", parse_mode="Markdown")
        return
    
    hop_point = game_obj._to_int(game_obj.data.get("hop_point", 0))
    if hop_point < bet_amount:
        await update.message.reply_text(f"❌ *پوینت کافی نیست! شما {format_number(hop_point)} 🪙 داری*", parse_mode="Markdown")
        return
    
    del GAME_XO_STATE[str(user_id)]
    
    msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
    msg += f"💰 *مبلغ ورودی : {format_number(bet_amount)} 🪙*"
    keyboard = [[InlineKeyboardButton(f"🏗️ ساخت میز بازی ({format_number(bet_amount)} 🪙)", callback_data=f"game-xo-create-{bet_amount}")]]
    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ================================================================
# ساخت میز بازی
# ================================================================

async def handle_xo_create(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int):
    """هندلر ساخت میز بازی - ویرایش همون پیام"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username
    full_name = query.from_user.full_name or f"کاربر{user_id}"
    game_obj = get_game(user_id, username or full_name)
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < GAME_HOST_REQUIRED_LEVEL:
        await query.edit_message_text(f"❌ *برای ساخت میز بازی به سطح {GAME_HOST_REQUIRED_LEVEL} نیاز داری.*", parse_mode="Markdown")
        return
    
    hop_point = game_obj._to_int(game_obj.data.get("hop_point", 0))
    if hop_point < bet_amount:
        await query.edit_message_text(f"❌ *پوینت کافی نیست! شما {format_number(hop_point)} 🪙 داری*", parse_mode="Markdown")
        return
    
    success, game_id, game = game_manager.create_game(user_id, full_name, bet_amount)
    if not success:
        await query.edit_message_text(f"❌ *{game_id}*", parse_mode="Markdown")
        return
    
    game_obj.data["hop_point"] = str(hop_point - bet_amount)
    game_obj.save_data()
    
    msg = get_xo_game_text(game)
    keyboard = get_xo_board_keyboard(game, user_id)
    await query.edit_message_text(
        msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    save_game_message(chat_id, message_id, game_id)
    
    try:
        if query.message.chat.type in ["group", "supergroup"]:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🧩 *یک میز بازی XO ساخته شد!*\n\n"
                    f"👤 *میزبان:* {full_name}\n"
                    f"💰 *مبلغ شرط:* {format_number(bet_amount)} 🪙\n\n"
                    f"💡 *برای پیوستن، روی دکمه زیر کلیک کن.*"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🧩 پیوستن به بازی", callback_data=f"game-xo-join-{game_id}")]
                ]),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error sending game invite: {e}")


# ================================================================
# پیوستن به بازی
# ================================================================

async def handle_xo_join(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    """هندلر پیوستن به بازی - ویرایش همون پیام"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username
    full_name = query.from_user.full_name or f"کاربر{user_id}"
    game_obj = get_game(user_id, username or full_name)
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < GAME_REQUIRED_LEVEL:
        await query.edit_message_text(f"❌ *برای بازی XO به سطح {GAME_REQUIRED_LEVEL} نیاز داری.*", parse_mode="Markdown")
        return
    
    game = game_manager.get_game(game_id)
    if not game:
        await query.edit_message_text("❌ *بازی مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    if game.status != "waiting":
        await query.edit_message_text("❌ *این بازی در حال انجام است یا به پایان رسیده*", parse_mode="Markdown")
        return
    
    if str(user_id) == game.host_id:
        await query.edit_message_text("❌ *شما میزبان این بازی هستید*", parse_mode="Markdown")
        return
    
    hop_point = game_obj._to_int(game_obj.data.get("hop_point", 0))
    if hop_point < game.bet_amount:
        await query.edit_message_text(
            f"❌ *پوینت کافی نیست! شما {format_number(hop_point)} 🪙 داری، نیاز به {format_number(game.bet_amount)} 🪙*",
            parse_mode="Markdown"
        )
        return
    
    on_cooldown, remaining = game_manager.is_on_cooldown(user_id)
    if on_cooldown:
        minutes = remaining // 60
        seconds = remaining % 60
        await query.edit_message_text(
            f"⏳ *به جیبت استراحت بده!*\n\n"
            f"💤 {minutes} دقیقه و {seconds} ثانیه دیگه میتونی بازی کنی",
            parse_mode="Markdown"
        )
        return
    
    success, _, joined_game = game_manager.join_game(game_id, user_id, full_name)
    if not success:
        await query.edit_message_text(f"❌ *{success}*", parse_mode="Markdown")
        return
    
    game_obj.data["hop_point"] = str(hop_point - game.bet_amount)
    game_obj.save_data()
    
    game_manager.set_cooldown(user_id)
    game_manager.set_cooldown(int(game.host_id))
    
    msg = get_xo_game_text(joined_game)
    keyboard = get_xo_board_keyboard(joined_game, user_id)
    await query.edit_message_text(
        msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    save_game_message(chat_id, message_id, game_id)


# ================================================================
# حرکت در بازی
# ================================================================

async def handle_xo_move(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, row: int, col: int):
    """هندلر حرکت در بازی - ویرایش همون پیام"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    game_obj = get_game(user_id)
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    game = game_manager.get_game(game_id)
    if not game:
        await query.edit_message_text("❌ *بازی مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    if game.status != "playing":
        await query.edit_message_text("❌ *این بازی در حال انجام نیست*", parse_mode="Markdown")
        return
    
    user_id_str = str(user_id)
    if game.current_turn == "host" and user_id_str != game.host_id:
        await query.answer("❌ نوبت میزبان است!", show_alert=True)
        return
    if game.current_turn == "player" and user_id_str != game.player_id:
        await query.answer("❌ نوبت بازیکن دوم است!", show_alert=True)
        return
    
    result = game_manager.make_move(game_id, user_id, row, col)
    if not result.get("success"):
        await query.answer(f"❌ {result.get('reason', 'خطا')}", show_alert=True)
        return
    
    if result.get("winner"):
        winner = result.get("winner")
        is_draw = result.get("is_draw", False)
        
        if not is_draw:
            prize = game.bet_amount * 2
            winner_id = int(game.host_id if winner == "host" else game.player_id)
            winner_game = get_game(winner_id)
            winner_points = winner_game._to_int(winner_game.data.get("hop_point", 0))
            winner_game.data["hop_point"] = str(winner_points + prize)
            winner_game.save_data()
            
            try:
                await context.bot.send_message(
                    winner_id,
                    f"🎉 *شما برنده شدید!*\n💰 *جایزه:* {format_number(prize)} 🪙",
                    parse_mode="Markdown"
                )
            except:
                pass
            
            loser_id = int(game.player_id if winner == "host" else game.host_id)
            try:
                await context.bot.send_message(
                    loser_id,
                    f"😔 *شما بازنده شدید.*\n💰 *مبلغ از دست رفته:* {format_number(game.bet_amount)} 🪙",
                    parse_mode="Markdown"
                )
            except:
                pass
        else:
            for pid in [game.host_id, game.player_id]:
                if pid:
                    p_game = get_game(int(pid))
                    p_points = p_game._to_int(p_game.data.get("hop_point", 0))
                    p_game.data["hop_point"] = str(p_points + game.bet_amount)
                    p_game.save_data()
                    try:
                        await context.bot.send_message(
                            int(pid),
                            f"🤝 *بازی مساوی شد!*\n💰 *{format_number(game.bet_amount)} 🪙 برگشت*",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
        
        clear_game_message(chat_id, game_id)
        asyncio.create_task(remove_game_after_delay(game_id, 300))
    
    updated_game = game_manager.get_game(game_id)
    if updated_game:
        msg = get_xo_game_text(updated_game)
        keyboard = get_xo_board_keyboard(updated_game, user_id)
        
        await query.edit_message_text(
            msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        save_game_message(chat_id, message_id, game_id)


# ================================================================
# بستن و لغو بازی
# ================================================================

async def handle_xo_close(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    """هندلر بستن بازی"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    
    clear_game_message(chat_id, game_id)
    game_manager.remove_game(game_id)
    
    await query.edit_message_text(
        "🔙 *بازی بسته شد.*\n\nبرای شروع بازی جدید، دوباره «بازی هاپویی» رو بزن.",
        parse_mode="Markdown"
    )


async def handle_xo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    """هندلر لغو میز بازی"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    game_obj = get_game(user_id)
    game = game_manager.get_game(game_id)
    chat_id = query.message.chat.id
    
    if not game:
        await query.edit_message_text("❌ *بازی مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    if str(user_id) != game.host_id:
        await query.edit_message_text("❌ *فقط میزبان می‌تواند میز را لغو کند*", parse_mode="Markdown")
        return
    
    game_obj.data["hop_point"] = str(game_obj._to_int(game_obj.data.get("hop_point", 0)) + game.bet_amount)
    game_obj.save_data()
    
    clear_game_message(chat_id, game_id)
    game_manager.remove_game(game_id)
    
    await query.edit_message_text(
        "🗑️ *میز بازی لغو شد و پول شما برگشت.*\n\nبرای شروع بازی جدید، دوباره «بازی هاپویی» رو بزن.",
        parse_mode="Markdown"
    )


async def remove_game_after_delay(game_id: str, delay: int):
    """حذف بازی بعد از تاخیر"""
    await asyncio.sleep(delay)
    game_manager.remove_game(game_id)
