# handlers_common.py - توابع مشترک بین همه هندلرها

from game import HopDogGame, StreetHapo
from database import get_user_data

user_games = {}
street_hapo_instance = None
GAME_XO_STATE = {}


def get_game(user_id, username=""):
    if user_id not in user_games:
        user_games[user_id] = HopDogGame(user_id, username)
    return user_games[user_id]


def get_street_hapo():
    global street_hapo_instance
    if street_hapo_instance is None:
        street_hapo_instance = StreetHapo()
    return street_hapo_instance


def get_user_display_name(user_id, username="", full_name=""):
    if full_name and full_name.strip() and not full_name.startswith("کاربر"):
        return full_name
    if username and username.strip():
        return f"@{username}"
    return f"کاربر{user_id}"
