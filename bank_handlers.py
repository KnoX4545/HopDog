# bank_handlers.py - هندلرهای بانک هاپویی و انتقال هاپویی

import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    BANK_PURCHASE_COST, BANK_REQUIRED_LEVEL, TRANSFER_MIN_AMOUNT,
    TRANSFER_MAX_AMOUNT, TRANSFER_COOLDOWN, TRANSFER_MIN_LEVEL_SENDER,
    TRANSFER_MIN_LEVEL_RECEIVER, BANK_ACCOUNT_CHANGE_COST
)
from globals import get_game, TRANSFER_STATE
from bank import (
    get_bank_menu_text, get_bank_keyboard, get_change_card_confirm_text,
    get_card_to_card_text, format_number
)
from database import get_user_by_identifier, get_user_by_card
from utils import parse_amount, get_confirm_keyboard
from logger_config import log_transaction, log_security, log_error

logger = logging.getLogger(__name__)


# ================================================================
# منوی بانک
# ================================================================

async def show_bank_menu(update: Update, game):
    """نمایش منوی بانک هاپویی"""
    is_callback = hasattr(update, 'callback_query') and update.callback_query is not None
    
    level = game._to_int(game.data.get("level", 1))
    hop_point = game._to_int(game.data["hop_point"])
    
    if level < BANK_REQUIRED_LEVEL:
        msg = f"🏦 *بانک هاپویی از سطح {BANK_REQUIRED_LEVEL} باز میشود*\n⭐ *سطح شما:* {level}"
        if is_callback:
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    if not game.data.get("bank_opened", False):
        if hop_point < BANK_PURCHASE_COST:
            msg = (
                f"🏦 *برای خرید بانک به {format_number(BANK_PURCHASE_COST)} هاپو پوینت نیاز داری*\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙"
            )
            if is_callback:
                await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(msg, parse_mode="Markdown")
            return
        
        keyboard = [[InlineKeyboardButton(f"🏦 خرید بانک ({format_number(BANK_PURCHASE_COST)} 🪙)", callback_data="buy_bank")]]
        msg = (
            f"🏦 *آیا میخوای بانک هاپویی رو بخری؟*\n"
            f"💰 *هزینه: {format_number(BANK_PURCHASE_COST)} 🪙\n"
            f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙"
        )
        if is_callback:
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    try:
        game.apply_bank_interest()
        msg = get_bank_menu_text(game, False)
        keyboard = get_bank_keyboard(False)
        if is_callback:
            await update.callback_query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in show_bank_menu: {e}")
        if is_callback:
            await update.callback_query.edit_message_text(
                "🏦 *بانک هاپویی*\n\n❌ *خطا در نمایش بانک. لطفاً دوباره تلاش کنید.*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🏦 *بانک هاپویی*\n\n❌ *خطا در نمایش بانک. لطفاً دوباره تلاش کنید.*",
                parse_mode="Markdown"
            )


# ================================================================
# پردازش تراکنش‌های بانکی (واریز و برداشت)
# ================================================================

async def process_bank_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش واریز یا برداشت از بانک"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    is_deposit = context.user_data.get("waiting_for_deposit", False)
    is_withdraw = context.user_data.get("waiting_for_withdraw", False)
    
    if not is_deposit and not is_withdraw:
        return
    
    text = update.message.text.strip()
    amount = parse_amount(text)
    
    if amount is None:
        await update.message.reply_text(
            "❌ *عدد معتبر وارد کن.*\n\n"
            "💡 *مثال:* `500` یا `1k` یا `1.5k` یا `1m`",
            parse_mode="Markdown"
        )
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ *مبلغ باید بیشتر از صفر باشد*", parse_mode="Markdown")
        context.user_data["waiting_for_deposit"] = False
        context.user_data["waiting_for_withdraw"] = False
        return
    
    if is_deposit:
        result = game.deposit(amount)
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await update.message.reply_text(
                f"✅ *{format_number(amount)} هاپو پوینت به بانک واریز شد*\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
        context.user_data["waiting_for_deposit"] = False
        
    elif is_withdraw:
        result = game.withdraw(amount)
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await update.message.reply_text(
                f"✅ *{format_number(amount)} هاپو پوینت از بانک برداشت شد*\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
        context.user_data["waiting_for_withdraw"] = False


# ================================================================
# انتقال هاپویی
# ================================================================

async def transfer_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور انتقال هاپو پوینت"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if game.is_jailed():
        await update.message.reply_text(
            "⛓️ *شما در زندان هستید.*\n\n"
            "📌 *دستورات مجاز در زندان:*\n"
            "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
            "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
            parse_mode="Markdown"
        )
        return
    
    can = game.can_transfer()
    if not can["success"]:
        await update.message.reply_text(can["reason"], parse_mode="Markdown")
        return
    
    target_user_id = None
    target_name = None
    
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_name = update.message.reply_to_message.from_user.full_name or f"کاربر{target_user_id}"
    else:
        parts = update.message.text.split()
        if len(parts) >= 2:
            identifier = parts[1].strip()
            if identifier.startswith('@'):
                identifier = identifier[1:]
            
            if identifier.isdigit():
                target_user_id = int(identifier)
                target_data = get_user_by_identifier(str(target_user_id))
                if target_data:
                    target_name = target_data.get('player_name', f"کاربر{target_user_id}")
                else:
                    await update.message.reply_text(f"❌ *کاربری با آیدی `{identifier}` یافت نشد.*", parse_mode="Markdown")
                    return
            else:
                target_data = get_user_by_identifier(identifier)
                if target_data:
                    target_user_id = int(target_data['user_id'])
                    target_name = target_data.get('player_name', f"کاربر{target_user_id}")
                else:
                    await update.message.reply_text(f"❌ *کاربری با یوزرنیم `@{identifier}` یافت نشد.*", parse_mode="Markdown")
                    return
        else:
            await update.message.reply_text(
                "❌ *لطفاً کاربر مورد نظر را مشخص کن.*\n\n"
                "📌 *روش‌های مشخص کردن کاربر:*\n"
                "1️⃣ ریپلای روی پیام کاربر\n"
                "2️⃣ نوشتن آیدی عددی: `انتقال هاپویی 123456789`\n"
                "3️⃣ نوشتن یوزرنیم: `انتقال هاپویی @username`\n\n"
                "💰 *سپس مبلغ مورد نظر را در مرحله بعد وارد کن.*",
                parse_mode="Markdown"
            )
            return
    
    if target_user_id is None:
        await update.message.reply_text("❌ *کاربر مورد نظر یافت نشد.*", parse_mode="Markdown")
        return
    
    if target_user_id == user_id:
        await update.message.reply_text("❌ *نمی‌تونی به خودت هاپو پوینت انتقال بدی!*", parse_mode="Markdown")
        return
    
    target_game = get_game(target_user_id)
    target_level = target_game._to_int(target_game.data.get("level", 1))
    if target_level < TRANSFER_MIN_LEVEL_RECEIVER:
        await update.message.reply_text(
            f"❌ *کاربر مقصد باید حداقل سطح {TRANSFER_MIN_LEVEL_RECEIVER} داشته باشد.*",
            parse_mode="Markdown"
        )
        return
    
    if target_game.data.get("profile_locked", False):
        await update.message.reply_text("❌ *پروفایل کاربر مقصد قفل است.*", parse_mode="Markdown")
        return
    
    context.user_data["transfer_target_id"] = str(target_user_id)
    context.user_data["transfer_target_name"] = target_name
    context.user_data["waiting_for_transfer_amount"] = True
    
    hop_point = game._to_int(game.data.get("hop_point", 0))
    await update.message.reply_text(
        f"💰 *مبلغ مورد نظر برای انتقال به {target_name} رو وارد کن:*\n\n"
        f"📊 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n"
        f"🔻 *حداقل:* {format_number(TRANSFER_MIN_AMOUNT)} 🪙\n"
        f"🔺 *حداکثر:* {format_number(TRANSFER_MAX_AMOUNT)} 🪙\n\n"
        f"💡 *میتونی از اختصارات استفاده کنی:*\n"
        f"┘─ `1k` = 1,000 | `1.5k` = 1,500\n"
        f"┘─ `1m` = 1,000,000 | `1.5m` = 1,500,000\n"
        f"┘─ `1کا` = 1,000 | `1میل` = 1,000,000\n\n"
        f"💡 *فقط عدد یا اختصار رو تایپ کن و ارسال کن.*",
        parse_mode="Markdown"
    )


async def process_transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مبلغ انتقال"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    if not context.user_data.get("waiting_for_transfer_amount"):
        return
    
    if game.is_jailed():
        await update.message.reply_text(
            "⛓️ *شما در زندان هستید.*\n\n"
            "📌 *دستورات مجاز در زندان:*\n"
            "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
            "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
            parse_mode="Markdown"
        )
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    text = update.message.text.strip()
    amount = parse_amount(text)
    
    if amount is None:
        await update.message.reply_text(
            "❌ *عدد معتبر وارد کن.*\n\n"
            "💡 *مثال:* `500` یا `1k` یا `1.5k` یا `1m`",
            parse_mode="Markdown"
        )
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ *مبلغ باید بیشتر از صفر باشد.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    target_id = context.user_data.get("transfer_target_id")
    target_name = context.user_data.get("transfer_target_name")
    
    if not target_id or not target_name:
        await update.message.reply_text("❌ *خطا در انتقال. لطفاً دوباره تلاش کن.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    try:
        target_id = int(target_id)
    except:
        await update.message.reply_text("❌ *خطا در شناسه کاربر مقصد.*", parse_mode="Markdown")
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    if amount < TRANSFER_MIN_AMOUNT:
        await update.message.reply_text(
            f"❌ *حداقل مبلغ انتقال {format_number(TRANSFER_MIN_AMOUNT)} هاپو پوینت است.*",
            parse_mode="Markdown"
        )
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    if amount > TRANSFER_MAX_AMOUNT:
        await update.message.reply_text(
            f"❌ *حداکثر مبلغ انتقال {format_number(TRANSFER_MAX_AMOUNT)} هاپو پوینت است.*",
            parse_mode="Markdown"
        )
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    hop_point = game._to_int(game.data.get("hop_point", 0))
    if hop_point < amount:
        await update.message.reply_text(
            f"❌ *موجودی کافی نیست.*\n"
            f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n"
            f"💰 *نیاز:* {format_number(amount)} 🪙",
            parse_mode="Markdown"
        )
        context.user_data["waiting_for_transfer_amount"] = False
        return
    
    context.user_data["transfer_amount"] = amount
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ بله", callback_data=f"transfer_confirm_{target_id}_{amount}"),
            InlineKeyboardButton("❌ نه", callback_data=f"transfer_cancel_{target_id}_{amount}")
        ]
    ])
    
    await update.message.reply_text(
        f"⚠️ *آیا از انتقال {format_number(amount)} 🪙 به {target_name} مطمئنی؟*\n\n"
        f"💰 *مبلغ:* {format_number(amount)} 🪙\n"
        f"👤 *گیرنده:* {target_name}\n"
        f"📊 *هاپو پوینت هات پس از انتقال:* {format_number(hop_point - amount)} 🪙\n\n"
        f"❗️ *محدودیت‌ها:*\n"
        f"┘─ *حداقل:* {format_number(TRANSFER_MIN_AMOUNT)} 🪙\n"
        f"┘─ *حداکثر:* {format_number(TRANSFER_MAX_AMOUNT)} 🪙\n"
        f"┘─ *فاصله بین انتقال‌ها:* {TRANSFER_COOLDOWN} ثانیه ({TRANSFER_COOLDOWN//60} دقیقه)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    context.user_data["waiting_for_transfer_amount"] = False


# ================================================================
# کالبک‌های انتقال
# ================================================================

async def handle_transfer_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید انتقال هاپو پوینت"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    data = query.data
    
    parts = data.replace("transfer_confirm_", "").split("_")
    if len(parts) < 2:
        await query.edit_message_text("❌ *خطا در اطلاعات انتقال.*", parse_mode="Markdown")
        return
    
    try:
        target_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        await query.edit_message_text("❌ *خطا در اطلاعات انتقال.*", parse_mode="Markdown")
        return
    
    if game.is_jailed():
        await query.edit_message_text(
            "⛓️ *شما در زندان هستید.*\n\n"
            "📌 *دستورات مجاز در زندان:*\n"
            "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
            "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
            parse_mode="Markdown"
        )
        return
    
    can = game.can_transfer()
    if not can["success"]:
        await query.edit_message_text(can["reason"], parse_mode="Markdown")
        return
    
    hop_point = game._to_int(game.data.get("hop_point", 0))
    if hop_point < amount:
        await query.edit_message_text(
            f"❌ *موجودی کافی نیست.*\n"
            f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
            parse_mode="Markdown"
        )
        return
    
    result = game.transfer_points(target_id, amount)
    if result["success"]:
        target_game = get_game(target_id)
        target_name = target_game.data.get("player_name", f"کاربر{target_id}")
        new_balance = game._to_int(game.data.get("hop_point", 0))
        
        log_transaction(user_id, "انتقال", amount, f"به {target_id}")
        log_security(user_id, "انتقال", f"{amount} به {target_id}")
        
        await query.edit_message_text(
            f"✅ *انتقال موفقیت‌آمیز بود!*\n\n"
            f"💰 *{format_number(amount)} 🪙 به {target_name} انتقال یافت.*\n"
            f"📊 *هاپو پوینت هات:* {format_number(new_balance)} 🪙",
            parse_mode="Markdown"
        )
        
        try:
            target_new_balance = target_game._to_int(target_game.data.get("hop_point", 0))
            await context.bot.send_message(
                target_id,
                f"💰 *{full_name} مبلغ {format_number(amount)} 🪙 به شما انتقال داد!*\n"
                f"📊 *هاپو پوینت هات:* {format_number(target_new_balance)} 🪙",
                parse_mode="Markdown"
            )
        except:
            pass
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
    
    context.user_data["transfer_amount"] = None
    context.user_data["transfer_target_id"] = None
    context.user_data["transfer_target_name"] = None
    context.user_data["waiting_for_transfer_amount"] = False


async def handle_transfer_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو انتقال هاپو پوینت"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ *انتقال لغو شد.*", parse_mode="Markdown")
    context.user_data["transfer_amount"] = None
    context.user_data["transfer_target_id"] = None
    context.user_data["transfer_target_name"] = None
    context.user_data["waiting_for_transfer_amount"] = False


# ================================================================
# کالبک‌های بانک
# ================================================================

async def handle_bank_callback(query, game, data, context):
    """هندلر کالبک‌های بانک"""
    user_id = query.from_user.id
    
    # ======== خرید بانک ========
    if data == "buy_bank":
        result = game.open_bank()
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.edit_message_text(
                f"🏦 *بانک هاپویی خریداری شد!*\n"
                f"💳 *شماره کارت شما:* {result['card_number']}\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(2)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.answer(f"❌ {result['reason']}", show_alert=True)
        return
    
    # ======== واریز ========
    if data == "bank_deposit":
        await query.edit_message_text(
            "💰 *مبلغ واریزی رو بنویس:*\n\n"
            "💡 *میتونی از اختصارات استفاده کنی:*\n"
            "┘─ `1k` = 1,000 | `1.5k` = 1,500\n"
            "┘─ `1m` = 1,000,000 | `1.5m` = 1,500,000\n"
            "┘─ `1کا` = 1,000 | `1میل` = 1,000,000",
            parse_mode="Markdown"
        )
        context.user_data["waiting_for_deposit"] = True
        return
    
    # ======== برداشت ========
    if data == "bank_withdraw":
        await query.edit_message_text(
            "💰 *مبلغ برداشت رو بنویس:*\n\n"
            "💡 *میتونی از اختصارات استفاده کنی:*\n"
            "┘─ `1k` = 1,000 | `1.5k` = 1,500\n"
            "┘─ `1m` = 1,000,000 | `1.5m` = 1,500,000\n"
            "┘─ `1کا` = 1,000 | `1میل` = 1,000,000",
            parse_mode="Markdown"
        )
        context.user_data["waiting_for_withdraw"] = True
        return
    
    # ======== تایید واریز ========
    if data == "deposit_confirm":
        amount = context.user_data.get("deposit_amount")
        if amount is None:
            await query.edit_message_text("❌ *خطا در واریز. لطفاً دوباره تلاش کن.*", parse_mode="Markdown")
            return
        
        result = game.deposit(amount)
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.edit_message_text(
                f"✅ *{format_number(amount)} هاپو پوینت به بانک واریز شد*\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(2)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
        context.user_data["deposit_amount"] = None
        return
    
    # ======== لغو واریز ========
    if data == "deposit_cancel":
        await query.edit_message_text("❌ *واریز لغو شد*", parse_mode="Markdown")
        await asyncio.sleep(1)
        msg = get_bank_menu_text(game, False)
        keyboard = get_bank_keyboard(False)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        context.user_data["deposit_amount"] = None
        return
    
    # ======== تایید برداشت ========
    if data == "withdraw_confirm":
        amount = context.user_data.get("withdraw_amount")
        if amount is None:
            await query.edit_message_text("❌ *خطا در برداشت. لطفاً دوباره تلاش کن.*", parse_mode="Markdown")
            return
        
        result = game.withdraw(amount)
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.edit_message_text(
                f"✅ *{format_number(amount)} هاپو پوینت از بانک برداشت شد*\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(2)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
        context.user_data["withdraw_amount"] = None
        return
    
    # ======== لغو برداشت ========
    if data == "withdraw_cancel":
        await query.edit_message_text("❌ *برداشت لغو شد*", parse_mode="Markdown")
        await asyncio.sleep(1)
        msg = get_bank_menu_text(game, False)
        keyboard = get_bank_keyboard(False)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        context.user_data["withdraw_amount"] = None
        return
    
    # ======== کارت به کارت ========
    if data == "bank_card_to_card":
        await query.edit_message_text(get_card_to_card_text())
        context.user_data["waiting_for_card_to_card"] = True
        return
    
    # ======== تراکنش‌ها ========
    if data == "bank_transactions":
        msg = get_bank_menu_text(game, True)
        keyboard = get_bank_keyboard(True)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    # ======== تغییر شماره حساب ========
    if data == "bank_change_card":
        if not game.data["bank_opened"]:
            await query.answer("❌ شما بانک ندارید", show_alert=True)
            return
        msg = get_change_card_confirm_text(game)
        await query.edit_message_text(msg, reply_markup=get_confirm_keyboard("bank_change_card_yes", "bank_change_card_no"), parse_mode="Markdown")
        return
    
    if data == "bank_change_card_yes":
        result = game.change_card_number()
        if result["success"]:
            hop_point = game._to_int(game.data["hop_point"])
            await query.edit_message_text(
                f"✅ *شماره حساب شما تغییر کرد!*\n"
                f"🔄 *شماره جدید:* {result['new_card']}\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
                parse_mode="Markdown"
            )
            await asyncio.sleep(2)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.answer(f"❌ {result['reason']}", show_alert=True)
        return
    
    if data == "bank_change_card_no":
        await query.edit_message_text("❌ *تغییر شماره حساب لغو شد*", parse_mode="Markdown")
        await asyncio.sleep(1)
        msg = get_bank_menu_text(game, False)
        keyboard = get_bank_keyboard(False)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return


# ================================================================
# پردازش کارت به کارت (پیام)
# ================================================================

async def process_card_to_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش کارت به کارت"""
    if not context.user_data.get("waiting_for_card_to_card"):
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    text = update.message.text.strip()
    parts = text.split()
    
    if len(parts) != 2:
        await update.message.reply_text(
            "❌ *فرمت اشتباه است.*\n\n"
            "🔺 *لطفاً مبلغ و شماره حساب مقصد را وارد کنید*\n"
            "┘─ *مثال:* `500 1234567890123456`\n"
            "┘─ *مثال:* `1k 1234567890123456`",
            parse_mode="Markdown"
        )
        return
    
    amount_str, card_number = parts
    amount = parse_amount(amount_str)
    
    if amount is None:
        await update.message.reply_text(
            "❌ *عدد معتبر وارد کن.*\n\n"
            "💡 *مثال:* `500` یا `1k` یا `1.5k`",
            parse_mode="Markdown"
        )
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ *مبلغ باید بیشتر از صفر باشد*", parse_mode="Markdown")
        return
    
    card_number = card_number.replace(" ", "").replace("-", "")
    if len(card_number) != 16 or not card_number.isdigit():
        await update.message.reply_text("❌ *شماره کارت باید ۱۶ رقم باشد*", parse_mode="Markdown")
        return
    
    result = game.card_to_card(amount, card_number)
    if result["success"]:
        await update.message.reply_text(
            f"✅ *کارت به کارت با موفقیت انجام شد!*\n\n"
            f"💰 *مبلغ:* {format_number(amount)} 🪙\n"
            f"💳 *به کارت:* `{card_number}`\n"
            f"👤 *گیرنده:* {result.get('target_name', 'کاربر')}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
    
    context.user_data["waiting_for_card_to_card"] = False
