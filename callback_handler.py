# handlers.py - هندلرهای پیام و کالبک (نسخه نهایی کامل)

import os
import json
import asyncio
import logging
import random
import traceback
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    ADMIN_PASSWORD, MIN_MEMBERS_TO_STAY, RANK_NAMES, MAX_LEVEL,
    TRANSFER_MIN_AMOUNT, TRANSFER_MAX_AMOUNT, TRANSFER_COOLDOWN,
    TRANSFER_MIN_LEVEL_SENDER, TRANSFER_MIN_LEVEL_RECEIVER,
    BANK_PURCHASE_COST, JAIL_MAX_SPAM_COMMANDS, JAIL_SPAM_WINDOW,
    JAIL_DURATION_SPAM, JAIL_FINE_SPAM, JAIL_REASON_SPAM,
    JAIL_DURATION_MEOW, JAIL_FINE_MEOW, JAIL_REASON_MEOW,
    JAIL_REASON_SMUGGLE, JAIL_DURATION_SMUGGLE, JAIL_FINE_SMUGGLE,
    JAIL_VOTE_DURATION, JAIL_VOTE_NEEDED, HUNT_DECISION_TIMER,
    STREET_HAPO_DECISION_TIME, STREET_HAPO_COSTS, STREET_HAPO_SUCCESS_CHANCE,
    STREET_HAPO_IMAGE_URL, STREET_HAPO_REWARD_MIN, STREET_HAPO_REWARD_MAX,
    STREET_HAPO_FAIL_MESSAGES, STREET_HAPO_MAX_ATTEMPTS, CLAW_IMAGES,
    SMUGGLE_MIN_HAPO, SMUGGLE_MAX_HAPO, SMUGGLE_REQUIRED_LEVEL,
    SMUGGLE_REWARD_MIN, SMUGGLE_REWARD_MAX, FRIDGE_REQUIRED_LEVEL,
    FRIDGE_PURCHASE_COST, FRIDGE_MAX_LEVEL, FRIDGE_CAPACITY,
    FRIDGE_UPGRADE_COSTS, FRIDGE_COOK_MULTIPLIER_SELL, FRIDGE_COOK_MULTIPLIER_FOOD,
    SMUGGLE_TIME_PER_HAPO, LEADERBOARD_MAX_USERS, LEADERBOARD_MAX_GROUPS
)
from game import HopDogGame, StreetHapo
from database import (
    get_user_by_identifier, get_user_by_card, get_all_groups,
    add_group, remove_group, get_user_data, save_user_data, supabase
)
from bank import (
    get_bank_menu_text, get_bank_keyboard, get_change_card_confirm_text,
    get_card_to_card_text, format_number
)
from academy import (
    ACADEMY_MAIN, ACADEMY_SUB_SYSTEM, ACADEMY_SUB_FEATURES, ACADEMY_SUB_ADVENTURE,
    ACADEMY_SYSTEM_PAGE1, ACADEMY_SYSTEM_PAGE2, ACADEMY_SYSTEM_PAGE3, ACADEMY_SYSTEM_PAGE4,
    ACADEMY_ANIMALS_PAGE1, ACADEMY_ANIMALS_PAGE2, ACADEMY_ANIMALS_PAGE3,
    ACADEMY_CLAW_PAGE1, ACADEMY_CLAW_PAGE2, ACADEMY_CLAW_PAGE3,
    ACADEMY_HAPO, ACADEMY_HUNT, ACADEMY_BANK, ACADEMY_TRANSFER, ACADEMY_JAIL, ACADEMY_STREET_HAPO,
    ACADEMY_HOP, ACADEMY_POINTS, ACADEMY_EXP, ACADEMY_PROFILE,
    ACADEMY_FRIDGE, ACADEMY_SMUGGLE, ACADEMY_LEADERBOARD,
    ACADEMY_GAMES, ACADEMY_GAMES_XO, ACADEMY_GAMES_MENU,
    show_academy_main, show_academy_system_menu, show_academy_features_menu,
    show_academy_adventure_menu, show_academy_games_menu, show_academy_game_xo,
    show_academy_system_pages, show_academy_animals_pages, show_academy_claw_pages,
    show_feature_page, show_adventure_page, show_street_hapo_page
)

# ================================================================
# Import بازی‌ها (با GAME_XO_STATE)
# ================================================================

from utils import parse_amount, get_confirm_keyboard, get_game
from game_functions import game_manager
from game_handlers import (
    show_games_menu, show_xo_main, handle_xo_set_bet, process_xo_bet,
    handle_xo_create, handle_xo_join, handle_xo_move,
    handle_xo_close, handle_xo_cancel,
    GAME_XO_STATE
)

# ================================================================
# دیکشنری‌های عمومی
# ================================================================

user_games = {}
SPAM_TRACKER = {}
MEOW_VOTES = {}
TRANSFER_STATE = {}
STREET_HAPO_LAST_SENT = {}
street_hapo_instance = None

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================================================================
# توابع کمکی
# ================================================================


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # ======== پنجه ========
        if data == "buy_claw":
            result = game.buy_claw()
            if result["success"]:
                await query.message.reply_text("✅ *پنجه خریداری شد!*", parse_mode="Markdown")
                await asyncio.sleep(1)
                await show_claw_menu(update, game)
            else:
                await query.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
            return
        
        if data == "upgrade_claw":
            result = game.upgrade_claw()
            if result["success"]:
                await query.message.reply_text(f"✅ *پنجه به سطح {result['new_level']} ارتقا یافت*", parse_mode="Markdown")
                await asyncio.sleep(1)
                await show_claw_menu(update, game)
            else:
                await query.message.reply_text(f"❌ *{result['reason']}*", parse_mode="Markdown")
            return
        
        # ======== هاپوی خیابونی ========
        if data == "street_hapo_rescue":
            await handle_street_hapo_rescue(update, context, query)
            return
        
        # ======== آکادمی ========
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
        
        # ======== قوانین ========
        if data == "rules_page_1":
            await show_rules(update, context, 1)
            return
        if data == "rules_page_2":
            await show_rules(update, context, 2)
            return
        
        # ======== لیدربرد ========
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
        
        # ======== ریست کاربر ========
        if data.startswith("rest_confirm_"):
            target_id = data.replace("rest_confirm_", "")
            await reset_user_confirm(update, context, target_id)
            return
        if data == "rest_cancel_":
            await reset_user_cancel(update, context)
            return
        
        # ======== انتقال ========
        if data.startswith("transfer_confirm_"):
            await handle_transfer_confirm(update, context)
            return
        if data.startswith("transfer_cancel_"):
            await handle_transfer_cancel(update, context)
            return
        
        # ======== واریز و برداشت بانک (تایید/لغو) ========
        if data == "deposit_confirm":
            amount = context.user_data.get("deposit_amount")
            if amount is None:
                await query.edit_message_text("❌ *خطا در واریز. لطفاً دوباره تلاش کن.*", parse_mode="Markdown")
                return
            
            result = game.deposit(amount)
            if result["success"]:
                await query.edit_message_text(
                    f"✅ *{format_number(amount)} هاپو پوینت به بانک واریز شد*\n"
                    f"💰 *موجودی بانک:* {format_number(result['new_balance'])} 🪙",
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
        
        if data == "deposit_cancel":
            await query.edit_message_text("❌ *واریز لغو شد*", parse_mode="Markdown")
            await asyncio.sleep(1)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            context.user_data["deposit_amount"] = None
            return
        
        if data == "withdraw_confirm":
            amount = context.user_data.get("withdraw_amount")
            if amount is None:
                await query.edit_message_text("❌ *خطا در برداشت. لطفاً دوباره تلاش کن.*", parse_mode="Markdown")
                return
            
            result = game.withdraw(amount)
            if result["success"]:
                await query.edit_message_text(
                    f"✅ *{format_number(amount)} هاپو پوینت از بانک برداشت شد*\n"
                    f"💰 *موجودی بانک:* {format_number(result['new_balance'])} 🪙",
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
        
        if data == "withdraw_cancel":
            await query.edit_message_text("❌ *برداشت لغو شد*", parse_mode="Markdown")
            await asyncio.sleep(1)
            msg = get_bank_menu_text(game, False)
            keyboard = get_bank_keyboard(False)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            context.user_data["withdraw_amount"] = None
            return
        
        # ======== بانک ========
        if data == "buy_bank":
            result = game.open_bank()
            if result["success"]:
                await query.edit_message_text(f"🏦 *بانک هاپویی خریداری شد!*\n💳 *شماره کارت شما:* {result['card_number']}", parse_mode="Markdown")
                await asyncio.sleep(2)
                msg = get_bank_menu_text(game, False)
                keyboard = get_bank_keyboard(False)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await query.answer(f"❌ {result['reason']}", show_alert=True)
            return
        
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
        
        if data == "bank_card_to_card":
            await query.edit_message_text(get_card_to_card_text())
            context.user_data["waiting_for_card_to_card"] = True
            return
        
        if data == "bank_transactions":
            msg = get_bank_menu_text(game, True)
            keyboard = get_bank_keyboard(True)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        
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
                await query.edit_message_text(f"✅ *شماره حساب شما تغییر کرد!*\n🔄 *شماره جدید:* {result['new_card']}", parse_mode="Markdown")
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
        
        # ======== یخچال ========
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
        if data == "hunt_fridge":
            animal = game.data.get("current_hunt_animal")
            if not animal:
                await query.edit_message_text("❌ *هیچ حیوانی برای ذخیره وجود ندارد*", parse_mode="Markdown")
                return
            animal_name = animal.get("name")
            await handle_hunt_to_fridge(update, context, query, animal_name)
            return
        
        # ======== قاچاق ========
        if data.startswith("smuggle_count_"):
            count = data.replace("smuggle_count_", "")
            await handle_smuggle_start(update, context, query, count)
            return
        if data == "smuggle_back":
            await show_smuggle_menu(update, game)
            return
        
        # ======== شکار ========
        if data == "hunt_sell":
            hunt_time = game._to_float(game.data.get("hunt_time", 0))
            if hunt_time > 0:
                now = datetime.now().timestamp()
                if (now - hunt_time) > HUNT_DECISION_TIMER:
                    game.data["current_hunt_animal"] = None
                    game.data["hunt_time"] = "0"
                    game.save_data()
                    await query.edit_message_text("🦌 *حیوان فرار کرد!*", parse_mode="Markdown")
                    return
            result = game.sell_animal()
            if result["success"]:
                await query.message.reply_text(f"💰 *حیوان فروخته شد!*\n✅ *{format_number(result['value'])} 🪙 دریافت کردی*", parse_mode="Markdown")
            else:
                await query.answer(f"❌ {result['reason']}", show_alert=True)
            return
        
        if data == "hunt_feed":
            hunt_time = game._to_float(game.data.get("hunt_time", 0))
            if hunt_time > 0:
                now = datetime.now().timestamp()
                if (now - hunt_time) > HUNT_DECISION_TIMER:
                    game.data["current_hunt_animal"] = None
                    game.data["hunt_time"] = "0"
                    game.save_data()
                    await query.edit_message_text("🦌 *حیوان فرار کرد!*", parse_mode="Markdown")
                    return
            result = game.feed_hapo()
            if result["success"]:
                await query.message.reply_text(f"🍖 *{result['fed']} غذا به هاپو داده شد*\n✅ *هاپو سیر شد!*", parse_mode="Markdown")
                return
            error_msg = result["reason"]
            animal = game.data.get("current_hunt_animal")
            if error_msg == "هاپو سیر است" and animal:
                if game._to_float(game.data.get("hunt_time", 0)) > 0:
                    now = datetime.now().timestamp()
                    hunt_time = game._to_float(game.data["hunt_time"])
                    if (now - hunt_time) > HUNT_DECISION_TIMER:
                        game.data["current_hunt_animal"] = None
                        game.data["hunt_time"] = "0"
                        game.save_data()
                        await query.message.reply_text("🦌 *حیوان فرار کرد!*", parse_mode="Markdown")
                        return
                msg = f"❌ *هاپو سیر است!*\n\n"
                msg += f"{animal['emoji']} *{animal['name']}*\n"
                msg += f"⭐ *سطح :* {animal['rarity_name']}\n"
                msg += f"⚖️ *وزن :* {animal['weight']} کیلو\n"
                msg += f"💰 *ارزش فروش :* {format_number(animal['value'])} 🪙\n\n"
                msg += "❗️ *میخوای چیکارش کنی ؟*"
                keyboard = [
                    [InlineKeyboardButton(f"💰 فروش ({format_number(animal['value'])})", callback_data="hunt_sell")]
                ]
                if game.data.get("fridge_owned", False):
                    keyboard.append([InlineKeyboardButton("❄️ بندازش تو یخچال", callback_data="hunt_fridge")])
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return
            await query.answer(f"❌ {error_msg}", show_alert=True)
            return
        
        # ======== پروفایل ========
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
        
        # ======== میو و زندان ========
        if data.startswith("meow_vote_"):
            vote_key = data.replace("meow_vote_", "")
            if vote_key not in MEOW_VOTES:
                await query.answer("❌ رای‌گیری به پایان رسیده است", show_alert=True)
                return
            vote_data = MEOW_VOTES[vote_key]
            voter_id = user_id
            if voter_id == vote_data["target_id"]:
                await query.answer("❌ نمی‌تونی به خودت رای بدی!", show_alert=True)
                return
            if voter_id in vote_data["votes"]:
                await query.answer("❌ تو قبلاً رای دادی!", show_alert=True)
                return
            vote_data["votes"].append(voter_id)
            votes_count = len(vote_data["votes"])
            keyboard = [[InlineKeyboardButton("🗳️ رای به زندان", callback_data=f"meow_vote_{vote_key}")]]
            await query.edit_message_text(f"😱 *یک گربه ی بی ادب!*\nرای بدید که بفرستیمش زندان\n{votes_count}/{JAIL_VOTE_NEEDED}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            await query.answer("✅ رای شما ثبت شد!")
            if votes_count >= JAIL_VOTE_NEEDED:
                target_id = vote_data["target_id"]
                target_game = get_game(target_id)
                target_game.jail_user(JAIL_REASON_MEOW, JAIL_DURATION_MEOW, JAIL_FINE_MEOW)
                await query.edit_message_text(f"😡 *گربه ی بی ادب!*\n\n✅ *با {votes_count} رای، کاربر به زندان فرستاده شد!*", parse_mode="Markdown")
                del MEOW_VOTES[vote_key]
            return
        
        # ======== پرداخت جریمه زندان ========
        if data == "jail_pay_fine":
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
                msg += f"💰 *موجودی شما:* {format_number(hop_point)} 🪙\n"
                msg += f"💰 *کمبود:* {format_number(fine - hop_point)} 🪙\n\n"
                msg += f"⏳ *زمان باقی‌مانده:* {minutes:02d}:{seconds:02d}\n\n"
                msg += "💡 *می‌تونی صبر کنی تا آزاد بشی یا پول جمع کنی و جریمه رو بدی.*\n"
                msg += "🏦 *برای مدیریت بانک از «بانک هاپویی» استفاده کن.*"
                
                await query.edit_message_text(msg, parse_mode="Markdown")
                return
            
            keyboard = get_confirm_keyboard("jail_pay_fine_yes", "jail_pay_fine_no")
            await query.edit_message_text(
                f"⚠️ *آیا از پرداخت جریمه {format_number(fine)} 🪙 مطمئنی؟*\n\n"
                f"💰 *موجودی شما:* {format_number(hop_point)} 🪙\n"
                f"💰 *پس از پرداخت:* {format_number(hop_point - fine)} 🪙",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        if data == "jail_pay_fine_yes":
            result = game.pay_jail_fine()
            if result["success"]:
                await query.edit_message_text("✅ *جریمه پرداخت شد و شما آزاد شدید!* 🎉", parse_mode="Markdown")
                await asyncio.sleep(1)
                await query.message.reply_text(
                    "🐶 *به دنیای هاپوها برگشتی!*\n\n"
                    "💡 *یادت باشه دیگه اسپم نکنی!* 😉",
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
                msg += f"💰 *موجودی شما:* {format_number(hop_point)} 🪙\n"
                msg += f"⏳ *زمان باقی‌مانده:* {minutes:02d}:{seconds:02d}\n\n"
                msg += "🏦 *برای مدیریت بانک از «بانک هاپویی» استفاده کن.*"
                
                await query.edit_message_text(msg, parse_mode="Markdown")
            return
        
        if data == "jail_pay_fine_no":
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
                msg += f"💰 *موجودی شما :* {format_number(hop_point)} 🪙\n"
                
                if hop_point >= fine:
                    msg += f"✅ *پوینت کافی برای پرداخت جریمه داری!*\n"
                else:
                    msg += f"❌ *پوینت کافی نیست! {format_number(fine - hop_point)} 🪙 کم داری*\n"
                
                msg += f"┘─ میتونید با پرداخت جریمه از زندان آزاد شوید\n\n"
                msg += f"❗️ تا زمانی که توی حبس باشید فقط میتوانید از دستورات زیر استفاده کنید:\n"
                msg += f"┘─ `زندان هاپویی` - مشاهده وضعیت زندان\n"
                msg += f"┘─ `بانک هاپویی` یا `هاپو بانک` - مدیریت بانک\n"
                
                keyboard = [[InlineKeyboardButton("💰 پرداخت جریمه", callback_data="jail_pay_fine")]]
                await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            else:
                await query.edit_message_text("🐶 *شما در زندان نیستید! آزاد هستید* 🎉", parse_mode="Markdown")
            return
        
        # ======== هاپو ========
        if data == "confirm_hapo_name":
            new_name = context.user_data.get("new_hapo_name", "")
            if not new_name:
                await query.edit_message_text("❌ *خطا در تغییر اسم*", parse_mode="Markdown")
                return
            
            # ======== پاک‌سازی اسم ========
            new_name = new_name.strip()
            new_name = " ".join(new_name.split())
            logger.info(f"📝 اسم جدید هاپو (پاک شده): '{new_name}'")
            
            hop_point = game._to_int(game.data["hop_point"])
            if hop_point < 750:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *پوینت کافی نیست!*\n💰 نیاز: 750 🪙\n💰 موجودی: {format_number(hop_point)} 🪙\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                context.user_data["new_hapo_name"] = None
                return
            
            old_name = game.data["hapo_name"]
            game.data["hapo_name"] = new_name
            game.data["hop_point"] = str(hop_point - 750)
            game.save_data()
            
            logger.info(f"✅ اسم هاپو از '{old_name}' به '{new_name}' تغییر کرد")
            
            await query.edit_message_text(
                f"✅ *اسم هاپو از «{old_name}» به «{new_name}» تغییر یافت*",
                parse_mode="Markdown"
            )
            context.user_data["new_hapo_name"] = None
            await asyncio.sleep(2)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        if data == "cancel_hapo_name":
            await query.edit_message_text("❌ *تغییر اسم هاپو لغو شد*", parse_mode="Markdown")
            context.user_data["new_hapo_name"] = None
            await asyncio.sleep(1)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        if data == "buy_hapo":
            result = game.buy_hapo()
            if result["success"]:
                await query.edit_message_text(f"✅ *هاپو خریداری شد!*\nاسم هاپو: {result['name']}", parse_mode="Markdown")
                await asyncio.sleep(2)
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *{result['reason']}*\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            return
        
        if data == "hapo_harvest":
            hapo_harvest = game._to_int(game.data["hapo_harvest"])
            if hapo_harvest > 0:
                hop_point = game._to_int(game.data["hop_point"])
                game.data["hop_point"] = str(hop_point + hapo_harvest)
                game.data["hapo_harvest"] = "0"
                game.save_data()
                await query.edit_message_text(f"✅ *{format_number(hapo_harvest)} هاپو پوینت برداشت شد*", parse_mode="Markdown")
                await asyncio.sleep(2)
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *هیچ هاپو پوینتی برای برداشت نیست*\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            return
        
        if data == "hapo_level_up":
            check = game.can_upgrade_level()
            if not check["success"]:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *{check['reason']}*\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                return
            
            price = game.get_hapo_upgrade_price()
            hop_point = game._to_int(game.data["hop_point"])
            if hop_point < price:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *پوینت کافی نیست!*\n💰 نیاز: {format_number(price)} 🪙\n💰 موجودی: {format_number(hop_point)} 🪙\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                return
            
            result = game.upgrade_hapo_level()
            if result["success"]:
                msg = f"✅ *سطح هاپو به {result['new_level']} ارتقا یافت*"
                await query.edit_message_text(msg, parse_mode="Markdown")
                await asyncio.sleep(2)
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *{result['reason']}*\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            return
        
        if data == "hapo_rank_up_confirm":
            check = game.can_rank_up()
            if not check["success"]:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *{check['reason']}*\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                return
            
            price = game.get_hapo_rank_up_price()
            hop_point = game._to_int(game.data["hop_point"])
            if hop_point < price:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *پوینت کافی نیست!*\n💰 نیاز: {format_number(price)} 🪙\n💰 موجودی: {format_number(hop_point)} 🪙\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                return
            
            hapo_rank = game._to_int(game.data["hapo_rank"])
            current_max = game.get_hapo_max_level_for_rank(hapo_rank)
            next_max = game.get_hapo_max_level_for_rank(hapo_rank + 1)
            msg = f"⚠️ *آیا از ارتقا مقام هاپو مطمئنی؟*\n\n"
            msg += f"🌟 *مقام فعلی:* {RANK_NAMES[hapo_rank]}\n"
            msg += f"🌟 *مقام جدید:* {RANK_NAMES[hapo_rank + 1]}\n"
            msg += f"📊 *سقف سطح فعلی:* {current_max}\n"
            msg += f"📊 *سقف سطح جدید:* {next_max}\n"
            msg += f"💰 *هزینه:* {format_number(price)} 🪙"
            await query.edit_message_text(
                msg,
                reply_markup=get_confirm_keyboard("hapo_rank_up_yes", "hapo_rank_up_no"),
                parse_mode="Markdown"
            )
            return
        
        if data == "hapo_rank_up_yes":
            result = game.confirm_rank_up()
            if result["success"]:
                await query.edit_message_text(
                    f"✅ *مقام هاپو به {result['new_rank_name']} ارتقا یافت!*",
                    parse_mode="Markdown"
                )
                await asyncio.sleep(2)
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *{result['reason']}*\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            return
        
        if data == "hapo_rank_up_no":
            await query.edit_message_text("❌ *ارتقا مقام لغو شد*", parse_mode="Markdown")
            await asyncio.sleep(1)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        if data == "hapo_rename":
            hop_point = game._to_int(game.data["hop_point"])
            if hop_point < 750:
                msg = get_hapo_menu_text(game)
                keyboard = get_hapo_menu_keyboard(game)
                await query.edit_message_text(
                    f"❌ *پوینت کافی نیست!*\n💰 نیاز: 750 🪙\n💰 موجودی: {format_number(hop_point)} 🪙\n\n{msg}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                return
            await query.edit_message_text("✏️ *اسم جدید هاپو رو وارد کن:*", parse_mode="Markdown")
            context.user_data["waiting_for_hapo_name"] = True
            return
        
        if data == "hapo_max":
            await query.edit_message_text("🏆 *هاپو در بالاترین سطح است*", parse_mode="Markdown")
            await asyncio.sleep(1)
            msg = get_hapo_menu_text(game)
            keyboard = get_hapo_menu_keyboard(game)
            await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            return
        
    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")
        logger.error(traceback.format_exc())
        try:
            await query.answer("❌ خطایی رخ داد!", show_alert=True)
        except:
            pass

