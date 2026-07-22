# game_handlers.py - هندلرهای بازی XO

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bank import format_number
from games import game_manager
from handlers_common import get_game, GAME_XO_STATE

logger = logging.getLogger(__name__)


def get_xo_board_keyboard(game, user_id: int):
    if not game or not game.game_id:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ خطا", callback_data="xo_no_move")
        ]])
    
    keyboard = []
    user_id_str = str(user_id)
    
    is_my_turn = False
    if game.status == "playing":
        if game.current_turn == "host" and user_id_str == game.host_id:
            is_my_turn = True
        elif game.current_turn == "player" and user_id_str == game.player_id:
            is_my_turn = True
    
    for row in range(3):
        row_buttons = []
        for col in range(3):
            symbol = game.board[row][col]
            if symbol == " ":
                if is_my_turn:
                    callback = f"xo-move-{game.game_id}-{row}-{col}"
                    row_buttons.append(InlineKeyboardButton("⬜", callback_data=callback))
                else:
                    row_buttons.append(InlineKeyboardButton("⬜", callback_data="xo_no_move"))
            else:
                row_buttons.append(InlineKeyboardButton(symbol, callback_data="xo_no_move"))
        keyboard.append(row_buttons)
    
    if game.status == "waiting":
        keyboard.append([InlineKeyboardButton("⏳ در انتظار بازیکن...", callback_data="xo_no_move")])
    elif game.status == "playing":
        turn_name = game.host_name if game.current_turn == "host" else game.player_name
        keyboard.append([InlineKeyboardButton(f"🎯 نوبت: {turn_name}", callback_data="xo_no_move")])
    elif game.status == "finished":
        if game.winner == "draw":
            keyboard.append([InlineKeyboardButton("🤝 مساوی", callback_data="xo_no_move")])
        else:
            winner_name = game.host_name if game.winner == "host" else game.player_name
            keyboard.append([InlineKeyboardButton(f"🏆 {winner_name} برنده شد!", callback_data="xo_no_move")])
    
    if game.status == "finished":
        keyboard.append([InlineKeyboardButton("🔙 بستن بازی", callback_data=f"xo-close-{game.game_id}")])
    elif game.status == "waiting" and user_id_str == game.host_id:
        keyboard.append([InlineKeyboardButton("🗑️ لغو میز", callback_data=f"xo-cancel-{game.game_id}")])
    
    return InlineKeyboardMarkup(keyboard)


def get_xo_game_text(game) -> str:
    msg = f"🕹 *بازی هاپویی XO* 🧩\n\n"
    msg += f"🧑‍🤝‍🧑 *میزبان:* {game.host_name}\n"
    if game.player_name:
        msg += f"🧑‍🤝‍🧑 *بازیکن:* {game.player_name}\n"
    else:
        msg += f"🧑‍🤝‍🧑 *بازیکن:* در انتظار...\n"
    msg += f"💰 *مبلغ شرط:* {format_number(game.bet_amount)} 🪙\n"
    
    if game.status == "finished":
        if game.winner == "draw":
            msg += f"🤝 *نتیجه:* مساوی!\n💰 *پوینت‌ها به صاحبانش برگشت*\n"
        else:
            winner_name = game.host_name if game.winner == "host" else game.player_name
            prize = game.bet_amount * 2
            msg += f"🏆 *برنده:* {winner_name}!\n💰 *جایزه:* {format_number(prize)} 🪙\n"
    else:
        msg += f"📊 *وضعیت:* {game.get_status_text()}\n"
    
    msg += f"\n┌───┬───┬───┐\n"
    msg += f"│ {game.board[0][0]} │ {game.board[0][1]} │ {game.board[0][2]} │\n"
    msg += f"├───┼───┼───┤\n"
    msg += f"│ {game.board[1][0]} │ {game.board[1][1]} │ {game.board[1][2]} │\n"
    msg += f"├───┼───┼───┤\n"
    msg += f"│ {game.board[2][0]} │ {game.board[2][1]} │ {game.board[2][2]} │\n"
    msg += f"└───┴───┴───┘\n"
    return msg


async def show_games_menu(update: Update, game_obj):
    if game_obj.is_jailed():
        await update.message.reply_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < 2:
        await update.message.reply_text("🕹 *بازی‌های هاپویی از سطح 2 باز میشود*", parse_mode="Markdown")
        return
    
    try:
        user_game = game_manager.get_user_game(int(game_obj.user_id))
        if user_game:
            msg = get_xo_game_text(user_game)
            keyboard = get_xo_board_keyboard(user_game, int(game_obj.user_id))
            await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        msg = "🕹 *بازی های هاپویی* 🐶\n\n❗️ لطفا بازی مورد نظر را انتخاب کنید ⬇️\n\n🧩 بازی میویی XO\n┘─ محدودیت بازیکن : 2 هاپو"
        keyboard = [[InlineKeyboardButton("🧩 بازی XO", callback_data="game_xo_main")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in show_games_menu: {e}")
        await update.message.reply_text("❌ *خطایی رخ داد! لطفاً دوباره تلاش کنید.*", parse_mode="Markdown")


async def show_xo_main(update: Update, query=None, game_obj=None):
    if query:
        user_id = query.from_user.id
        game_obj = get_game(user_id)
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < 2:
        await query.edit_message_text("🕹 *بازی XO از سطح 2 باز میشود*", parse_mode="Markdown")
        return
    
    user_game = game_manager.get_user_game(int(game_obj.user_id))
    if user_game:
        msg = get_xo_game_text(user_game)
        keyboard = get_xo_board_keyboard(user_game, int(game_obj.user_id))
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    on_cooldown, remaining = game_manager.is_on_cooldown(int(game_obj.user_id))
    if on_cooldown:
        await query.edit_message_text(f"⏳ *لطفاً {remaining} ثانیه صبر کنید*", parse_mode="Markdown")
        return
    
    msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
    
    if str(game_obj.user_id) in GAME_XO_STATE:
        state = GAME_XO_STATE[str(game_obj.user_id)]
        if state.get("state") == "betting":
            msg += "💰 *مبلغ ورودی : درحال تعیین*\n\n❓ لطفا مبلغ ورودی را در جواب همین پنل وارد کنید\n┘─ مثال : 500"
            await query.edit_message_text(msg, parse_mode="Markdown")
            return
    
    msg += "💰 *مبلغ ورودی : تعیین نشده ❌*"
    keyboard = [[InlineKeyboardButton("💰 تعیین مبلغ ورودی", callback_data="game_xo_set_bet")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_xo_set_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    game_obj = get_game(user_id)
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < 3:
        await query.edit_message_text("❌ *برای ساخت میز بازی به سطح 3 نیاز داری.*", parse_mode="Markdown")
        return
    
    GAME_XO_STATE[str(user_id)] = {"state": "betting"}
    
    msg = "🕹 *بازی هاپویی XO* 🧩\n\n❗️ لطفا میز بازی را بچینید\n\n"
    msg += "💰 *مبلغ ورودی : درحال تعیین*\n\n❓ لطفا مبلغ ورودی را در جواب همین پنل وارد کنید\n┘─ مثال : 500"
    await query.edit_message_text(msg, parse_mode="Markdown")


async def process_xo_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game_obj = get_game(user_id, username or full_name)
    
    if str(user_id) not in GAME_XO_STATE:
        return
    
    state = GAME_XO_STATE[str(user_id)]
    if state.get("state") != "betting":
        return
    
    text = update.message.text.strip().replace(",", "").replace(" ", "")
    
    try:
        bet_amount = int(text)
    except ValueError:
        await update.message.reply_text("❌ *عدد معتبر وارد کن*", parse_mode="Markdown")
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
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_xo_create(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username
    full_name = query.from_user.full_name or f"کاربر{user_id}"
    game_obj = get_game(user_id, username or full_name)
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < 3:
        await query.edit_message_text("❌ *برای ساخت میز بازی به سطح 3 نیاز داری.*", parse_mode="Markdown")
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
    await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    
    try:
        chat_id = query.message.chat.id
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


async def handle_xo_join(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username
    full_name = query.from_user.full_name or f"کاربر{user_id}"
    game_obj = get_game(user_id, username or full_name)
    
    if game_obj.is_jailed():
        await query.edit_message_text("⛓️ *شما در زندان هستید*", parse_mode="Markdown")
        return
    
    level = game_obj._to_int(game_obj.data.get("level", 1))
    if level < 2:
        await query.edit_message_text("❌ *برای بازی XO به سطح 2 نیاز داری.*", parse_mode="Markdown")
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
        await query.edit_message_text(f"❌ *پوینت کافی نیست! شما {format_number(hop_point)} 🪙 داری، نیاز به {format_number(game.bet_amount)} 🪙*", parse_mode="Markdown")
        return
    
    on_cooldown, remaining = game_manager.is_on_cooldown(user_id)
    if on_cooldown:
        await query.edit_message_text(f"⏳ *لطفاً {remaining} ثانیه صبر کنید*", parse_mode="Markdown")
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
    await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")


async def handle_xo_move(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, row: int, col: int):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    game_obj = get_game(user_id)
    
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
                await context.bot.send_message(winner_id, f"🎉 *شما برنده شدید!*\n💰 *جایزه:* {format_number(prize)} 🪙", parse_mode="Markdown")
            except:
                pass
            
            loser_id = int(game.player_id if winner == "host" else game.host_id)
            try:
                await context.bot.send_message(loser_id, f"😔 *شما بازنده شدید.*\n💰 *مبلغ از دست رفته:* {format_number(game.bet_amount)} 🪙", parse_mode="Markdown")
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
                        await context.bot.send_message(int(pid), f"🤝 *بازی مساوی شد!*\n💰 *{format_number(game.bet_amount)} 🪙 برگشت*", parse_mode="Markdown")
                    except:
                        pass
        
        asyncio.create_task(remove_game_after_delay(game_id, 300))
    
    updated_game = game_manager.get_game(game_id)
    if updated_game:
        msg = get_xo_game_text(updated_game)
        keyboard = get_xo_board_keyboard(updated_game, user_id)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")


async def remove_game_after_delay(game_id: str, delay: int):
    await asyncio.sleep(delay)
    game_manager.remove_game(game_id)


async def handle_xo_close(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    query = update.callback_query
    await query.answer()
    game_manager.remove_game(game_id)
    await query.edit_message_text("🔙 *بازی بسته شد.*", parse_mode="Markdown")


async def handle_xo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    game_obj = get_game(user_id)
    
    game = game_manager.get_game(game_id)
    if not game:
        await query.edit_message_text("❌ *بازی مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    if str(user_id) != game.host_id:
        await query.edit_message_text("❌ *فقط میزبان می‌تواند میز را لغو کند*", parse_mode="Markdown")
        return
    
    game_obj.data["hop_point"] = str(game_obj._to_int(game_obj.data.get("hop_point", 0)) + game.bet_amount)
    game_obj.save_data()
    
    game_manager.remove_game(game_id)
    await query.edit_message_text("🗑️ *میز بازی لغو شد و پول شما برگشت.*", parse_mode="Markdown")
