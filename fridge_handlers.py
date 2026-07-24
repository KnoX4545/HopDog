# fridge_handlers.py - نسخه کامل اصلاح شده برای ذخیره‌سازی صحیح یخچال

import asyncio
import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    FRIDGE_REQUIRED_LEVEL, FRIDGE_PURCHASE_COST, FRIDGE_MAX_LEVEL,
    FRIDGE_CAPACITY, FRIDGE_UPGRADE_COSTS, FRIDGE_COOK_MULTIPLIER_SELL,
    FRIDGE_COOK_MULTIPLIER_FOOD, SMUGGLE_REQUIRED_LEVEL, SMUGGLE_MIN_HAPO,
    SMUGGLE_MAX_HAPO, SMUGGLE_TIME_PER_HAPO, SMUGGLE_REWARD_MIN,
    SMUGGLE_REWARD_MAX, SMUGGLE_JAIL_DURATION, SMUGGLE_JAIL_FINE,
    HUNT_DECISION_TIMER
)
from globals import get_game
from utils import format_number, get_confirm_keyboard
from logger_config import log_transaction, log_error, log_game
from database import supabase

logger = logging.getLogger(__name__)


# ================================================================
# نمایش منوی یخچال
# ================================================================

async def show_fridge_menu(update: Update, game):
    """نمایش منوی یخچال هاپویی"""
    is_callback = hasattr(update, 'callback_query') and update.callback_query is not None
    
    if game.is_jailed():
        msg = "⛓️ *شما در زندان هستید.*\n\n📌 *دستورات مجاز در زندان:*\n┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک"
        if is_callback:
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    level = game._to_int(game.data.get("level", 1))
    
    if not game.data.get("fridge_owned", False):
        if level < FRIDGE_REQUIRED_LEVEL:
            msg = f"❄️ *یخچال هاپویی از سطح {FRIDGE_REQUIRED_LEVEL} باز میشود*"
            if is_callback:
                await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(msg, parse_mode="Markdown")
            return
        
        hop_point = game._to_int(game.data.get("hop_point", 0))
        if hop_point < FRIDGE_PURCHASE_COST:
            msg = (
                f"❄️ *یخچال هاپویی* ❄️\n\n"
                f"برای خرید یخچال به {format_number(FRIDGE_PURCHASE_COST)} هاپو پوینت نیاز داری\n"
                f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙"
            )
            if is_callback:
                await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(msg, parse_mode="Markdown")
            return
        
        keyboard = [[InlineKeyboardButton(f"🛒 خرید یخچال ({format_number(FRIDGE_PURCHASE_COST)} 🪙)", callback_data="buy_fridge")]]
        msg = (
            f"❄️ *یخچال هاپویی* ❄️\n\n"
            f"🧊 با یخچال هاپویی میتونی حیوانات شکار شده رو ذخیره کنی!\n"
            f"💰 *هزینه خرید:* {format_number(FRIDGE_PURCHASE_COST)} 🪙\n"
            f"📦 *ظرفیت اولیه:* 1 حیوان\n"
            f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n\n"
            f"❄️ *آیا میخوای یخچال هاپویی بخری؟*"
        )
        if is_callback:
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    # ======== یخچال وجود دارد - بررسی وضعیت پخت ========
    game.check_cooking_status()
    
    # ======== دریافت مجدد آیتم‌ها از دیتابیس ========
    items = game.get_fridge_items()
    fridge_level = game._to_int(game.data.get("fridge_level", 1))
    capacity = game.get_fridge_capacity()
    upgrade_cost = game.get_fridge_upgrade_cost()
    player_name = game.data.get("player_name", "کاربر")
    hop_point = game._to_int(game.data.get("hop_point", 0))
    
    msg = f"❄️ *یخچال هاپویی {player_name}*\n\n"
    msg += f"⭐️ *سطح یخچال :* {fridge_level}\n"
    msg += f"📦 *ظرفیت یخچال :* {len(items)}/{capacity}\n"
    msg += f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n"
    
    if game.data.get("hapo_owned", False):
        hapo_food = game._to_int(game.data.get("hapo_food", 0))
        hapo_max_food = game.get_hapo_max_food()
        hapo_name = game.data.get("hapo_name", "هاپو")
        msg += f"🍖 *شکم {hapo_name}:* {hapo_food}/{hapo_max_food}\n"
    
    msg += "\n"
    
    if items:
        msg += "〰️〰️〰️〰️〰️〰️〰️\n"
        for i, item in enumerate(items):
            cooked = item.get("cooked", False)
            cooking = item.get("cooking", False)
            name = item.get("name", "ناشناس")
            emoji = item.get("emoji", "🐟")
            rarity = item.get("rarity_name", "معمولی")
            weight = item.get("weight", 0)
            value = item.get("value", 0)
            nutrition = item.get("nutrition", 1)
            status = ""
            
            if cooked:
                status = " *(پخته شده 🍳)*"
            elif cooking:
                progress = game.get_fridge_item_cook_progress(i)
                if progress:
                    status = f" *(در حال پخت {progress['progress']}%)*"
            
            msg += f"{emoji} *{name}*{status}\n"
            msg += f"┘─ ⭐️ *سطح :* {rarity}\n"
            msg += f"┘─ ⚖️ *وزن :* {weight} کیلو\n"
            msg += f"┘─ 💰 *ارزش :* {format_number(value)} 🪙\n"
            msg += f"┘─ 🍖 *ارزش غذایی :* {nutrition}\n"
            msg += "〰️〰️〰️〰️〰️〰️〰️\n"
    else:
        msg += "❄️ *یخچال خالی است!*\n"
        msg += "〰️〰️〰️〰️〰️〰️〰️\n"
    
    if upgrade_cost is not None:
        msg += f"\n💰 *هزینه ارتقا سطح یخچال :* {format_number(upgrade_cost)} 🪙"
    else:
        msg += "\n🏆 *یخچال در بالاترین سطح است*"
    
    keyboard = []
    if upgrade_cost is not None:
        keyboard.append([InlineKeyboardButton(f"⬆️ ارتقا یخچال ({format_number(upgrade_cost)} 🪙)", callback_data="upgrade_fridge")])
    
    if items:
        row = []
        for i, item in enumerate(items):
            if i < 5:
                emoji = item.get("emoji", "🐟")
                row.append(InlineKeyboardButton(emoji, callback_data=f"fridge_item_{i}"))
        if row:
            keyboard.append(row)
    
    if is_callback:
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")


# ================================================================
# ✅ ذخیره حیوان در یخچال (اصلاح شده با لاگ و ذخیره‌سازی مطمئن)
# ================================================================

async def handle_hunt_to_fridge(update: Update, context: ContextTypes.DEFAULT_TYPE, query, animal_name):
    """ذخیره حیوان شکار شده در یخچال - نسخه اصلاح شده"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    # ======== دریافت حیوان از دیتابیس ========
    animal = game.data.get("current_hunt_animal")
    
    logger.info(f"🔍 handle_hunt_to_fridge - animal_name: '{animal_name}'")
    logger.info(f"🔍 handle_hunt_to_fridge - animal from data: {animal}")
    
    if not animal:
        await query.edit_message_text("❌ *هیچ حیوانی برای ذخیره وجود ندارد*", parse_mode="Markdown")
        return
    
    # ======== بررسی زمان ========
    hunt_time = game._to_float(game.data.get("hunt_time", 0))
    if hunt_time > 0:
        now = datetime.now().timestamp()
        if (now - hunt_time) > HUNT_DECISION_TIMER:
            game.data["current_hunt_animal"] = None
            game.data["hunt_time"] = "0"
            game.save_data()
            await query.edit_message_text("🦌 *حیوان فرار کرد! وقتت تموم شد.*", parse_mode="Markdown")
            return
    
    # ======== بررسی وجود یخچال ========
    if not game.data.get("fridge_owned", False):
        await query.edit_message_text("❌ *شما یخچال هاپویی ندارید! با دستور «یخچال هاپویی» بخر.*", parse_mode="Markdown")
        return
    
    # ======== بررسی ظرفیت یخچال ========
    items = game.get_fridge_items()
    capacity = game.get_fridge_capacity()
    
    logger.info(f"📦 ظرفیت یخچال: {len(items)}/{capacity}")
    
    if len(items) >= capacity:
        msg = f"❌ *یخچال شما پر است!* 📦\n\n"
        msg += f"📊 *ظرفیت:* {len(items)}/{capacity}\n"
        msg += f"{animal['emoji']} *{animal['name']}*\n"
        msg += f"⭐ *سطح:* {animal['rarity_name']}\n"
        msg += f"⚖️ *وزن:* {animal['weight']} کیلو\n"
        msg += f"💰 *ارزش فروش:* {format_number(animal['value'])} 🪙\n"
        msg += f"🍖 *ارزش غذایی:* {animal['nutrition']} کالری\n\n"
        msg += "❗️ *یخچال پر است! یکی از گزینه‌های زیر رو انتخاب کن:*"
        
        keyboard = [
            [InlineKeyboardButton(f"💰 فروش ({format_number(animal['value'])})", callback_data="hunt_sell")],
            [InlineKeyboardButton(f"🍖 به هاپو بده", callback_data="hunt_feed")],
            [InlineKeyboardButton("❄️ حیوان رو رها کن", callback_data="hunt_release")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    # ======== ✅ ذخیره در یخچال ========
    animal_copy = animal.copy()
    animal_copy["cooked"] = False
    animal_copy["cooking"] = False
    items.append(animal_copy)
    
    # ذخیره در دیتابیس
    game.save_fridge_items(items)
    
    # حذف حیوان از حالت شکار
    game.data["current_hunt_animal"] = None
    game.data["hunt_time"] = "0"
    game.save_data()
    
    # ✅ لاگ برای اطمینان
    logger.info(f"✅ حیوان {animal['name']} در یخچال ذخیره شد - کاربر {user_id}")
    logger.info(f"📦 تعداد آیتم‌های یخچال: {len(items)}")
    
    await query.edit_message_text(
        f"❄️ *{animal['emoji']} {animal['name']} با موفقیت در یخچال ذخیره شد!*\n\n"
        f"📦 *ظرفیت یخچال:* {len(items)}/{game.get_fridge_capacity()}",
        parse_mode="Markdown"
    )


# ================================================================
# کالبک‌های یخچال (بقیه توابع)
# ================================================================

async def handle_fridge_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """خرید یخچال"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    result = game.buy_fridge()
    if result["success"]:
        await query.edit_message_text("✅ *یخچال هاپویی خریداری شد!*\n❄️ از این به بعد میتونی حیوانات رو توی یخچال ذخیره کنی.", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_fridge_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """ارتقا یخچال"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    result = game.upgrade_fridge()
    if result["success"]:
        await query.edit_message_text(f"✅ *یخچال به سطح {result['new_level']} ارتقا یافت!*", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_fridge_back(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """برگشت به منوی یخچال"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    await show_fridge_menu(update, game)


async def handle_fridge_item(update: Update, context: ContextTypes.DEFAULT_TYPE, query, index):
    """نمایش جزئیات یک آیتم در یخچال"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    items = game.get_fridge_items()
    if index < 0 or index >= len(items):
        await query.edit_message_text("❌ *حیوان مورد نظر یافت نشد*", parse_mode="Markdown")
        return
    
    item = items[index]
    cooked = item.get("cooked", False)
    cooking = item.get("cooking", False)
    name = item.get("name", "ناشناس")
    emoji = item.get("emoji", "🐟")
    rarity = item.get("rarity_name", "معمولی")
    weight = item.get("weight", 0)
    value = item.get("value", 0)
    nutrition = item.get("nutrition", 1)
    original_value = item.get("original_value", value)
    original_nutrition = item.get("original_nutrition", nutrition)
    hop_point = game._to_int(game.data["hop_point"])
    
    status = ""
    if cooked:
        status = " *(پخته شده 🍳)*"
    elif cooking:
        progress = game.get_fridge_item_cook_progress(index)
        if progress:
            status = f" *(در حال پخت {progress['progress']}%)*"
    
    msg = f"❄️ *یخچال هاپویی*\n\n"
    msg += f"{emoji} *{name}*{status}\n"
    msg += f"⭐️ *سطح :* {rarity}\n"
    msg += f"⚖️ *وزن :* {weight} کیلو\n"
    msg += f"💰 *ارزش :* {format_number(value)} 🪙\n"
    msg += f"🍖 *ارزش غذایی :* {nutrition}\n"
    msg += f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n\n"
    
    if cooked:
        msg += f"🔹 *ارزش قبل از پخت:* {format_number(original_value)} 🪙\n"
        msg += f"🔹 *ارزش غذایی قبل از پخت:* {original_nutrition}\n\n"
    
    msg += "❗️ *میخوای چیکارش کنی ؟*"
    
    keyboard = []
    if cooking:
        keyboard.append([InlineKeyboardButton("◀️ برگشت", callback_data="fridge_back")])
    elif cooked:
        keyboard.append([
            InlineKeyboardButton(f"💰 فروش ({format_number(value)} 🪙)", callback_data=f"fridge_sell_{index}")
        ])
        if game.data.get("hapo_owned", False):
            keyboard.append([
                InlineKeyboardButton(f"🍖 به هاپو بده ({nutrition} کالری)", callback_data=f"fridge_feed_{index}")
            ])
        keyboard.append([InlineKeyboardButton("◀️ برگشت", callback_data="fridge_back")])
    else:
        cook_time = int(weight * 100)
        minutes = cook_time // 60
        seconds = cook_time % 60
        keyboard.append([
            InlineKeyboardButton(f"🔥 بپوخش ({minutes}م {seconds}ث)", callback_data=f"fridge_cook_{index}")
        ])
        keyboard.append([
            InlineKeyboardButton(f"💰 فروش ({format_number(value)} 🪙)", callback_data=f"fridge_sell_{index}")
        ])
        if game.data.get("hapo_owned", False):
            keyboard.append([
                InlineKeyboardButton(f"🍖 به هاپو بده ({nutrition} کالری)", callback_data=f"fridge_feed_{index}")
            ])
        keyboard.append([InlineKeyboardButton("◀️ برگشت", callback_data="fridge_back")])
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_fridge_cook(update: Update, context: ContextTypes.DEFAULT_TYPE, query, index):
    """شروع پخت حیوان در یخچال - ✅ با ذخیره‌سازی در دیتابیس"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    result = game.cook_item(index)
    if result["success"]:
        cook_time = result["cook_time"]
        minutes = cook_time // 60
        seconds = cook_time % 60
        item = result["item"]
        
        # ✅ اطمینان از ذخیره در دیتابیس
        game.save_data()
        
        logger.info(f"🔥 شروع پخت {item['name']} - کاربر {user_id} - زمان: {cook_time}s")
        
        await query.edit_message_text(
            f"🔥 *شروع پخت {item['emoji']} {item['name']}!*\n\n"
            f"⏳ *زمان پخت:* {minutes} دقیقه و {seconds} ثانیه\n"
            f"💡 *وقتی پخت تموم شد، بهت پیام میدم!*",
            parse_mode="Markdown"
        )
        asyncio.create_task(cook_timer(update, context, user_id, index, cook_time))
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def cook_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, index, cook_time):
    """تایمر پخت حیوان - ✅ با ذخیره‌سازی در دیتابیس"""
    await asyncio.sleep(cook_time)
    try:
        game = get_game(user_id)
        if not game.data.get("fridge_owned", False):
            return
        
        # بازیابی آیتم‌ها از دیتابیس
        items = game.get_fridge_items()
        if index < 0 or index >= len(items):
            return
        
        item = items[index]
        if not item.get("cooking", False):
            return
        
        # ✅ تکمیل پخت
        item["cooked"] = True
        item["cooking"] = False
        item["original_value"] = item.get("value", 0)
        item["original_nutrition"] = item.get("nutrition", 1)
        item["value"] = int(item["value"] * 10)
        item["nutrition"] = item["nutrition"] * 2
        
        # ✅ ذخیره در دیتابیس
        game.save_fridge_items(items)
        game.save_data()
        
        logger.info(f"✅ پخت {item['name']} کامل شد - کاربر {user_id}")
        
        try:
            await context.bot.send_message(
                user_id,
                f"🔥 *پخت {item['emoji']} {item['name']} کامل شد!*\n\n"
                f"💰 *ارزش جدید:* {format_number(item['value'])} 🪙 *(10 برابر)*\n"
                f"🍖 *ارزش غذایی جدید:* {item['nutrition']} *(2 برابر)*\n\n"
                f"❄️ *برای مشاهده به «یخچال هاپویی» برو.*",
                parse_mode="Markdown"
            )
        except:
            pass
    except Exception as e:
        logger.error(f"Error in cook_timer: {e}")


async def handle_fridge_sell(update: Update, context: ContextTypes.DEFAULT_TYPE, query, index):
    """فروش حیوان از یخچال - ✅ با حذف از دیتابیس"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    result = game.sell_from_fridge(index)
    if result["success"]:
        item = result["item"]
        value = result["value"]
        hop_point = game._to_int(game.data["hop_point"])
        
        logger.info(f"💰 فروش {item['name']} از یخچال - کاربر {user_id} - {value} 🪙")
        
        await query.edit_message_text(
            f"💰 *{item['emoji']} {item['name']} فروخته شد!*\n"
            f"✅ *{format_number(value)} 🪙 به حساب شما واریز شد.*\n"
            f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def handle_fridge_feed(update: Update, context: ContextTypes.DEFAULT_TYPE, query, index):
    """تغذیه هاپو از یخچال - ✅ با حذف از دیتابیس"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    result = game.feed_hapo_from_fridge(index)
    if result["success"]:
        item = result["item"]
        fed = result["fed"]
        new_food = result.get("new_food", 0)
        max_food = result.get("max_food", 0)
        hop_point = game._to_int(game.data["hop_point"])
        
        logger.info(f"🍖 تغذیه هاپو از یخچال - {item['name']} - کاربر {user_id}")
        
        await query.edit_message_text(
            f"🍖 *{item['emoji']} {item['name']} به هاپو داده شد!*\n\n"
            f"✅ *{fed} کالری به هاپو اضافه شد.*\n"
            f"🍖 *شکم هاپو:* {new_food}/{max_food}\n"
            f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1)
        await show_fridge_menu(update, game)
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


# ================================================================
# رها کردن حیوان (از شکار)
# ================================================================

async def handle_hunt_release(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """رها کردن حیوان شکار شده"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
    animal = game.data.get("current_hunt_animal")
    if not animal:
        await query.edit_message_text("❌ *هیچ حیوانی برای رها کردن وجود ندارد*", parse_mode="Markdown")
        return
    
    animal_name = animal.get("name", "حیوان")
    animal_emoji = animal.get("emoji", "🐾")
    
    game.data["current_hunt_animal"] = None
    game.data["hunt_time"] = "0"
    game.save_data()
    
    await query.edit_message_text(
        f"{animal_emoji} *{animal_name} رو رها کردی!*\n\n🐾 حیوان به طبیعت برگشت...",
        parse_mode="Markdown"
    )


# ================================================================
# قاچاق هاپویی
# ================================================================

async def show_smuggle_menu(update: Update, game):
    """نمایش منوی قاچاق هاپویی"""
    if game.is_jailed():
        await update.message.reply_text(
            "⛓️ *شما در زندان هستید.*\n\n"
            "📌 *دستورات مجاز در زندان:*\n"
            "┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
            "┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک",
            parse_mode="Markdown"
        )
        return
    
    level = game._to_int(game.data.get("level", 1))
    if level < SMUGGLE_REQUIRED_LEVEL:
        await update.message.reply_text(
            f"🥷 *قاچاق هاپویی از سطح {SMUGGLE_REQUIRED_LEVEL} باز میشود*",
            parse_mode="Markdown"
        )
        return
    
    street_hapo = game._to_int(game.data.get("street_hapo_rescued", 0))
    status = game.check_smuggle_status()
    
    if status:
        if status.get("status") == "in_progress":
            remaining = status.get("remaining", 0)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            progress = status.get("progress", 0)
            
            if hours > 0:
                time_text = f"{hours} ساعت و {minutes} دقیقه"
            else:
                time_text = f"{minutes} دقیقه"
            
            await update.message.reply_text(
                f"🥷 *قاچاق هاپویی در حال انجام...*\n\n"
                f"📦 *تعداد هاپوها:* {status.get('count', 0)}\n"
                f"⏳ *زمان باقی‌مانده:* {time_text}\n"
                f"📊 *پیشرفت:* {progress}%\n\n"
                f"💡 *وقتی قاچاق تموم شد بهت پیام میدم!*",
                parse_mode="Markdown"
            )
            return
        elif status.get("status") == "success":
            reward = status.get("reward", 0)
            count = status.get("count", 0)
            await update.message.reply_text(
                f"✅ *قاچاق هاپویی با موفقیت انجام شد!*\n\n"
                f"💰 *{count} هاپو با موفقیت قاچاق شدن!*\n"
                f"🎁 *پاداش:* {format_number(reward)} 🪙\n\n"
                f"🥷 *تو یک قاچاقچی واقعی هستی!*",
                parse_mode="Markdown"
            )
            return
        elif status.get("status") == "failed":
            count = status.get("count", 0)
            jail_duration = status.get("jail_duration", 40)
            jail_fine = status.get("jail_fine", 5000)
            await update.message.reply_text(
                f"🚨 *قاچاق هاپویی ناموفق!*\n\n"
                f"😱 *{count} هاپو توسط پلیس ضبط شد!*\n"
                f"⛓️ *شما به مدت {jail_duration} دقیقه زندانی شدید!*\n"
                f"💰 *جریمه:* {format_number(jail_fine)} 🪙\n\n"
                f"🥷 *دفعه بعد بیشتر دقت کن...*",
                parse_mode="Markdown"
            )
            return
    
    if street_hapo < SMUGGLE_MIN_HAPO:
        await update.message.reply_text(
            f"🥷 *قاچاق هاپویی*\n\n"
            f"برای شروع قاچاق به حداقل {SMUGGLE_MIN_HAPO} هاپوی خیابونی نیاز داری.\n"
            f"🐶 *هاپوهای خیابونی شما:* {street_hapo}\n\n"
            f"💡 *میتونی با نجات هاپوهای خیابونی تعدادشون رو بیشتر کنی!*",
            parse_mode="Markdown"
        )
        return
    
    keyboard = []
    for i in range(SMUGGLE_MIN_HAPO, min(SMUGGLE_MAX_HAPO + 1, street_hapo + 1), 3):
        row = []
        for j in range(i, min(i + 3, SMUGGLE_MAX_HAPO + 1, street_hapo + 1)):
            row.append(InlineKeyboardButton(f"{j}", callback_data=f"smuggle_count_{j}"))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("◀️ برگشت", callback_data="smuggle_back")])
    
    time_per_hapo = SMUGGLE_TIME_PER_HAPO // 60
    min_time = SMUGGLE_MIN_HAPO * time_per_hapo
    max_time = SMUGGLE_MAX_HAPO * time_per_hapo
    
    await update.message.reply_text(
        f"🥷 *قاچاق هاپویی*\n\n"
        f"🐶 *هاپوهای خیابونی موجود:* {street_hapo}\n"
        f"📦 *تعداد هاپوها برای قاچاق رو انتخاب کن:*\n"
        f"*(حداقل {SMUGGLE_MIN_HAPO} - حداکثر {SMUGGLE_MAX_HAPO})*\n\n"
        f"⏳ *هر هاپو = {time_per_hapo} دقیقه زمان قاچاق*\n"
        f"⏳ *{SMUGGLE_MIN_HAPO} هاپو = {min_time} دقیقه | {SMUGGLE_MAX_HAPO} هاپو = {max_time} دقیقه*\n"
        f"💰 *هر هاپو = {format_number(SMUGGLE_REWARD_MIN)} تا {format_number(SMUGGLE_REWARD_MAX)} 🪙*\n"
        f"🚨 *شانس موفقیت با افزایش تعداد کاهش می‌یابد*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_smuggle_start(update: Update, context: ContextTypes.DEFAULT_TYPE, query, count):
    """شروع قاچاق هاپویی"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    count = int(count)
    
    result = game.start_smuggle(count)
    if result["success"]:
        duration = result.get("duration", 0)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        success_chance = result.get("success_chance", 0)
        
        if hours > 0:
            time_text = f"{hours} ساعت و {minutes} دقیقه"
        else:
            time_text = f"{minutes} دقیقه"
        
        await query.edit_message_text(
            f"🥷 *قاچاق هاپویی شروع شد!*\n\n"
            f"📦 *تعداد هاپوها:* {count}\n"
            f"⏳ *زمان تقریبی:* {time_text}\n"
            f"🍀 *شانس موفقیت:* {success_chance}%\n\n"
            f"💡 *وقتی قاچاق تموم شد بهت پیام میدم!*",
            parse_mode="Markdown"
        )
        asyncio.create_task(smuggle_timer(update, context, user_id))
    else:
        await query.edit_message_text(f"❌ *{result['reason']}*", parse_mode="Markdown")


async def smuggle_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    """تایمر قاچاق هاپویی"""
    try:
        game = get_game(user_id)
        while True:
            status = game.check_smuggle_status()
            if status is None:
                return
            if status.get("status") != "in_progress":
                break
            await asyncio.sleep(60)
        
        if status.get("status") == "success":
            reward = status.get("reward", 0)
            count = status.get("count", 0)
            try:
                await context.bot.send_message(
                    user_id,
                    f"✅ *قاچاق هاپویی با موفقیت انجام شد!*\n\n"
                    f"💰 *{count} هاپو با موفقیت قاچاق شدن!*\n"
                    f"🎁 *پاداش:* {format_number(reward)} 🪙\n\n"
                    f"🥷 *تو یک قاچاقچی واقعی هستی!*",
                    parse_mode="Markdown"
                )
            except:
                pass
        elif status.get("status") == "failed":
            count = status.get("count", 0)
            jail_duration = status.get("jail_duration", 40)
            jail_fine = status.get("jail_fine", 5000)
            try:
                await context.bot.send_message(
                    user_id,
                    f"🚨 *قاچاق هاپویی ناموفق!*\n\n"
                    f"😱 *{count} هاپو توسط پلیس ضبط شد!*\n"
                    f"⛓️ *شما به مدت {jail_duration} دقیقه زندانی شدید!*\n"
                    f"💰 *جریمه:* {format_number(jail_fine)} 🪙\n\n"
                    f"🥷 *دفعه بعد بیشتر دقت کن...*",
                    parse_mode="Markdown"
                )
            except:
                pass
    except Exception as e:
        logger.error(f"Error in smuggle_timer: {e}")


async def handle_smuggle_back(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """برگشت به منوی قاچاق"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    await show_smuggle_menu(update, game)
