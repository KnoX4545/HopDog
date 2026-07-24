# game_handlers.py - هندلرهای بازی هاپویی (نسخه کامل با اصلاحات)

import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import GAME_REQUIRED_LEVEL, GAME_HOST_REQUIRED_LEVEL
from game_functions import game_manager, get_xo_board_keyboard, get_xo_game_text, get_xo_invite_text, get_xo_winner_text
from bank import format_number
from utils import parse_amount, get_confirm_keyboard
from globals import (
    get_game, GAME_XO_STATE, GAME_MESSAGES,
    save_game_message, get_game_message, clear_game_message,
    set_xo_state, get_xo_state, clear_xo_state
)
from logger_config import log_game, log_transaction, log_error

logger = logging.getLogger(__name__)


# ================================================================
# توابع کمکی
# ================================================================

async def update_game_message(query, game_id: str, user_id: int):
    """به‌روزرسانی پیام بازی (همون پیام رو ویرایش کن)"""
    game = game_manager.get_game(game_id)
    
    if not game:
        await query.edit_message_text("❌ *بازی مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    msg = get_xo_game_text(game)
    keyboard = get_xo_board_keyboard(game, user_id)
    
    try:
        await query.edit_message_text(
            msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        log_game(game_id, "به‌روزرسانی", f"کاربر {user_id}")
    except Exception as e:
        logger.error(f"❌ خطا در به‌روزرسانی پیام بازی {game_id}: {e}")
        log_error(e, f"به‌روزرسانی پیام بازی {game_id}", user_id)


async def send_game_message(chat_id, game_id: str, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام جدید بازی (وقتی ویرایش ممکن نیست)"""
    game = game_manager.get_game(game_id)
    
    if not game:
        return
    
    msg = get_xo_game_text(game)
    keyboard = get_xo_board_keyboard(game, user_id)
    
    try:
        sent = await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        save_game_message(chat_id, sent.message_id, game_id)
        log_game(game_id, "ارسال پیام جدید", f"کاربر {user_id}")
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام بازی {game_id}: {e}")
        log_error(e, f"ارسال پیام بازی {game_id}", user_id)


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
        await update.message.reply_text(
            f"🕹 *بازی‌های هاپویی از سطح {GAME_REQUIRED_LEVEL} باز میشود*\n\n"
            f"⭐ *سطح شما:* {level}\n"
            f"📈 *برای رسیدن به سطح {GAME_REQUIRED_LEVEL}، هاپ هاپ کن!*",
            parse_mode="Markdown"
        )
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
        log_game(user_game.game_id, "نمایش بازی فعال", f"کاربر {user_id}")
        return
    
    # ======== منوی اصلی ========
    msg = "🕹 *بازی های هاپویی* 🐶\n\n❗️ لطفا بازی مورد نظر را انتخاب کنید ⬇️\n\n🧩 بازی میویی XO\n┘─ محدودیت بازیکن : 2 هاپو"
    keyboard = [[InlineKeyboardButton("🧩 بازی XO", callback_data="game_xo_main")]]
    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    logger.info(f"🎮 منوی بازی برای کاربر {user_id} نمایش داده شد")


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
        await query.edit_message_text(
            f"🕹 *بازی XO از سطح {GAME_REQUIRED_LEVEL} باز میشود*\n\n"
            f"⭐ *سطح شما:* {level}",
            parse_mode="Markdown"
        )
        return
    
    user_id = int(game_obj.user_id)
    
    # ======== بررسی بازی فعال ========
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
        log_game(user_game.game_id, "نمایش در منوی XO", f"کاربر {user_id}")
        return
    
    # ======== بررسی خنک‌سازی ========
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
    
    # ======== بررسی حالت تعیین شرط ========
    xo_state = get_xo_state(user_id)
    if xo_state and xo_state.get("state") == "betting":
        msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
        msg += "💰 *مبلغ ورودی : درحال تعیین*\n\n❓ لطفا مبلغ ورودی را در جواب همین پنل وارد کنید\n┘─ مثال : 500\n┘─ مثال : 1k\n┘─ مثال : 1.5m"
        await query.edit_message_text(msg, parse_mode="Markdown")
        return
    
    # ======== منوی اصلی XO ========
    msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
    msg += "💰 *مبلغ ورودی : تعیین نشده ❌*"
    keyboard = [[InlineKeyboardButton("💰 تعیین مبلغ ورودی", callback_data="game_xo_set_bet")]]
    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    logger.info(f"🎮 منوی XO برای کاربر {user_id} نمایش داده شد")


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
        await query.edit_message_text(
            f"❌ *برای ساخت میز بازی به سطح {GAME_HOST_REQUIRED_LEVEL} نیاز داری.*\n"
            f"⭐ *سطح شما:* {level}",
            parse_mode="Markdown"
        )
        return
    
    set_xo_state(user_id, {"state": "betting"})
    logger.info(f"💰 کاربر {user_id} وارد حالت تعیین شرط شد")
    
    msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
    msg += "💰 *مبلغ ورودی : درحال تعیین*\n\n❓ لطفا مبلغ ورودی را در جواب همین پنل وارد کنید\n┘─ مثال : 500\n┘─ مثال : 1k\n┘─ مثال : 1.5m"
    await query.edit_message_text(msg, parse_mode="Markdown")


async def process_xo_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مبلغ شرط وارد شده - با پشتیبانی از اختصارات"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game_obj = get_game(user_id, username or full_name)
    
    xo_state = get_xo_state(user_id)
    if not xo_state or xo_state.get("state") != "betting":
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
        await update.message.reply_text(
            f"❌ *پوینت کافی نیست!*\n"
            f"💰 *موجودی شما:* {format_number(hop_point)} 🪙\n"
            f"💰 *نیاز:* {format_number(bet_amount)} 🪙",
            parse_mode="Markdown"
        )
        return
    
    clear_xo_state(user_id)
    logger.info(f"💰 کاربر {user_id} مبلغ {bet_amount} رو برای شرط انتخاب کرد")
    
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
        await query.edit_message_text(
            f"❌ *برای ساخت میز بازی به سطح {GAME_HOST_REQUIRED_LEVEL} نیاز داری.*\n"
            f"⭐ *سطح شما:* {level}",
            parse_mode="Markdown"
        )
        return
    
    hop_point = game_obj._to_int(game_obj.data.get("hop_point", 0))
    if hop_point < bet_amount:
        await query.edit_message_text(
            f"❌ *پوینت کافی نیست!*\n"
            f"💰 *موجودی شما:* {format_number(hop_point)} 🪙\n"
            f"💰 *نیاز:* {format_number(bet_amount)} 🪙",
            parse_mode="Markdown"
        )
        return
    
    success, game_id, game = game_manager.create_game(user_id, full_name, bet_amount)
    if not success:
        await query.edit_message_text(f"❌ *{success}*", parse_mode="Markdown")
        return
    
    # ======== قفل کردن پول میزبان ========
    game_obj.data["hop_point"] = str(hop_point - bet_amount)
    game_obj.save_data()
    
    log_game(game_id, "ساخت", f"میزبان: {full_name}, مبلغ: {bet_amount}")
    log_transaction(user_id, "شرط‌بندی بازی", bet_amount, f"ساخت میز {game_id}")
    
    msg = get_xo_game_text(game)
    keyboard = get_xo_board_keyboard(game, user_id)
    await query.edit_message_text(
        msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    save_game_message(chat_id, message_id, game_id)
    
    # ======== ارسال دعوتنامه به گروه ========
    try:
        if query.message.chat.type in ["group", "supergroup"]:
            invite_msg = get_xo_invite_text(game)
            await context.bot.send_message(
                chat_id=chat_id,
                text=invite_msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🧩 پیوستن به بازی", callback_data=f"game-xo-join-{game_id}")]
                ]),
                parse_mode="Markdown"
            )
            log_game(game_id, "ارسال دعوتنامه", f"به گروه {chat_id}")
    except Exception as e:
        logger.error(f"❌ خطا در ارسال دعوتنامه بازی {game_id}: {e}")
        log_error(e, f"ارسال دعوتنامه بازی {game_id}", user_id)


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
        await query.edit_message_text(
            f"❌ *برای بازی XO به سطح {GAME_REQUIRED_LEVEL} نیاز داری.*\n"
            f"⭐ *سطح شما:* {level}",
            parse_mode="Markdown"
        )
        return
    
    game = game_manager.get_game(game_id)
    if not game:
        await query.edit_message_text("❌ *بازی مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    if game.status != "waiting":
        await query.edit_message_text(f"❌ *این بازی در حال انجام است یا به پایان رسیده (وضعیت: {game.status})*", parse_mode="Markdown")
        return
    
    if str(user_id) == game.host_id:
        await query.edit_message_text("❌ *شما میزبان این بازی هستید*", parse_mode="Markdown")
        return
    
    hop_point = game_obj._to_int(game_obj.data.get("hop_point", 0))
    if hop_point < game.bet_amount:
        await query.edit_message_text(
            f"❌ *پوینت کافی نیست!*\n"
            f"💰 *موجودی شما:* {format_number(hop_point)} 🪙\n"
            f"💰 *نیاز:* {format_number(game.bet_amount)} 🪙",
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
    
    # ======== قفل کردن پول بازیکن دوم ========
    game_obj.data["hop_point"] = str(hop_point - game.bet_amount)
    game_obj.save_data()
    
    # ======== تنظیم خنک‌سازی برای هر دو بازیکن ========
    game_manager.set_cooldown(user_id)
    game_manager.set_cooldown(int(game.host_id))
    
    log_game(game_id, "پیوستن", f"بازیکن: {full_name}")
    log_transaction(user_id, "شرط‌بندی بازی", game.bet_amount, f"پیوستن به {game_id}")
    
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
        await query.edit_message_text(f"❌ *این بازی در حال انجام نیست (وضعیت: {game.status})*", parse_mode="Markdown")
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
    
    log_game(game_id, "حرکت", f"کاربر {user_id} در ({row},{col})")
    
    # ======== بررسی پایان بازی ========
    if result.get("winner"):
        winner = result.get("winner")
        is_draw = result.get("is_draw", False)
        
        if not is_draw:
            # ======== ✅ برنده مشخص شده - پرداخت جایزه ========
            prize = game.bet_amount * 2
            winner_id = int(game.host_id if winner == "host" else game.player_id)
            loser_id = int(game.player_id if winner == "host" else game.host_id)
            
            # ======== پرداخت جایزه به برنده ========
            winner_game = get_game(winner_id)
            winner_points = winner_game._to_int(winner_game.data.get("hop_point", 0))
            winner_game.data["hop_point"] = str(winner_points + prize)
            winner_game.save_data()
            
            log_game(game_id, "پایان", f"برنده: {winner_id}, جایزه: {prize}")
            log_transaction(winner_id, "برنده بازی", prize, f"بازی {game_id}")
            
            # ======== پیام به برنده ========
            try:
                await context.bot.send_message(
                    winner_id,
                    f"🎉 *شما برنده شدید!*\n"
                    f"🧩 *بازی:* {game_id}\n"
                    f"💰 *جایزه:* {format_number(prize)} 🪙\n\n"
                    f"👏 تبریک میگم!",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"❌ خطا در ارسال پیام برنده {winner_id}: {e}")
            
            # ======== پیام به بازنده ========
            try:
                await context.bot.send_message(
                    loser_id,
                    f"😔 *شما بازنده شدید.*\n"
                    f"🧩 *بازی:* {game_id}\n"
                    f"💰 *مبلغ از دست رفته:* {format_number(game.bet_amount)} 🪙\n\n"
                    f"💪 دفعه بعد بیشتر تلاش کن!",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"❌ خطا در ارسال پیام بازنده {loser_id}: {e}")
        
        else:
            # ======== ✅ بازی مساوی - برگشت پول ========
            log_game(game_id, "مساوی", "بازی مساوی شد - برگشت پول")
            
            for pid in [game.host_id, game.player_id]:
                if pid:
                    p_game = get_game(int(pid))
                    p_points = p_game._to_int(p_game.data.get("hop_point", 0))
                    p_game.data["hop_point"] = str(p_points + game.bet_amount)
                    p_game.save_data()
                    
                    try:
                        await context.bot.send_message(
                            int(pid),
                            f"🤝 *بازی مساوی شد!*\n"
                            f"🧩 *بازی:* {game_id}\n"
                            f"💰 *{format_number(game.bet_amount)} 🪙 به حساب شما برگشت*",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"❌ خطا در ارسال پیام مساوی به {pid}: {e}")
        
        # ======== پاک کردن پیام ذخیره شده ========
        clear_game_message(chat_id, game_id)
        
        # ======== حذف بازی بعد از ۵ دقیقه ========
        asyncio.create_task(remove_game_after_delay(game_id, 300))
    
    # ======== به‌روزرسانی پیام ========
    updated_game = game_manager.get_game(game_id)
    if updated_game:
        msg = get_xo_game_text(updated_game)
        keyboard = get_xo_board_keyboard(updated_game, user_id)
        
        try:
            await query.edit_message_text(
                msg,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            log_game(game_id, "به‌روزرسانی پیام", f"کاربر {user_id}")
        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی پیام بازی {game_id}: {e}")
            # اگر نتونست ویرایش کنه، پیام جدید بفرست
            await send_game_message(chat_id, game_id, user_id, context)


# ================================================================
# بستن و لغو بازی
# ================================================================

async def handle_xo_close(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    """هندلر بستن بازی"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    
    clear_game_message(chat_id, game_id)
    game_manager.remove_game(game_id)
    
    log_game(game_id, "بسته شدن", f"کاربر {user_id}")
    logger.info(f"🗑️ بازی {game_id} توسط کاربر {user_id} بسته شد")
    
    await query.edit_message_text(
        "🔙 *بازی بسته شد.*\n\n"
        "برای شروع بازی جدید، دوباره «بازی هاپویی» رو بزن.",
        parse_mode="Markdown"
    )


async def handle_xo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    """هندلر لغو میز بازی - ✅ برگشت پول به میزبان"""
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
    
    # ======== ✅ برگشت پول به میزبان ========
    current_points = game_obj._to_int(game_obj.data.get("hop_point", 0))
    game_obj.data["hop_point"] = str(current_points + game.bet_amount)
    game_obj.save_data()
    
    log_game(game_id, "لغو میز", f"میزبان {user_id} - پول برگشت: {game.bet_amount}")
    log_transaction(user_id, "لغو میز بازی", game.bet_amount, f"بازگشت پول {game_id}")
    logger.info(f"🗑️ بازی {game_id} توسط میزبان {user_id} لغو شد - پول برگشت: {game.bet_amount}")
    
    clear_game_message(chat_id, game_id)
    game_manager.remove_game(game_id)
    
    await query.edit_message_text(
        "🗑️ *میز بازی لغو شد و پول شما برگشت.*\n\n"
        f"💰 *مبلغ برگشتی:* {format_number(game.bet_amount)} 🪙\n\n"
        "برای شروع بازی جدید، دوباره «بازی هاپویی» رو بزن.",
        parse_mode="Markdown"
    )


# ================================================================
# تابع کمکی حذف بازی بعد از تاخیر
# ================================================================

async def remove_game_after_delay(game_id: str, delay: int):
    """حذف بازی بعد از تاخیر"""
    await asyncio.sleep(delay)
    game_manager.remove_game(game_id)
    logger.info(f"🗑️ بازی {game_id} بعد از {delay} ثانیه حذف شد")


# ================================================================
# تابع بازیابی پیام بازی (برای ری‌استارت)
# ================================================================

async def restore_game_message(chat_id: int, game_id: str, context: ContextTypes.DEFAULT_TYPE):
    """بازیابی پیام بازی (برای زمانی که بات ری‌استارت شده)"""
    message_id = get_game_message(chat_id, game_id)
    if not message_id:
        return
    
    game = game_manager.get_game(game_id)
    if not game:
        clear_game_message(chat_id, game_id)
        return
    
    try:
        msg = get_xo_game_text(game)
        keyboard = get_xo_board_keyboard(game, int(game.host_id))
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"♻️ پیام بازی {game_id} بازیابی شد")
    except Exception as e:
        logger.error(f"❌ خطا در بازیابی پیام بازی {game_id}: {e}")
        clear_game_message(chat_id, game_id)


# ================================================================
# تست
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 game_handlers.py - تست اولیه")
    print("=" * 60)
    print("✅ فایل آماده استفاده است!")
    print("=" * 60)
