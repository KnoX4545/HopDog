# bot.py - فایل اصلی بات تلگرام

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from core import HopDogGame
from data import RARITY_NAMES, RARITY_COLORS

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)

# توکن بات
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

# دیکشنری برای نگهداری داده‌های کاربران
user_games = {}

def get_game(user_id):
    if user_id not in user_games:
        user_games[user_id] = HopDogGame(user_id)
    return user_games[user_id]

# ================================================================
# دستورات اصلی
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game = get_game(user_id)
    
    if game.data["player_name"] == "":
        await update.message.reply_text(
            "🐾 به هاپ داگ خوش اومدی!\n"
            "اسمت رو برام بنویس تا شروع کنیم 🐕"
        )
        game.data["waiting_for_name"] = True
        game.save_data()
    else:
        await update.message.reply_text(
            f"🐾 سلام {game.data['player_name']}!\n"
            "به هاپ داگ خوش اومدی 🐕\n\n"
            "دستورات:\n"
            "🐾 هاپ هاپ - گرفتن هاپو پوینت\n"
            "📊 هاپویی - وضعیت خودت\n"
            "📚 آکادمی - راهنما\n"
            "🐕 هاپو - مدیریت هاپو\n"
            "🏹 شکار - شکار حیوانات\n"
            "🏦 بانک هاپویی - مدیریت بانک"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game = get_game(user_id)
    text = update.message.text.strip()
    
    # اگر کاربر در حال وارد کردن اسم است
    if game.data.get("waiting_for_name", False):
        game.data["player_name"] = text
        game.data["waiting_for_name"] = False
        game.save_data()
        await update.message.reply_text(
            f"✅ اسم شما ثبت شد: {game.data['player_name']}\n\n"
            "حالا میتونی از دستورات استفاده کنی 🐾\n"
            "🐾 هاپ هاپ - برای گرفتن هاپو پوینت\n"
            "📚 آکادمی - برای راهنما"
        )
        return
    
    # پردازش دستورات
    text_lower = text.lower()
    
    # دستور هاپ هاپ
    if text_lower in ["هاپ هاپ", "هاپ", "hop"]:
        result = game.do_hop()
        if not result["success"]:
            remaining = result.get("remaining", 0)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await update.message.reply_text(
                f"⏳ هنوز هاپت نمیاد...\n"
                f"باید {mins}:{secs:02d} صبر کنی"
            )
            return
        
        msg = f"🐾 {result['earned']} هاپو پوینت گرفتی ✨\n"
        msg += f"💰 هاپو پوینت‌هات: {int(game.data['hop_point'])}"
        
        if result.get("level_up"):
            msg += f"\n\n🎉 سطح شما به {result['new_level']} ارتقا یافت!\n"
            msg += f"🎁 جایزه: {result['reward']} هاپو پوینت"
        
        await update.message.reply_text(msg)
        return
    
    # دستور هاپویی (پروفایل)
    if text_lower in ["هاپویی", "hapui", "وضعیت", "پروفایل"]:
        required = game.get_required_for_level(game.data["level"])
        msg = f"📊 وضعیت هاپویی شما\n"
        msg += f"👤 کاربر: {game.data['player_name']}\n"
        msg += f"⭐ سطح: {game.data['level']}\n"
        if game.data["level"] < 20:
            msg += f"🐾 هاپ شمار: {game.data['hop_count']}/{required}\n"
        else:
            msg += "🏆 سطح نهایی\n"
        msg += f"💰 هاپو پوینت‌هات: {int(game.data['hop_point'])}"
        await update.message.reply_text(msg)
        return
    
    # دستور هاپو
    if text_lower in ["هاپو", "hapo"]:
        await show_hapo_menu(update, game)
        return
    
    # دستور پنجه
    if text_lower in ["پنجه", "claw"]:
        await show_claw_menu(update, game)
        return
    
    # دستور شکار
    if text_lower in ["شکار", "hunt"]:
        await do_hunt(update, game)
        return
    
    # دستور بانک
    if text_lower in ["بانک هاپویی", "هاپو بانک", "بانک"]:
        await show_bank_menu(update, game)
        return
    
    # دستور آکادمی
    if text_lower in ["آکادمی", "academy", "راهنما", "help"]:
        await show_academy(update)
        return
    
    # دستور تغییر اسم
    if text_lower in ["تغییر اسم", "اسم هاپویی"]:
        if game.data["hop_point"] < 750:
            await update.message.reply_text("❌ برای تغییر اسم به 750 هاپو پوینت نیاز داری")
            return
        await update.message.reply_text("✏️ اسم جدید خود را وارد کن")
        context.user_data["waiting_for_new_name"] = True
        return
    
    # اگر کاربر در حال تغییر اسم است
    if context.user_data.get("waiting_for_new_name", False):
        if game.data["hop_point"] < 750:
            await update.message.reply_text("❌ پوینت کافی نیست")
            context.user_data["waiting_for_new_name"] = False
            return
        old_name = game.data["player_name"]
        game.data["player_name"] = text
        game.data["hop_point"] -= 750
        game.save_data()
        await update.message.reply_text(f"✅ اسم شما از {old_name} به {game.data['player_name']} تغییر یافت")
        context.user_data["waiting_for_new_name"] = False
        return
    
    await update.message.reply_text(
        "❌ دستور اشتباه است\n\n"
        "دستورات موجود:\n"
        "🐾 هاپ هاپ\n"
        "📊 هاپویی\n"
        "📚 آکادمی\n"
        "🐕 هاپو\n"
        "🏹 شکار\n"
        "🏦 بانک هاپویی"
    )

# ================================================================
# منوهای تعاملی با دکمه‌های شیشه‌ای
# ================================================================

async def show_hapo_menu(update: Update, game):
    keyboard = []
    
    if not game.data["hapo_owned"]:
        if game.data["level"] < 3:
            await update.message.reply_text("🐕 هاپو از سطح 3 باز میشود")
            return
        if game.data["hop_point"] < 300:
            await update.message.reply_text("🐕 برای خرید هاپو به 300 هاپو پوینت نیاز داری")
            return
        keyboard = [
            [InlineKeyboardButton("🐕 خرید هاپو (300 هاپو پوینت)", callback_data="buy_hapo")]
        ]
        await update.message.reply_text(
            "🐕 آیا میخوای هاپو بخری؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # کاربر هاپو دارد
    game.update_hapo_production()
    total = game.get_hapo_total_level()
    max_food = game.get_hapo_max_food()
    capacity = game.get_hapo_capacity()
    status = game.get_hapo_food_status()
    prod = game.get_hapo_production()
    price = game.get_hapo_upgrade_price()
    is_max = total >= 25
    
    msg = f"🐕 {game.data['hapo_name']}\n"
    msg += f"⭐ سطح: {game.data['hapo_level']}/5\n"
    msg += f"🌟 مقام: {RANK_NAMES[game.data['hapo_rank']]}\n"
    msg += f"🍖 شکم: {status['text']} ({int(game.data['hapo_food'])}/{max_food})\n"
    msg += f"💰 تولیدی: {int(game.data['hapo_harvest'])}\n"
    msg += f"⚡ تولید در ثانیه: {prod:.2f}\n"
    msg += f"📦 ظرفیت: {capacity:,}\n"
    
    if not is_max:
        msg += f"💰 هزینه ارتقا: {price:,} هاپو پوینت"
    else:
        msg += "🏆 مقام نهایی"
    
    keyboard = [
        [InlineKeyboardButton("💰 برداشت", callback_data="hapo_harvest")],
    ]
    
    if is_max:
        keyboard[0].append(InlineKeyboardButton("🏆 نهایی", callback_data="hapo_max"))
    elif game.data["hapo_level"] >= 5 and game.data["hapo_rank"] < 4:
        keyboard.append([InlineKeyboardButton("🌟 ارتقا مقام", callback_data="hapo_rank_up")])
    else:
        keyboard.append([InlineKeyboardButton("⬆️ ارتقا سطح", callback_data="hapo_level_up")])
    
    if game.data["hop_point"] >= 750:
        keyboard.append([InlineKeyboardButton("✏️ تغییر اسم", callback_data="hapo_rename")])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_claw_menu(update: Update, game):
    if game.data["level"] < 2:
        await update.message.reply_text("🔒 پنجه از سطح 2 باز میشود")
        return
    
    if game.data["claw_level"] == 0:
        cost = game.get_claw_cost(1)
        keyboard = [[InlineKeyboardButton(f"🛒 خرید پنجه ({cost} هاپو پوینت)", callback_data="buy_claw")]]
        await update.message.reply_text(
            f"🦞 شما پنجه ندارید\n"
            f"💰 هزینه خرید: {cost} هاپو پوینت\n"
            f"⏳ زمان استراحت: 60:00\n"
            f"🍀 شانس شکار:\n"
            f"  ⚪ معمولی: 95%\n"
            f"  🔵 کمیاب: 5%",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    claw_data = game.get_claw_data(game.data["claw_level"])
    next_level = game.data["claw_level"] + 1
    next_data = game.get_claw_data(next_level)
    
    msg = f"🦞 پنجه شما\n"
    msg += f"⭐ سطح: {game.data['claw_level']}\n"
    msg += f"⏳ زمان استراحت: {claw_data['cooldown']:02d}:00\n"
    msg += f"🍀 شانس شکار:\n"
    msg += f"  ⚪ معمولی: {claw_data['common']}%\n"
    msg += f"  🔵 کمیاب: {claw_data['uncommon']}%\n"
    if claw_data['epic'] > 0:
        msg += f"  🟣 حماسی: {claw_data['epic']}%\n"
    if claw_data['legendary'] > 0:
        msg += f"  🟡 افسانه‌ای: {claw_data['legendary']}%\n"
    
    keyboard = []
    if next_data:
        keyboard.append([InlineKeyboardButton(
            f"⬆️ ارتقا به سطح {next_level} ({next_data['cost']} هاپو پوینت)", 
            callback_data="upgrade_claw"
        )])
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def do_hunt(update: Update, game):
    result = game.do_hunt()
    
    if not result["success"]:
        reason = result.get("reason", "")
        if reason == "خسته‌ام":
            remaining = result.get("remaining", 0)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await update.message.reply_text(f"⏳ تا شکار بعدی {mins}:{secs:02d} مونده")
        else:
            await update.message.reply_text(f"❌ {reason}")
        return
    
    animal = result["animal"]
    msg = f"🏹 شما موفق به شکار شدید!\n"
    msg += f"{animal['emoji']} {animal['name']}\n"
    msg += f"⭐ {animal['rarity_name']}\n"
    msg += f"⚖️ وزن: {animal['weight']} کیلو\n"
    msg += f"💰 ارزش: {animal['value']} هاپو پوینت\n"
    msg += f"🍖 ارزش غذایی: {animal['nutrition']} کالری"
    
    keyboard = [
        [
            InlineKeyboardButton(f"💰 فروش ({animal['value']} هاپو پوینت)", callback_data=f"sell_{animal['value']}"),
            InlineKeyboardButton(f"🍖 به هاپو بده", callback_data=f"feed_{animal['nutrition']}")
        ]
    ]
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_bank_menu(update: Update, game):
    if game.data["level"] < 4:
        await update.message.reply_text("🏦 بانک هاپویی از سطح 4 باز میشود")
        return
    
    if not game.data["bank_opened"]:
        if game.data["hop_point"] < 5000:
            await update.message.reply_text(f"🏦 برای خرید بانک به 5000 هاپو پوینت نیاز داری")
            return
        keyboard = [[InlineKeyboardButton("🏦 خرید بانک (5000 هاپو پوینت)", callback_data="buy_bank")]]
        await update.message.reply_text(
            "🏦 آیا میخوای بانک هاپویی رو بخری؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    game.apply_bank_interest()
    interest = min(int(game.data["bank_balance"] * 0.03), 350000)
    
    msg = f"🏦 بانک هاپویی\n"
    msg += f"👤 {game.data['player_name']}\n"
    msg += f"💰 موجودی: {int(game.data['bank_balance']):,} هاپو پوینت\n\n"
    msg += f"🤑 سود بانکی\n"
    msg += f"📥 سود قابل دریافت: {interest:,} هاپو پوینت\n"
    msg += f"⏳ زمان واریز: 06:00 صبح"
    
    keyboard = [
        [
            InlineKeyboardButton("➕ واریز", callback_data="bank_deposit"),
            InlineKeyboardButton("➖ برداشت", callback_data="bank_withdraw")
        ]
    ]
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_academy(update: Update):
    msg = f"📚 آکادمی هاپویی ✨\n\n"
    msg += f"🐾 جایی که هاپوهای کنجکاو جواب سوال‌هاشون رو پیدا میکنن\n\n"
    msg += f"⭐ سطح کاربران: هرچی سطح بالاتر، پوینت بیشتر\n"
    msg += f"🐕 هاپو: همراه ملوس خودت رو به خونه بیار\n"
    msg += f"🏹 شکار: با پنجه برو شکار\n"
    msg += f"🏦 بانک: پولتو ذخیره کن و سود بگیر"
    
    keyboard = [
        [
            InlineKeyboardButton("⭐ سیستم هاپویی", callback_data="academy_system"),
            InlineKeyboardButton("🐕 راهنمای هاپو", callback_data="academy_hapo")
        ],
        [
            InlineKeyboardButton("🏹 راهنمای شکار", callback_data="academy_hunt"),
            InlineKeyboardButton("🏦 راهنمای بانک", callback_data="academy_bank")
        ]
    ]
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================================================================
# مدیریت Callback (دکمه‌ها)
# ================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    game = get_game(user_id)
    data = query.data
    
    # خرید هاپو
    if data == "buy_hapo":
        result = game.buy_hapo()
        if result["success"]:
            await query.edit_message_text(
                f"✅ هاپو خریداری شد!\n"
                f"اسم هاپو: {result['name']}\n"
                f"برای دیدن منوی هاپو، دستور هاپو رو بزن"
            )
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    # برداشت هاپو
    if data == "hapo_harvest":
        amount = int(game.data["hapo_harvest"])
        if amount > 0:
            game.data["hop_point"] += amount
            game.data["hapo_harvest"] = 0
            game.save_data()
            await query.edit_message_text(f"✅ {amount:,} هاپو پوینت برداشت شد")
        else:
            await query.edit_message_text("❌ هیچ هاپو پوینتی برای برداشت نیست")
        return
    
    # ارتقا سطح هاپو
    if data == "hapo_level_up":
        price = game.get_hapo_upgrade_price()
        if game.data["hop_point"] < price:
            await query.edit_message_text(f"❌ به {price:,} هاپو پوینت نیاز داری")
            return
        game.data["hop_point"] -= price
        game.data["hapo_level"] += 1
        game.data["hapo_food"] = min(game.get_hapo_max_food(), int(game.data["hapo_food"] + 2))
        game.save_data()
        await query.edit_message_text(f"✅ سطح هاپو به {game.data['hapo_level']} ارتقا یافت")
        return
    
    # ارتقا مقام هاپو
    if data == "hapo_rank_up":
        price = game.get_hapo_upgrade_price()
        if game.data["hop_point"] < price:
            await query.edit_message_text(f"❌ به {price:,} هاپو پوینت نیاز داری")
            return
        game.data["hop_point"] -= price
        game.data["hapo_rank"] += 1
        game.data["hapo_level"] = 1
        game.data["hapo_food"] = game.get_hapo_max_food()
        game.data["hapo_harvest"] = 0
        game.save_data()
        await query.edit_message_text(f"✅ مقام هاپو به {RANK_NAMES[game.data['hapo_rank']]} ارتقا یافت")
        return
    
    # تغییر اسم هاپو
    if data == "hapo_rename":
        if game.data["hop_point"] < 750:
            await query.edit_message_text("❌ به 750 هاپو پوینت نیاز داری")
            return
        await query.edit_message_text("✏️ اسم جدید هاپو رو وارد کن")
        context.user_data["waiting_for_hapo_name"] = True
        return
    
    # خرید پنجه
    if data == "buy_claw":
        result = game.buy_claw()
        if result["success"]:
            await query.edit_message_text(
                "✅ پنجه خریداری شد!\n"
                "حالا میتونی با دستور شکار بری شکار"
            )
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    # ارتقا پنجه
    if data == "upgrade_claw":
        result = game.upgrade_claw()
        if result["success"]:
            await query.edit_message_text(f"✅ پنجه به سطح {result['new_level']} ارتقا یافت")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    # فروش حیوان
    if data.startswith("sell_"):
        value = int(data.split("_")[1])
        result = game.sell_animal(value)
        if result["success"]:
            await query.edit_message_text(f"✅ حیوان فروخته شد!\n💰 {value} هاپو پوینت دریافت کردی")
        return
    
    # غذا دادن به هاپو
    if data.startswith("feed_"):
        nutrition = int(data.split("_")[1])
        result = game.feed_hapo(nutrition)
        if result["success"]:
            await query.edit_message_text(f"✅ {result['fed']} غذا به هاپو داده شد")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    # خرید بانک
    if data == "buy_bank":
        result = game.open_bank()
        if result["success"]:
            await query.edit_message_text("🏦 بانک هاپویی خریداری شد!")
        else:
            await query.edit_message_text(f"❌ {result['reason']}")
        return
    
    # واریز به بانک
    if data == "bank_deposit":
        await query.edit_message_text("💰 مبلغ واریزی رو بنویس")
        context.user_data["bank_deposit"] = True
        return
    
    # برداشت از بانک
    if data == "bank_withdraw":
        await query.edit_message_text("💰 مبلغ برداشت رو بنویس")
        context.user_data["bank_withdraw"] = True
        return
    
    # آکادمی
    if data == "academy_system":
        await query.edit_message_text(
            "⭐ سیستم سطوح هاپویی\n\n"
            "هرچی سطح بالاتر، پوینت بیشتری میگیری!\n"
            f"سطح فعلی شما: {game.data['level']}\n\n"
            "با هر بار هاپ هاپ، تجربه میگیری و سطحت بالا میره"
        )
        return
    
    if data == "academy_hapo":
        await query.edit_message_text(
            "🐕 راهنمای هاپو\n\n"
            "هاپو یه همراه نازه که برات هاپو پوینت تولید میکنه!\n"
            "هرچی سطحش بالاتر، تولیدش بیشتره.\n"
            "برای خرید هاپو به سطح 3 و 300 هاپو پوینت نیاز داری."
        )
        return
    
    if data == "academy_hunt":
        await query.edit_message_text(
            "🏹 راهنمای شکار\n\n"
            "با پنجه میتونی بری شکار!\n"
            "حیوانات مختلفی وجود دارن که هرکدوم ارزش متفاوتی دارن.\n"
            "برای شکار به سطح 2 و یک پنجه نیاز داری."
        )
        return
    
    if data == "academy_bank":
        await query.edit_message_text(
            "🏦 راهنمای بانک\n\n"
            "توی بانک میتونی هاپو پوینت‌هات رو ذخیره کنی!\n"
            "هر روز 3% سود به موجودی بانک اضافه میشه.\n"
            "برای باز کردن بانک به سطح 4 و 5000 هاپو پوینت نیاز داری."
        )
        return

# ================================================================
# اجرای اصلی
# ================================================================

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("🤖 بات HopDog اجرا شد!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
