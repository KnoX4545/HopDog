# bot.py - فایل اصلی بات تلگرام (نسخه کامل)

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from core import HopDogGame
from data import RARITY_NAMES, RARITY_COLORS, ADMIN_PASSWORD

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")

user_games = {}

def get_game(user_id, username=""):
    if user_id not in user_games:
        user_games[user_id] = HopDogGame(user_id, username)
    return user_games[user_id]

# ================================================================
# پیام‌های خوش‌آمدگویی و راهنما (مو به مو مثل کد اصلی)
# ================================================================

WELCOME_MESSAGE = """🐾 به هاپ داگ خوش اومدی 🐕

⚠️ این بات فقط در گروه‌ها کار می‌کند!
لطفاً بات را به گروه خود اضافه کنید.

دستورات پایه:
🐾 هاپ هاپ - دریافت هاپو پوینت
📊 هاپویی - مشاهده وضعیت
📚 آکادمی - راهنمای کامل

🔒 برای دستورات ادمین، از پیوی بات استفاده کنید."""

ACADEMY_SYSTEM = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : سیستم هاپویی ⚙️
┘─ 📚 مطلب : سطح کاربران 🐾

✨ لیست سطح های موجود کاربران ⬇️

〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 1
┘─ 💰 پوینت : 5 - 15 🪙
┘─ ⏳ زمان : 5:00
┘─ 🔓 قابلیت ها : شروع
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 2
┘─ 🐾 هاپ مورد نیاز : 5
┘─ 💰 پوینت : 10 - 20 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 50 🪙
┘─ 🔓 قابلیت ها : پنجه، شکار
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 3
┘─ 🐾 هاپ مورد نیاز : 15
┘─ 💰 پوینت : 15 - 25 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 225 🪙
┘─ 🔓 قابلیت ها : هاپو
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 4
┘─ 🐾 هاپ مورد نیاز : 40
┘─ 💰 پوینت : 20 - 35 🪙
┘─ ⏳ زمان : 5:00
┘─ 💝 جایزه ارتقا : 500 🪙
┘─ 🔓 قابلیت ها : بانک هاپویی
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 5
┘─ 🐾 هاپ مورد نیاز : 75
┘─ 💰 پوینت : 25 - 40 🪙
┘─ ⏳ زمان : 4:55
┘─ 💝 جایزه ارتقا : 1000 🪙
┘─ 🔓 قابلیت ها : ارتقا بیشتر
〰️〰️〰️〰️〰️〰️〰️
⭐️ سطح 6 تا 20 : ارتقا بیشتر با پوینت‌های بالاتر و زمان کمتر"""

ACADEMY_HAPO = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : قابلیت ها 🔓
┘─ 📚 مطلب : هاپو 🐕

🌘 در میان سایه‌های این دنیای مرموز، هیچ‌چیز دلگرم‌کننده‌تر از صدای خُرخُر یک همدم کوچک نیست…

🐕 وقت آن رسیده که صاحب یک هاپو اختصاصی بشی !
😻 برای اینکه همراه ملوس خودت رو به خونه بیاری، کافیه بگی هاپو

💫 از اون لحظه به بعد، هاپو تو شروع میکنه به تولید جادوییِ 🪙 هاپو پوینت ! حتی وقتی تو خوابی، اون هر ثانیه براشون زحمت میکشه
┘─ 🔺 مثلاً یک هاپو سطح 1 در هر ثانیه 0.1 🪙 هاپو پوینت تولید میکنه

❗️ اما نگهداری از این موجودات ناز، مسئولیت‌هایی هم داره ⬇️

- 🍖 شکم گرسنه، هاپ هاپ نمیکنه
┘─ ⚡️ هاپو تو برای کار کردن به انرژی نیاز داره. اگه شکمش خالی بشه، تولید پوینت رو متوقف میکنه.
  ┘─ 😋 چطوری سیرش کنی ؟ با همون حیواناتی که از جنگل شکار کردی ! 🐾 هر وعده غذا، هاپو تو رو تا 2 ساعت سرحال و پرانرژی نگه میداره.

- 📦 ظرفیت محدود
┘─ 💰 هاپوها جعبه کوچیکی برای جمع‌آوری پوینت‌ها دارن. اگه ظرفیت هاپوت پر بشه، دیگه پوینتی اضافه نمیشه تا زمانی که سر بزنی و پوینت‌های جمع‌شده رو از توی جعبه برداری. 🐾

✨ رشد و فراتر از آن
- ⭐️ با بالاتر بردن سطح هاپو، سرعت تولید پوینت و ظرفیت نگهداری اون بیشتر میشه.
- 🌟 اما هر 5 سطح، هاپو تو به یک تحول بزرگ نیاز داره : ارتقا مقام !
┘─ ❗️ وقتی مقام هاپوت رو بالا میبری، سطح و پوینت‌های داخل جعبش صفر میشه، اما در عوض ⬇️
  ┘─ 1️⃣ سقف سطح‌های بعدی 5 تا بیشتر میشه (مثلاً تا سطح 10 باز میشه)
  ┘─ 2️⃣ حجم شکم هاپوت بزرگتر میشه و میتونه غذای بیشتری رو برای مدت طولانی‌تر ذخیره کنه

💕 یک اسم، یک هویت
- 😺 هاپو تو لایق یک نامِ زیباست. میتونی براش اسم انتخاب کنی و از اون به بعد، به جای کلمه عمومی، با اسم خودش صداش بزنی !

✨ همین حالا هاپو خودت رو بخر، براش حیوان شکار کن و شاهد رشد سرمایه 🪙 خودت باش

❗️ سطح مورد نیاز جهت خرید هاپو : 3"""

ACADEMY_HUNT = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : قابلیت ها 🔓
┘─ 📚 مطلب : شکار هاپویی 🏹

✨ در کنار جنگل‌های اسرارآمیز این جهان، هاپوهای گرسنه و ماجراجو به چیزی بیشتر از یک صدا نیاز دارن…

😻 وقتشه مهارت جدیدی رو امتحان کنی : شکار

😽 برای شروع این ماجراجویی، اول از همه باید بگی پنجه تا یک پنجه سطح 1 برای خودت بخری
🐾 بعد از اون، کافیه بگی شکار تا پنجه‌ات رو بندازی توی جنگل تا ببینی چه صید شگفت‌انگیزی انتظارت رو میکشه !

⌛️ وقتی حیوان رو شکار کردی، فقط 60 ثانیه فرصت داری تا یک تصمیم مهم بگیری ⬇️
- 🪙 میتونی اون رو بفروشی و جیبت رو پر از 🪙 هاپو پوینت کنی
- 🍖 یا اگه یک هاپوی ملوس داری، اون رو به عنوان غذا به هاپوت بدی تا شکمش پر شه !

🦞 هر زمان که دوباره بگی پنجه، میتونی سطح پنجه‌ات رو ببینی و اگه خواستی اون رو ارتقا بدی و قوی‌ترش کنی.

⭐️ هر حیوان برای خودش سطح و همچنین وزن ⚖️ خاص داره. اگه شانس باهات یار باشه و یه حیوان کمیاب و حسابی سنگین به تور بندازی، قیمت فروشش سر به فلک میکشه

⌛️ ولی خب، شکارچی بودن کار خسته‌کننده‌ای‌ست و بعد از هر بار شکار، به کمی استراحت ⚡️ نیاز داری تا دوباره انرژی بگیری.

😺 خبر خوب اینجاست که برای کم کردن زمان استراحت و سریع‌تر شکار کردن، یه راه عالی داری ⬇️
1️⃣ پنجه‌ات رو به سطح‌های بالاتر ارتقا بدی 🌟

😼 پس منتظر چی هستی شکارچی ؟
✨ همین حالا پنجه‌ات رو بخر و بزرگترین حیوان دنیای هاپوها رو صید کن

❗️ سطح مورد نیاز جهت شکار : 2"""

ACADEMY_BANK = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : قابلیت ها 🔓
┘─ 📚 مطلب : بانک هاپویی 🏦

🌘 در قلب پر هیاهوی شهر هاپوها، ساختمانی امن و باشکوه وجود داره؛ جایی که میتونی ثروتت رو از خرج شدن بی‌موقع دور نگه داری و بذاری آروم‌آروم رشد کنه.

🏦 به بانک هاپویی خوش اومدی.
✨ اگر میخوای وارد سیستم بانکی بشی، کافیه بنویسی: بانک هاپویی یا هاپو بانک

┘─ ❗️ برای استفاده از بانک، باید حداقل سطح 4 باشی و همچنین باید بانک رو با هزینه 5,000 🪙 خریداری کنی.
┘─ 💰 پولی که واریز میکنی از هاپو پوینت‌های قابل استفاده‌ات کم میشه و تا وقتی برداشت نکنی قابل خرج کردن نیست.

🤑 سود بانکی
┘─ 🛍 هر روز ساعت 06:00، معادل 3٪ از موجودی بانک به حساب بانکی‌ات اضافه میشه.
┘─ 📥 حداکثر سود روزانه 350,000 هاپو پوینت هست؛ حتی اگر موجودی بانک خیلی بیشتر بشه.
┘─ 💰 هرچقدر موجودی بانک بیشتر باشه، سود دریافتی بیشتر خواهد بود.

🐾 با بانک هاپویی، هاپو پوینت‌هات رو امن نگه دار و بذار خودشون رشد کنن."""

ACADEMY_HOP = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾
┘─ 📚 مطلب : هاپ هاپ 🐾

🌘 در این دنیای بزرگ ، هر هاپوی نازی برای زنده موندن باید اول از همه یک کار مهم انجام بده…
🐾 باید هاپ هاپ کنه !

هر بار که یک هاپو توی این جهان هاپ هاپ کنه ، مقداری 🪙 هاپو پوینت دریافت میکنه.
💰 هاپو پوینت همون ارز ارزشمند دنیای هاپوهاست که با اون میتونی قوی‌تر بشی و در مسیر رشد قدم برداری. ✨

اما حواست باشه…
هر هاپو بعد از هر بار هاپ کردن ، به کمی استراحت نیاز داره ⌛️
چون حتی نازترین هاپوها هم برای ادامه ماجراجویی باید نفسی تازه کنن.

خبر خوب اینجاست که اگه خودت سطح بیشتری داشته باشی ، نیاز به استراحت کمتری داری ⌛️
و میتونی خیلی سریعتر دوباره هاپ هاپ کنی ⚡️

از طرفی اگه میخای با هر بار هاپ کردن ، هاپو پوینت بیشتری به دست بیاری ،
باید سطح خودت رو بالاتر ببری 🌟
هرچی قوی‌تر بشی ، پاداش بیشتری هم دریافت میکنی.

پس منتظر چی هستی ؟ 😼
✨ همین حالا هاپ هاپ کن و قدم به دنیای شگفت‌انگیز هاپوها بزار 🐾"""

ACADEMY_POINTS = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾
┘─ 📚 مطلب : هاپو پوینت 🪙

🪙 هاپو پوینت ارز با ارزش دنیای هاپوهاست 🐾
🐈 هرچی بیشتر ازین ارز داشته باشی بیشتر بهت احترام گذاشته میشه و قدرت بیشتری توی دنیای هاپوها داری !

💫 راه های زیادی برای به دست آوردن این ارز وجود داره از جمله ابتدایی ترینشون یعنی هاپ هاپ کردن 🐾
😽 ولی از طرفی هم راه های زیادی برای خرج کردنشون وجود داره مثلا خرید اولین هاپوی گوگولی خودت و...

📚 مطمئن شو قبل از استفاده ازین ارز با ارزش با زدن آکادمی تمامی قوانین مهم دنیای هاپوها رو مطالعه کنی ❤️"""

ACADEMY_EXP = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾
┘─ 📚 مطلب : تجربه و سطح ⭐️

💫 همه ی هاپوها از سطح 1 شروع میکنن و به مرور زمان , با کسب تجربه سطح خودشون رو ارتقا میدن ✨

⭐️ برای کسب تجربه و رسیدن به سطح بعدی (ارتقا سطح) باید مقدار مشخصی هاپ هاپ کنی 🐾
🐾 هر هاپ هاپ ثبت شده برای شما , یک تجربه به حساب میاد

💝 هربار که سطحت ارتقا پیدا کنه , جوایز خفن مانند 🪙 هاپو پوینت دریافت میکنی…
✨ و همچنین با رسیدن به سطح های بالاتر , قابلیت ها و امکانات تازه ای برات باز میشه

🐾 میتونی با نوشتن هاپویی پروفایل هاپویی خودت رو مشاهده کنی و سطح کنونی خودت و همچنین تعداد باقی مونده هاپ هات تا رسیدن به سطح بعدی رو ببینی"""

ACADEMY_PROFILE = """📚 آکادمی هاپویی ✨
┘─ 🐾 بخش : شروع ماجراجویی 🐾
┘─ 📚 مطلب : پروفایل هاپویی 🪪

🐈 هر هاپوی ناز و گوگولی یه هویت خاص برای خودش داره ✨

🪪 توی پروفایل هاپویی میتونی اطلاعات دقیق خودت رو مشاهده کنی !
🐾 مثلا تعداد هاپ هاپ هاتون یا 🪙 هاپو پوینت هاتون و یا ⭐️ سطحتون و...

🐱 برای مشاهده پروفایل هاپویی خودت بنویس هاپویی"""

# ================================================================
# دستورات
# ================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"کاربر{user_id}"
    game = get_game(user_id, username)
    
    # فقط یک بار پیام خوش‌آمدگویی
    if not game.data.get("has_seen_welcome", False):
        game.data["has_seen_welcome"] = True
        game.save_data()
        await update.message.reply_text(WELCOME_MESSAGE)
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
    username = update.effective_user.username or f"کاربر{user_id}"
    game = get_game(user_id, username)
    text = update.message.text.strip()
    text_lower = text.lower()
    is_private = update.message.chat.type == "private"
    
    # ======== دستور ادمین (فقط در پیوی) ========
    if text_lower == "kknoxx1":
        if not is_private:
            return  # در گروه هیچ کاری نکن
        await update.message.reply_text("🔑 رمز ادمین را وارد کن:")
        context.user_data["waiting_for_admin"] = True
        return
    
    if context.user_data.get("waiting_for_admin", False):
        if not is_private:
            context.user_data["waiting_for_admin"] = False
            return
        if text == ADMIN_PASSWORD:
            game.data["is_admin"] = True
            game.save_data()
            await update.message.reply_text("✅ شما ادمین شدید! 🛡️")
            await update.message.reply_text(
                "دستورات ادمین:\n"
                "setlevel [عدد] - تغییر سطح\n"
                "setpoint [عدد] - تغییر پوینت"
            )
        else:
            await update.message.reply_text("❌ رمز اشتباه است")
        context.user_data["waiting_for_admin"] = False
        return
    
    # ======== دستورات ادمین (فقط در پیوی) ========
    if text_lower.startswith("setlevel") or text_lower.startswith("setpoint"):
        if not is_private:
            return
        if not game.data.get("is_admin", False):
            await update.message.reply_text("❌ شما ادمین نیستید")
            return
        
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ فرمت: setlevel [عدد] یا setpoint [عدد]")
            return
        
        try:
            value = int(parts[1])
            if text_lower.startswith("setlevel"):
                if 1 <= value <= 20:
                    game.data["level"] = value
                    await update.message.reply_text(f"✅ سطح به {value} تغییر یافت")
                else:
                    await update.message.reply_text("❌ سطح باید بین 1 تا 20 باشد")
            else:
                game.data["hop_point"] = value
                await update.message.reply_text(f"✅ پوینت به {value} تغییر یافت")
            game.save_data()
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد وارد کن")
        return
    
    # ======== دستورات اصلی (فقط در گروه) ========
    if not is_private:
        # دستور هاپ هاپ
        if text_lower in ["هاپ هاپ", "هاپ", "hop", "هاپ هوپ", "هوپ"]:
            result = game.do_hop()
            if not result["success"]:
                remaining = result.get("remaining", 0)
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                await update.message.reply_text(
                    f"⏳ هنوز هاپت نمیاد ...\n"
                    f"باید {mins}:{secs:02d} صبر کنی"
                )
                return
            
            msg = f"🐾 {result['earned']} هاپو پوینت گرفتی ✨\n"
            msg += f"💰 هاپو پوینت‌هات : {int(game.data['hop_point'])}"
            
            if result.get("level_up"):
                msg += f"\n\n🎉 سطح شما به {result['new_level']} ارتقا یافت!\n"
                msg += f"🎁 جایزه: {result['reward']} هاپو پوینت"
            
            await update.message.reply_text(msg)
            return
        
        # دستور هاپویی
        if text_lower in ["هاپویی", "hapui", "وضعیت", "پروفایل"]:
            required = game.get_required_for_level(game.data["level"])
            msg = f"📊 وضعیت هاپویی شما\n"
            msg += f"👤 کاربر: {game.data['player_name']}\n"
            if game.data.get("is_admin", False):
                msg += "🛡️ [ادمین]\n"
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
        
        # تغییر اسم (فقط در گروه)
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
        
        # ======== دستور اشتباه ========
        # هیچ کاری نکن (سکوت کامل)
        return
    
    else:
        # ======== در پیوی ========
        # فقط دستورات ادمین و کمک
        if text_lower in ["start", "/start"]:
            await update.message.reply_text(
                "🐾 این بات فقط در گروه‌ها کار می‌کند!\n"
                "لطفاً بات را به گروه خود اضافه کنید.\n\n"
                "برای دستورات ادمین از دستور kknoxx1 استفاده کنید."
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
    keyboard = [
        [
            InlineKeyboardButton("⭐ سیستم هاپویی", callback_data="academy_system"),
            InlineKeyboardButton("🐕 راهنمای هاپو", callback_data="academy_hapo")
        ],
        [
            InlineKeyboardButton("🏹 راهنمای شکار", callback_data="academy_hunt"),
            InlineKeyboardButton("🏦 راهنمای بانک", callback_data="academy_bank")
        ],
        [
            InlineKeyboardButton("🐾 هاپ هاپ", callback_data="academy_hop"),
            InlineKeyboardButton("🪙 هاپو پوینت", callback_data="academy_points")
        ],
        [
            InlineKeyboardButton("⭐ تجربه و سطح", callback_data="academy_exp"),
            InlineKeyboardButton("🪪 پروفایل", callback_data="academy_profile")
        ]
    ]
    
    await update.message.reply_text(
        "📚 آکادمی هاپویی ✨\n\n🐾 جایی که هاپوهای کنجکاو جواب سوال‌هاشون رو پیدا میکنن\n\nلطفا بخش مورد نظر را انتخاب کنید ⬇️",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================================================================
# مدیریت Callback
# ================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username or f"کاربر{user_id}"
    game = get_game(user_id, username)
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
    
    # ======== آکادمی ========
    if data == "academy_system":
        await query.edit_message_text(ACADEMY_SYSTEM)
        return
    
    if data == "academy_hapo":
        await query.edit_message_text(ACADEMY_HAPO)
        return
    
    if data == "academy_hunt":
        await query.edit_message_text(ACADEMY_HUNT)
        return
    
    if data == "academy_bank":
        await query.edit_message_text(ACADEMY_BANK)
        return
    
    if data == "academy_hop":
        await query.edit_message_text(ACADEMY_HOP)
        return
    
    if data == "academy_points":
        await query.edit_message_text(ACADEMY_POINTS)
        return
    
    if data == "academy_exp":
        await query.edit_message_text(ACADEMY_EXP)
        return
    
    if data == "academy_profile":
        await query.edit_message_text(ACADEMY_PROFILE)
        return

# ================================================================
# Handle messages for bank deposit/withdraw
# ================================================================

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"کاربر{user_id}"
    game = get_game(user_id, username)
    text = update.message.text.strip()
    
    # تغییر اسم هاپو
    if context.user_data.get("waiting_for_hapo_name", False):
        if game.data["hop_point"] < 750:
            await update.message.reply_text("❌ پوینت کافی نیست")
            context.user_data["waiting_for_hapo_name"] = False
            return
        game.data["hapo_name"] = text
        game.data["hop_point"] -= 750
        game.save_data()
        await update.message.reply_text(f"✅ اسم هاپو به {text} تغییر یافت")
        context.user_data["waiting_for_hapo_name"] = False
        return
    
    # واریز به بانک
    if context.user_data.get("bank_deposit", False):
        try:
            amount = int(text.replace(",", ""))
            result = game.deposit(amount)
            if result["success"]:
                await update.message.reply_text(f"✅ {amount:,} هاپو پوینت به بانک واریز شد\n💰 موجودی: {result['new_balance']:,}")
            else:
                await update.message.reply_text(f"❌ {result['reason']}")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        context.user_data["bank_deposit"] = False
        return
    
    # برداشت از بانک
    if context.user_data.get("bank_withdraw", False):
        try:
            amount = int(text.replace(",", ""))
            result = game.withdraw(amount)
            if result["success"]:
                await update.message.reply_text(f"✅ {amount:,} هاپو پوینت از بانک برداشت شد\n💰 موجودی: {result['new_balance']:,}")
            else:
                await update.message.reply_text(f"❌ {result['reason']}")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن")
        context.user_data["bank_withdraw"] = False
        return

# ================================================================
# اجرای اصلی
# ================================================================

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    print("🤖 بات HopDog اجرا شد!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
