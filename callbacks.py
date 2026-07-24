# callbacks.py - همه هندلرهای کالبک (CallbackQuery) هاپویی

import asyncio
import logging
import traceback
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    JAIL_VOTE_NEEDED, JAIL_VOTE_DURATION, JAIL_DURATION_MEOW,
    JAIL_FINE_MEOW, JAIL_REASON_MEOW, JAIL_DURATION_SPAM,
    JAIL_FINE_SPAM, JAIL_REASON_SPAM, STREET_HAPO_DECISION_TIME,
    STREET_HAPO_COSTS, STREET_HAPO_SUCCESS_CHANCE, STREET_HAPO_MAX_ATTEMPTS,
    STREET_HAPO_REWARD_MIN, STREET_HAPO_REWARD_MAX, STREET_HAPO_FAIL_MESSAGES
)
from globals import get_game, get_street_hapo, refresh_user_cache, clear_user_game
from utils import format_number, get_confirm_keyboard
from logger_config import log_security, log_transaction, log_error
from vote_storage import VoteStorage

# Import از فایل‌های دیگر
from base_handlers import (
    show_rules, my_profile_from_callback, show_jail,
    RULES_PAGE1, RULES_PAGE2, get_user_display_name
)
from hapo_handlers import (
    show_hapo_menu, get_hapo_menu_text, get_hapo_menu_keyboard,
    show_claw_menu, do_hunt, handle_hapo_callback,
    handle_hunt_callback, handle_hapo_feed_fridge,
    show_hapo_feed_menu
)
from fridge_handlers import (
    show_fridge_menu, handle_fridge_buy, handle_fridge_upgrade,
    handle_fridge_back, handle_fridge_item, handle_fridge_cook,
    handle_fridge_sell, handle_fridge_feed, handle_hunt_to_fridge,
    handle_hunt_release, show_smuggle_menu, handle_smuggle_start,
    handle_smuggle_back
)
from bank_handlers import (
    show_bank_menu, handle_bank_callback, handle_transfer_confirm,
    handle_transfer_cancel
)
from admin_handlers import (
    show_leaderboard_main, show_leaderboard_hapo, show_leaderboard_group,
    show_leaderboard_result, reset_user_confirm, reset_user_cancel
)
from academy import (
    show_academy_main, show_academy_system_menu, show_academy_features_menu,
    show_academy_adventure_menu, show_academy_games_menu, show_academy_game_xo,
    show_academy_system_pages, show_academy_animals_pages, show_academy_claw_pages,
    show_feature_page, show_adventure_page, show_street_hapo_page
)
from game_handlers import (
    show_xo_main, handle_xo_set_bet, handle_xo_create,
    handle_xo_join, handle_xo_move, handle_xo_close, handle_xo_cancel
)

logger = logging.getLogger(__name__)


# ================================================================
# هندلر اصلی کالبک
# ================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر اصلی همه کالبک‌ها"""
    try:
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id
        game = get_game(user_id)
        data = query.data
        
        # ======== دکمه‌های غیرفعال ========
        if data == "xo_no_move":
            return
        if data == "street_hapo_ignore":
            return
        
        # ================================================================
        # بازی XO
        # ================================================================
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
        
        # ================================================================
        # پنجه
        # ================================================================
        if data == "buy_claw":
            await handle_hunt_callback(query, game, data, context)
            return
        
        if data == "upgrade_claw":
            await handle_hunt_callback(query, game, data, context)
            return
        
        # ================================================================
        # شکار
        # ================================================================
        if data == "hunt_sell":
            await handle_hunt_callback(query, game, data, context)
            return
        
        if data == "hunt_feed":
            await handle_hunt_callback(query, game, data, context)
            return
        
        if data == "hunt_release":
            await handle_hunt_release(update, context, query)
            return
        
        if data == "hunt_fridge":
            await handle_hunt_to_fridge(update, context, query, "")
            return
        
        if data.startswith("hunt_fridge_"):
            animal_name = data.replace("hunt_fridge_", "")
            await handle_hunt_to_fridge(update, context, query, animal_name)
            return
        
        # ================================================================
        # هاپوی خیابونی
        # ================================================================
        if data == "street_hapo_rescue":
            await handle_street_hapo_rescue(update, context, query)
            return
        
        # ================================================================
        # آکادمی
        # ================================================================
        if data == "academy_back_main":
            await show_academy_main(update, query)
            return
        if data == "academy_system_menu":
            await show_academy_system_menu(update, query)
            return
        if data == "academy_features_menu":
            await show_academy_features_menu(update, query)
            return
        if data == "academy_adventure_menu":
            await show_academy_adventure_menu(update, query)
            return
        if data == "academy_games_menu":
            await show_academy_games_menu(update, query)
            return
        if data == "academy_game_xo":
            await show_academy_game_xo(update, query)
            return
        
        if data.startswith("academy_system_page"):
            page = int(data.replace("academy_system_page", ""))
            await show_academy_system_pages(update, query, page)
            return
        if data.startswith("academy_animals_page"):
            page = int(data.replace("academy_animals_page", ""))
            await show_academy_animals_pages(update, query, page)
            return
        if data.startswith("academy_claw_page"):
            page = int(data.replace("academy_claw_page", ""))
            await show_academy_claw_pages(update, query, page)
            return
        
        if data == "academy_hapo":
            await show_feature_page(update, query, "hapo")
            return
        if data == "academy_hunt":
            await show_feature_page(update, query, "hunt")
            return
        if data == "academy_bank":
            await show_feature_page(update, query, "bank")
            return
        if data == "academy_transfer":
            await show_feature_page(update, query, "transfer")
            return
        if data == "academy_jail":
            await show_feature_page(update, query, "jail")
            return
        if data == "academy_street_hapo":
            await show_street_hapo_page(update, query)
            return
        if data == "academy_fridge":
            await show_feature_page(update, query, "fridge")
            return
        if data == "academy_smuggle":
            await show_feature_page(update, query, "smuggle")
            return
        if data == "academy_leaderboard":
            await show_feature_page(update, query, "leaderboard")
            return
        if data == "academy_hop":
            await show_adventure_page(update, query, "hop")
            return
        if data == "academy_points":
            await show_adventure_page(update, query, "points")
            return
        if data == "academy_exp":
            await show_adventure_page(update, query, "exp")
            return
        if data == "academy_profile":
            await show_adventure_page(update, query, "profile")
            return
        
        # ================================================================
        # قوانین
        # ================================================================
        if data == "rules_page_1":
            await show_rules(update, context, 1)
            return
        if data == "rules_page_2":
            await show_rules(update, context, 2)
            return
        
        # ================================================================
        # لیدربرد
        # ================================================================
        if data == "lb_main":
            await show_leaderboard_main(update, context)
            return
        if data == "lb_hapo":
            await show_leaderboard_hapo(update, context)
            return
        if data == "lb_group":
            await show_leaderboard_group(update, context)
            return
        if data == "lb_back":
            await show_leaderboard_main(update, context)
            return
        if data == "lb_hapo_point":
            await show_leaderboard_result(update, context, "point", group=False, page=0)
            return
        if data == "lb_hapo_hop":
            await show_leaderboard_result(update, context, "hop", group=False, page=0)
            return
        if data == "lb_hapo_street":
            await show_leaderboard_result(update, context, "street", group=False, page=0)
            return
        if data == "lb_hapo_hunt":
            await show_leaderboard_result(update, context, "hunt", group=False, page=0)
            return
        if data == "lb_group_hop":
            await show_leaderboard_result(update, context, "hop", group=True, page=0)
            return
        if data == "lb_group_population":
            await show_leaderboard_result(update, context, "population", group=True, page=0)
            return
        if data == "lb_group_wealth":
            await show_leaderboard_result(update, context, "wealth", group=True, page=0)
            return
        if data == "lb_group_hunt":
            await show_leaderboard_result(update, context, "hunt", group=True, page=0)
            return
        
        if data.startswith("lb_"):
            # صفحه‌بندی لیدربرد
            parts = data.split("_")
            if len(parts) >= 4 and parts[2] == "page":
                category = parts[1]
                page = int(parts[3])
                is_group = category in ["group_hop", "group_population", "group_wealth", "group_hunt"]
                if is_group:
                    cat = category.replace("group_", "")
                    await show_leaderboard_result(update, context, cat, group=True, page=page)
                else:
                    await show_leaderboard_result(update, context, category, group=False, page=page)
            return
        
        # ================================================================
        # ریست کاربر
        # ================================================================
        if data.startswith("rest_confirm_"):
            target_id = data.replace("rest_confirm_", "")
            await reset_user_confirm(update, context, target_id)
            return
        if data == "rest_cancel":
            await reset_user_cancel(update, context)
            return
        
        # ================================================================
        # انتقال
        # ================================================================
        if data.startswith("transfer_confirm_"):
            await handle_transfer_confirm(update, context)
            return
        if data.startswith("transfer_cancel_"):
            await handle_transfer_cancel(update, context)
            return
        
        # ================================================================
        # بانک
        # ================================================================
        if data in ["buy_bank", "bank_deposit", "bank_withdraw", "deposit_confirm",
                    "deposit_cancel", "withdraw_confirm", "withdraw_cancel",
                    "bank_card_to_card", "bank_transactions", "bank_change_card",
                    "bank_change_card_yes", "bank_change_card_no"]:
            await handle_bank_callback(query, game, data, context)
            return
        
        # ================================================================
        # پروفایل
        # ================================================================
        if data == "profile_hide":
            game.data["profile_hidden"] = True
            game.save_data()
            await query.edit_message_text("✅ *پروفایل شما مخفی شد*", parse_mode="Markdown")
            await my_profile_from_callback(query, game)
            return
        if data == "profile_show":
            game.data["profile_hidden"] = False
            game.save_data()
            await query.edit_message_text("✅ *پروفایل شما نمایش داده شد*", parse_mode="Markdown")
            await my_profile_from_callback(query, game)
            return
        if data == "profile_lock":
            game.data["profile_locked"] = True
            game.save_data()
            await query.edit_message_text("✅ *پروفایل شما قفل شد*", parse_mode="Markdown")
            await my_profile_from_callback(query, game)
            return
        if data == "profile_unlock":
            game.data["profile_locked"] = False
            game.save_data()
            await query.edit_message_text("✅ *پروفایل شما باز شد*", parse_mode="Markdown")
            await my_profile_from_callback(query, game)
            return
        
        # ================================================================
        # میو و زندان
        # ================================================================
        if data.startswith("meow_vote_"):
            await handle_meow_vote(update, context, query, data)
            return
        
        if data == "jail_pay_fine":
            await handle_jail_pay_fine(update, context, query, game)
            return
        if data == "jail_pay_fine_yes":
            await handle_jail_pay_fine_yes(update, context, query, game)
            return
        if data == "jail_pay_fine_no":
            await handle_jail_pay_fine_no(update, context, query, game)
            return
        
        # ================================================================
        # یخچال
        # ================================================================
        if data == "buy_fridge":
            await handle_fridge_buy(update, context, query)
            return
        if data == "upgrade_fridge":
            await handle_fridge_upgrade(update, context, query)
            return
        if data == "fridge_back":
            await handle_fridge_back(update, context, query)
            return
        if data.startswith("fridge_item_"):
            index = int(data.replace("fridge_item_", ""))
            await handle_fridge_item(update, context, query, index)
            return
        if data.startswith("fridge_cook_"):
            index = int(data.replace("fridge_cook_", ""))
            await handle_fridge_cook(update, context, query, index)
            return
        if data.startswith("fridge_sell_"):
            index = int(data.replace("fridge_sell_", ""))
            await handle_fridge_sell(update, context, query, index)
            return
        if data.startswith("fridge_feed_"):
            index = int(data.replace("fridge_feed_", ""))
            await handle_fridge_feed(update, context, query, index)
            return
        
        # ================================================================
        # قاچاق
        # ================================================================
        if data.startswith("smuggle_count_"):
            count = data.replace("smuggle_count_", "")
            await handle_smuggle_start(update, context, query, count)
            return
        if data == "smuggle_back":
            await handle_smuggle_back(update, context, query)
            return
        
        # ================================================================
        # هاپو (باید آخرین باشد چون کلی کالبک دارد)
        # ================================================================
        # کالبک‌های هاپو
        hapo_callbacks = [
            "buy_hapo", "hapo_harvest", "hapo_level_up", "hapo_rank_up_confirm",
            "hapo_rank_up_yes", "hapo_rank_up_no", "hapo_rename", "hapo_max",
            "hapo_feed_show", "hapo_back", "cancel_hapo_name"
        ]
        if data in hapo_callbacks:
            await handle_hapo_callback(query, game, data, context)
            return
        
        # کالبک‌های تایید اسم هاپو
        if data.startswith("confirm_hapo_name_"):
            await handle_hapo_callback(query, game, data, context)
            return
        
        # کالبک‌های غذا از یخچال
        if data.startswith("hapo_feed_fridge_"):
            await handle_hapo_feed_fridge(query, game, data, context)
            return
        
        # ================================================================
        # اگر هیچکدام نبود
        # ================================================================
        logger.warning(f"⚠️ کالبک ناشناخته: {data}")
        await query.edit_message_text(
            "❌ *دستور ناشناخته.*\nلطفاً دوباره تلاش کنید.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ Error in handle_callback: {e}")
        logger.error(traceback.format_exc())
        try:
            await query.answer("❌ خطایی رخ داد!", show_alert=True)
        except:
            pass


# ================================================================
# هندلرهای میو و زندان
# ================================================================

async def handle_meow_vote(update: Update, context: ContextTypes.DEFAULT_TYPE, query, data):
    """هندلر رای میو"""
    vote_key = data.replace("meow_vote_", "")
    vote_data = VoteStorage.get_vote(vote_key)
    
    if not vote_data:
        await query.answer("❌ رای‌گیری به پایان رسیده است", show_alert=True)
        return
    
    user_id = update.effective_user.id
    voter_id = user_id
    
    if voter_id == vote_data.get("target_id"):
        await query.answer("❌ نمی‌تونی به خودت رای بدی!", show_alert=True)
        return
    
    if str(voter_id) in vote_data.get("votes", []):
        await query.answer("❌ تو قبلاً رای دادی!", show_alert=True)
        return
    
    vote_data["votes"].append(str(voter_id))
    VoteStorage.save_vote(vote_key, vote_data)
    
    votes_count = len(vote_data.get("votes", []))
    keyboard = [[InlineKeyboardButton("🗳️ رای به زندان", callback_data=f"meow_vote_{vote_key}")]]
    
    await query.edit_message_text(
        f"😱 *یک گربه ی بی ادب!*\nرای بدید که بفرستیمش زندان\n{votes_count}/{JAIL_VOTE_NEEDED}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    await query.answer("✅ رای شما ثبت شد!")
    
    if votes_count >= JAIL_VOTE_NEEDED:
        target_id = vote_data.get("target_id")
        target_game = get_game(target_id)
        target_game.jail_user(JAIL_REASON_MEOW, JAIL_DURATION_MEOW, JAIL_FINE_MEOW)
        log_security(target_id, "زندانی شدن", f"دلیل: {JAIL_REASON_MEOW} - {votes_count} رای")
        
        await query.edit_message_text(
            f"😡 *گربه ی بی ادب!*\n\n✅ *با {votes_count} رای، کاربر به زندان فرستاده شد!*",
            parse_mode="Markdown"
        )
        VoteStorage.delete_vote(vote_key)


async def handle_jail_pay_fine(update: Update, context: ContextTypes.DEFAULT_TYPE, query, game):
    """پرداخت جریمه زندان - نمایش تایید"""
    if not game.is_jailed():
        await query.answer("❌ شما در زندان نیستید", show_alert=True)
        return
    
    fine = game._to_int(game.data.get("jail_fine", 0))
    hop_point = game._to_int(game.data["hop_point"])
    
    if hop_point < fine:
        jail_info = game.get_jail_info()
        remaining = jail_info["remaining"]
        minutes = remaining // 60
        seconds = remaining % 60
        
        msg = f"⛓️ *زندان هاپویی*\n\n"
        msg += f"❌ *پوینت کافی نیست!*\n"
        msg += f"💰 *جریمه:* {format_number(fine)} 🪙\n"
        msg += f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n"
        msg += f"💰 *کمبود:* {format_number(fine - hop_point)} 🪙\n\n"
        msg += f"⏳ *زمان باقی‌مانده:* {minutes:02d}:{seconds:02d}\n\n"
        msg += "💡 *می‌تونی صبر کنی تا آزاد بشی یا:*\n"
        msg += "🏦 *از «بانک هاپویی» برای برداشت پول استفاده کن.*"
        
        await query.edit_message_text(msg, parse_mode="Markdown")
        return
    
    keyboard = get_confirm_keyboard("jail_pay_fine_yes", "jail_pay_fine_no")
    await query.edit_message_text(
        f"⚠️ *آیا از پرداخت جریمه {format_number(fine)} 🪙 مطمئنی؟*\n\n"
        f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n"
        f"💰 *پس از پرداخت:* {format_number(hop_point - fine)} 🪙",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def handle_jail_pay_fine_yes(update: Update, context: ContextTypes.DEFAULT_TYPE, query, game):
    """تایید پرداخت جریمه زندان"""
    result = game.pay_jail_fine()
    if result["success"]:
        await query.edit_message_text("✅ *جریمه پرداخت شد و شما آزاد شدید!* 🎉", parse_mode="Markdown")
        await asyncio.sleep(1)
        await query.message.reply_text(
            "🐶 *به دنیای هاپوها برگشتی!*\n\n💡 *یادت باشه دیگه اسپم نکنی!* 😉",
            parse_mode="Markdown"
        )
    else:
        fine = game._to_int(game.data.get("jail_fine", 0))
        hop_point = game._to_int(game.data["hop_point"])
        jail_info = game.get_jail_info()
        remaining = jail_info["remaining"]
        minutes = remaining // 60
        seconds = remaining % 60
        
        msg = f"❌ *{result['reason']}*\n\n"
        msg += f"💰 *جریمه:* {format_number(fine)} 🪙\n"
        msg += f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n"
        msg += f"⏳ *زمان باقی‌مانده:* {minutes:02d}:{seconds:02d}\n\n"
        msg += "🏦 *برای مدیریت بانک از «بانک هاپویی» استفاده کن.*"
        
        await query.edit_message_text(msg, parse_mode="Markdown")


async def handle_jail_pay_fine_no(update: Update, context: ContextTypes.DEFAULT_TYPE, query, game):
    """لغو پرداخت جریمه زندان"""
    await query.edit_message_text("❌ *پرداخت جریمه لغو شد*", parse_mode="Markdown")
    await asyncio.sleep(1)
    
    jail_info = game.get_jail_info()
    if jail_info:
        remaining = jail_info["remaining"]
        minutes = remaining // 60
        seconds = remaining % 60
        fine = jail_info["fine"]
        reason = jail_info["reason"]
        hop_point = game._to_int(game.data["hop_point"])
        
        msg = f"🐶 *زندان هاپویی* ⛓️\n\n"
        msg += f"📝 *دلیل حبس :* {reason}\n"
        msg += f"⏳ *مدت حبس :* {minutes:02d}:{seconds:02d}\n"
        msg += f"🏦 *جریمه نقدی :* {format_number(fine)} 🪙\n"
        msg += f"💰 *هاپو پوینت هات:* {format_number(hop_point)} 🪙\n"
        
        if hop_point >= fine:
            msg += f"✅ *پوینت کافی برای پرداخت جریمه داری!*\n"
        else:
            msg += f"❌ *پوینت کافی نیست! {format_number(fine - hop_point)} 🪙 کم داری*\n"
        
        msg += f"┘─ میتونید با پرداخت جریمه از زندان آزاد شوید\n\n"
        msg += f"❗️ *دستورات مجاز در زندان:*\n"
        msg += f"┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
        msg += f"┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک\n"
        
        keyboard = [[InlineKeyboardButton("💰 پرداخت جریمه", callback_data="jail_pay_fine")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await query.edit_message_text("🐶 *شما در زندان نیستید! آزاد هستید* 🎉", parse_mode="Markdown")


# ================================================================
# هندلر هاپوی خیابونی
# ================================================================

async def handle_street_hapo_rescue(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """نجات هاپوی خیابونی"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name or f"کاربر{user_id}"
    game = get_game(user_id, username or full_name)
    
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
        await query.message.reply_text(
            "❌ *همه شانس‌ها از دست رفته! هاپوی خیابونی نتونست نجات پیدا کنه...* 😢",
            parse_mode="Markdown"
        )
        return
    
    result = street_hapo.attempt_rescue(user_id, full_name, game)
    
    if result.get("success", False) and result.get("rescued", False):
        street_rescued = game._to_int(game.data.get("street_hapo_rescued", 0))
        
        msg = f"🎉 *{full_name} هاپوی خیابونی رو نجات داد!*\n\n"
        msg += f"💰 *{result['reward']} 🪙 هاپو پوینت جایزه گرفتی!*\n"
        msg += f"🐶 *تعداد هاپوهای نجات داده شده:* {street_rescued}\n\n"
        msg += f"🔄 *تعداد تلاش‌ها:* {result['attempt']}/{STREET_HAPO_MAX_ATTEMPTS}"
        
        keyboard = [[InlineKeyboardButton("🎉 تبریک!", callback_data="street_hapo_ignore")]]
        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
        try:
            await context.bot.send_message(
                user_id,
                f"🎉 *شما یک هاپوی خیابونی رو نجات دادید!*\n"
                f"💰 *{result['reward']} 🪙 به حساب شما واریز شد!*\n"
                f"🐶 *تعداد هاپوهای نجات داده شده:* {street_rescued}",
                parse_mode="Markdown"
            )
        except:
            pass
        
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except:
            pass
        
    elif result.get("died", False):
        msg = f"💀 *{result['message']}*\n\n🔄 *تعداد تلاش‌ها:* {result['attempt']}/{STREET_HAPO_MAX_ATTEMPTS}"
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
        
        msg = f"❌ *{result['message']}*\n\n"
        msg += f"🔄 *تلاش {current_attempt}/{STREET_HAPO_MAX_ATTEMPTS}*\n"
        msg += f"⏳ *زمان باقی‌مونده:* {remaining_time} ثانیه\n"
        
        keyboard = []
        if cost is not None and remaining > 0:
            keyboard.append([InlineKeyboardButton(f"🐶 تلاش مجدد ({cost} 🪙)", callback_data="street_hapo_rescue")])
            msg += f"💰 *هزینه تلاش بعدی:* {cost} 🪙"
        else:
            msg += f"❌ *همه شانس‌ها از دست رفته!*"
        
        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
    else:
        await query.answer(result.get("reason", "خطا!"), show_alert=True)
