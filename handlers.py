# handlers.py - فایل اصلی برای import کردن همه چیز

# ================================================================
# Import از base_handlers
# ================================================================

from base_handlers import (
    start,
    help_command,
    show_rules,
    group_welcome,
    handle_admin_login,
    admin_help,
    get_user_display_name,
    get_user_link,
    check_spam,
    my_profile_from_callback,
    do_hop,
    show_jail,
    my_profile,
    show_user_profile,
    handle_meow,
    meow_vote_timer,
    handle_message,
    send_street_hapo_notification,
    RULES_PAGE1,
    RULES_PAGE2
)

# ================================================================
# Import از hapo_handlers
# ================================================================

from hapo_handlers import (
    show_hapo_menu,
    get_hapo_menu_text,
    get_hapo_menu_keyboard,
    show_claw_menu,
    do_hunt,
    hunt_animal_timer,
    show_hapo_feed_menu,
    handle_hapo_rename_input,
    is_valid_hapo_name,
    contains_bad_word,
    handle_hapo_callback,
    handle_hunt_callback,
    handle_hapo_feed_fridge,
    FORBIDDEN_HAPO_NAMES
)

# ================================================================
# Import از fridge_handlers
# ================================================================

from fridge_handlers import (
    show_fridge_menu,
    handle_fridge_buy,
    handle_fridge_upgrade,
    handle_fridge_back,
    handle_fridge_item,
    handle_fridge_cook,
    handle_fridge_sell,
    handle_fridge_feed,
    cook_timer,
    handle_hunt_to_fridge,
    show_smuggle_menu,
    handle_smuggle_start,
    smuggle_timer,
    handle_smuggle_back,
    handle_hunt_release
)

# ================================================================
# Import از bank_handlers
# ================================================================

from bank_handlers import (
    show_bank_menu,
    transfer_points_command,
    process_transfer_amount,
    handle_transfer_confirm,
    handle_transfer_cancel,
    handle_bank_callback,
    process_bank_transaction,
    process_card_to_card
)

# ================================================================
# Import از admin_handlers
# ================================================================

from admin_handlers import (
    set_user_level,
    add_user_level,
    set_user_point,
    add_user_point,
    get_user_info,
    jail_user_command,
    reset_user_command,
    reset_user_confirm,
    reset_user_cancel,
    list_groups,
    admin_street_hapo,
    admin_set_street_hapo,
    admin_add_street_hapo,
    show_leaderboard_main,
    show_leaderboard_hapo,
    show_leaderboard_group,
    show_leaderboard_result,
    get_leaderboard_data,
    get_user_rank,
    LEADERBOARD_MAIN,
    LEADERBOARD_HAPO,
    LEADERBOARD_GROUP
)

# ================================================================
# Import از callbacks
# ================================================================

from callbacks import handle_callback

# ================================================================
# Import از academy
# ================================================================

from academy import (
    show_academy_main,
    show_academy_system_menu,
    show_academy_features_menu,
    show_academy_adventure_menu,
    show_academy_games_menu,
    show_academy_game_xo,
    show_academy_system_pages,
    show_academy_animals_pages,
    show_academy_claw_pages,
    show_feature_page,
    show_adventure_page,
    show_street_hapo_page,
    ACADEMY_MAIN,
    ACADEMY_SUB_SYSTEM,
    ACADEMY_SUB_FEATURES,
    ACADEMY_SUB_ADVENTURE
)

# ================================================================
# Import از game_handlers
# ================================================================

from game_handlers import (
    show_games_menu,
    show_xo_main,
    handle_xo_set_bet,
    process_xo_bet,
    handle_xo_create,
    handle_xo_join,
    handle_xo_move,
    handle_xo_close,
    handle_xo_cancel,
    update_game_message,
    send_game_message,
    remove_game_after_delay,
    restore_game_message
)

# ================================================================
# Import از globals
# ================================================================

from globals import (
    get_game,
    get_street_hapo,
    SPAM_TRACKER,
    MEOW_VOTES,
    TRANSFER_STATE,
    STREET_HAPO_LAST_SENT,
    GAME_XO_STATE,
    GAME_MESSAGES,
    user_games,
    USER_CACHE_TIMESTAMPS,
    USER_CACHE_TTL,
    street_hapo_instance,
    refresh_user_cache,
    clear_user_game,
    get_all_user_games,
    get_user_cache_info,
    clear_all_user_cache,
    save_game_message,
    get_game_message,
    clear_game_message,
    clear_all_game_messages,
    set_xo_state,
    get_xo_state,
    clear_xo_state,
    clear_all_xo_states,
    get_spam_tracker,
    set_spam_tracker,
    clear_spam_tracker,
    clear_all_spam_trackers,
    set_transfer_state,
    get_transfer_state,
    clear_transfer_state,
    clear_all_transfer_states,
    get_street_hapo_last_sent,
    set_street_hapo_last_sent,
    clear_street_hapo_last_sent,
    clear_all_street_hapo_last_sent,
    get_meow_vote,
    set_meow_vote,
    clear_meow_vote,
    clear_all_meow_votes,
    clear_all_caches,
    get_memory_stats
)

# ================================================================
# Import از utils
# ================================================================

from utils import (
    format_number,
    format_duration,
    format_date,
    format_date_persian,
    parse_amount,
    get_confirm_keyboard,
    get_cancel_keyboard,
    get_back_keyboard,
    get_pagination_keyboard,
    generate_random_string,
    generate_card_number,
    generate_game_id,
    generate_vote_key,
    is_valid_amount,
    is_valid_card_number,
    is_valid_username,
    get_time_remaining,
    is_expired,
    get_cooldown_text,
    truncate_text,
    safe_dict,
    safe_int,
    safe_float,
    safe_str,
    get_emoji_rating,
    get_progress_bar,
    bold,
    code,
    italic,
    underline,
    spoiler
)

# ================================================================
# Import از bank
# ================================================================

from bank import (
    get_bank_menu_text,
    get_bank_keyboard,
    get_change_card_confirm_text,
    get_card_to_card_text,
    get_next_interest_time,
    calculate_interest,
    validate_bank_amount,
    validate_card_number,
    log_bank_transaction
)

# ================================================================
# Import از logger_config
# ================================================================

from logger_config import (
    log_transaction,
    log_security,
    log_game,
    log_db,
    log_error,
    log_stats
)

# ================================================================
# Import از database
# ================================================================

from database import (
    get_user_data,
    save_user_data,
    get_user_by_identifier,
    get_user_by_card,
    is_card_unique,
    add_group,
    get_all_groups,
    get_group_stats,
    update_group_stats,
    update_group_member_count,
    update_group_activity,
    remove_group,
    get_user_count,
    get_group_count,
    reset_street_hapo_global,
    get_street_hapo_status,
    set_street_hapo_status,
    save_vote,
    get_vote,
    delete_vote,
    cleanup_expired_votes,
    get_active_votes,
    get_vote_count,
    is_vote_expired,
    get_top_users,
    get_top_groups,
    search_users,
    supabase
)

# ================================================================
# Import از vote_storage
# ================================================================

from vote_storage import (
    VoteStorage,
    create_meow_vote_key,
    create_meow_vote_data,
    is_meow_vote_active,
    get_meow_vote_result,
    get_meow_vote_key_from_data
)

# ================================================================
# Import از game_functions
# ================================================================

from game_functions import (
    game_manager,
    GameXO,
    GameManager,
    get_xo_board_keyboard,
    get_xo_game_text,
    get_xo_invite_text,
    get_xo_winner_text
)

# ================================================================
# Import از game
# ================================================================

from game import HopDogGame

# ================================================================
# Import از game_hapo_extras
# ================================================================

from game_hapo_extras import StreetHapo

# ================================================================
# Import از config
# ================================================================

from config import (
    TOKEN,
    SUPABASE_URL,
    SUPABASE_KEY,
    ADMIN_PASSWORD,
    WEBHOOK_PORT,
    WEBHOOK_URL,
    USE_WEBHOOK,
    BOT_NAME,
    BOT_USERNAME,
    BOT_VERSION,
    BOT_SUPPORT,
    BOT_CHANNEL,
    LEVEL_DATA,
    MAX_LEVEL,
    MIN_LEVEL,
    HAPO_NAMES,
    RANK_NAMES,
    MAX_RANK,
    RANK_UP_PRICES,
    HAPO_CAPACITY,
    HAPO_PRODUCTION,
    HAPO_LEVEL_PRICES,
    HAPO_PURCHASE_COST,
    HAPO_RENAME_COST,
    HAPO_MAX_TOTAL_LEVEL,
    CLAW_DATA,
    MAX_CLAW_LEVEL,
    CLAW_REQUIRED_LEVEL,
    HUNT_REQUIRED_LEVEL,
    CLAW_IMAGES,
    ANIMALS,
    RARITY_NAMES,
    RARITY_COLORS,
    RARITY_EMOJIS,
    HUNT_DECISION_TIMER,
    BANK_REQUIRED_LEVEL,
    BANK_PURCHASE_COST,
    BANK_INTEREST_RATE,
    BANK_MAX_DAILY_INTEREST,
    BANK_INTEREST_HOUR,
    BANK_ACCOUNT_CHANGE_COST,
    BANK_MIN_TRANSFER,
    BANK_MAX_TRANSFER,
    TRANSFER_MIN_AMOUNT,
    TRANSFER_MAX_AMOUNT,
    TRANSFER_COOLDOWN,
    TRANSFER_MIN_LEVEL_SENDER,
    TRANSFER_MIN_LEVEL_RECEIVER,
    TRANSFER_MAX_DAILY,
    JAIL_REASON_SPAM,
    JAIL_REASON_MEOW,
    JAIL_REASON_SMUGGLE,
    JAIL_REASON_ADMIN,
    JAIL_DURATION_SPAM,
    JAIL_DURATION_MEOW,
    JAIL_DURATION_SMUGGLE,
    JAIL_FINE_SPAM,
    JAIL_FINE_MEOW,
    JAIL_FINE_SMUGGLE,
    JAIL_MAX_SPAM_COMMANDS,
    JAIL_SPAM_WINDOW,
    JAIL_VOTE_DURATION,
    JAIL_VOTE_NEEDED,
    JAIL_MEOW_COOLDOWN,
    STREET_HAPO_INTERVAL,
    STREET_HAPO_DECISION_TIME,
    STREET_HAPO_MAX_ATTEMPTS,
    STREET_HAPO_SUCCESS_CHANCE,
    STREET_HAPO_COSTS,
    STREET_HAPO_REWARD_MIN,
    STREET_HAPO_REWARD_MAX,
    STREET_HAPO_FAIL_MESSAGES,
    STREET_HAPO_IMAGE_URL,
    FRIDGE_REQUIRED_LEVEL,
    FRIDGE_PURCHASE_COST,
    FRIDGE_MAX_LEVEL,
    FRIDGE_COOK_TIME_MULTIPLIER,
    FRIDGE_CAPACITY,
    FRIDGE_UPGRADE_COSTS,
    FRIDGE_COOK_MULTIPLIER_SELL,
    FRIDGE_COOK_MULTIPLIER_FOOD,
    SMUGGLE_REQUIRED_LEVEL,
    SMUGGLE_MIN_HAPO,
    SMUGGLE_MAX_HAPO,
    SMUGGLE_TIME_PER_HAPO,
    SMUGGLE_REWARD_MIN,
    SMUGGLE_REWARD_MAX,
    SMUGGLE_JAIL_DURATION,
    SMUGGLE_JAIL_FINE,
    SMUGGLE_SUCCESS_CHANCE,
    SMUGGLE_FAIL_CHANCE,
    GAME_REQUIRED_LEVEL,
    GAME_HOST_REQUIRED_LEVEL,
    GAME_XO_MIN_BET,
    GAME_XO_MAX_BET,
    GAME_TURN_TIMEOUT,
    GAME_COOLDOWN,
    GAME_XO_BOARD_SIZE,
    GAME_MAX_ACTIVE_GAMES,
    GAME_CLEANUP_DELAY,
    LEADERBOARD_MAX_USERS,
    LEADERBOARD_MAX_GROUPS,
    LEADERBOARD_CACHE_TIME,
    MIN_MEMBERS_TO_STAY,
    MAX_GROUPS_PER_USER,
    DEFAULT_LANGUAGE,
    TIMEZONE,
    HOP_MIN_POINTS,
    HOP_MAX_POINTS,
    MAX_HUNT_TIMER,
    MAX_COOK_TIMER,
    MAX_SMUGGLE_TIMER,
    MESSAGES,
    check_config
)

# ================================================================
# توضیحات فایل
# ================================================================

"""
handlers.py - فایل اصلی برای import کردن همه توابع و کلاس‌ها

این فایل فقط به عنوان یک نقطه ورود (Entry Point) برای import کردن
همه توابع از فایل‌های مختلف عمل می‌کند.

فایل‌های اصلی:
- base_handlers.py     : توابع پایه (شروع، راهنما، قوانین، خوش‌آمدگویی)
- hapo_handlers.py     : هندلرهای هاپو، پنجه، شکار
- fridge_handlers.py   : هندلرهای یخچال و قاچاق
- bank_handlers.py     : هندلرهای بانک و انتقال
- admin_handlers.py    : هندلرهای ادمین
- callbacks.py         : همه کالبک‌ها
- game_handlers.py     : هندلرهای بازی XO

برای استفاده:
    from handlers import start, help_command, handle_message, ...
"""

# ================================================================
# تست
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 handlers.py - بررسی importها")
    print("=" * 60)
    
    # لیست توابع اصلی
    functions = [
        "start", "help_command", "handle_message", "handle_callback",
        "show_bank_menu", "show_hapo_menu", "show_fridge_menu",
        "show_leaderboard_main", "set_user_level", "jail_user_command",
        "send_street_hapo_notification", "show_games_menu"
    ]
    
    print("✅ توابع اصلی:")
    for func in functions:
        print(f"  └─ {func}")
    
    print("\n" + "=" * 60)
    print("🎉 handlers.py آماده استفاده است!")
    print("=" * 60)
