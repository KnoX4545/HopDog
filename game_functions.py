# game_functions.py - توابع خالص بازی هاپویی (نسخه کامل با اصلاحات)

import random
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)


# ================================================================
# کلاس بازی XO (دوز)
# ================================================================

class GameXO:
    """بازی دوز (XO) با شرط‌بندی هاپو پوینت"""
    
    def __init__(self, host_id: int, host_name: str, bet_amount: int):
        import time
        self.game_id = f"xo-{host_id}-{int(time.time() * 1000)}-{random.randint(100, 999)}"
        self.host_id = str(host_id)
        self.host_name = host_name
        self.bet_amount = bet_amount
        self.player_id = None
        self.player_name = None
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.current_turn = "host"
        self.winner = None
        self.status = "waiting"  # waiting, playing, finished
        self.created_at = datetime.now().timestamp()
        self.last_move_at = datetime.now().timestamp()
        self.host_symbol = "❌"
        self.player_symbol = "⭕"
        self.move_count = 0
        
        logger.info(f"🎮 بازی جدید ساخته شد - game_id: {self.game_id}, میزبان: {host_name}")
    
    def to_dict(self) -> dict:
        """تبدیل به دیکشنری برای ذخیره"""
        return {
            "game_id": self.game_id,
            "host_id": self.host_id,
            "host_name": self.host_name,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "bet_amount": self.bet_amount,
            "board": self.board,
            "current_turn": self.current_turn,
            "winner": self.winner,
            "status": self.status,
            "created_at": self.created_at,
            "last_move_at": self.last_move_at,
            "host_symbol": self.host_symbol,
            "player_symbol": self.player_symbol,
            "move_count": self.move_count
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """ساخت از دیکشنری"""
        game = cls.__new__(cls)
        game.game_id = data.get("game_id")
        game.host_id = data.get("host_id")
        game.host_name = data.get("host_name")
        game.player_id = data.get("player_id")
        game.player_name = data.get("player_name")
        game.bet_amount = data.get("bet_amount", 0)
        game.board = data.get("board", [[" " for _ in range(3)] for _ in range(3)])
        game.current_turn = data.get("current_turn", "host")
        game.winner = data.get("winner")
        game.status = data.get("status", "waiting")
        game.created_at = data.get("created_at", datetime.now().timestamp())
        game.last_move_at = data.get("last_move_at", datetime.now().timestamp())
        game.host_symbol = data.get("host_symbol", "❌")
        game.player_symbol = data.get("player_symbol", "⭕")
        game.move_count = data.get("move_count", 0)
        return game
    
    def add_player(self, player_id: int, player_name: str) -> bool:
        """اضافه کردن بازیکن دوم"""
        if self.status != "waiting":
            logger.warning(f"⚠️ تلاش برای پیوستن به بازی {self.game_id} در حالی که وضعیت {self.status} است")
            return False
        
        if str(player_id) == self.host_id:
            logger.warning(f"⚠️ میزبان {player_id} تلاش کرد به بازی خودش بپیوندد")
            return False
        
        self.player_id = str(player_id)
        self.player_name = player_name
        self.status = "playing"
        self.current_turn = "host"
        self.last_move_at = datetime.now().timestamp()
        
        logger.info(f"✅ بازیکن {player_name} ({player_id}) به بازی {self.game_id} پیوست")
        return True
    
    def make_move(self, user_id: int, row: int, col: int) -> dict:
        """انجام حرکت"""
        if self.status != "playing":
            return {"success": False, "reason": "❌ بازی در حال انجام نیست"}
        
        user_id_str = str(user_id)
        
        # بررسی نوبت
        if self.current_turn == "host" and user_id_str != self.host_id:
            return {"success": False, "reason": "❌ نوبت میزبان است"}
        if self.current_turn == "player" and user_id_str != self.player_id:
            return {"success": False, "reason": "❌ نوبت بازیکن دوم است"}
        
        # بررسی خانه
        if row < 0 or row > 2 or col < 0 or col > 2:
            return {"success": False, "reason": "❌ خانه نامعتبر"}
        if self.board[row][col] != " ":
            return {"success": False, "reason": "❌ این خانه پر است"}
        
        # انجام حرکت
        symbol = self.host_symbol if user_id_str == self.host_id else self.player_symbol
        self.board[row][col] = symbol
        self.move_count += 1
        self.last_move_at = datetime.now().timestamp()
        
        logger.info(f"🎯 حرکت در بازی {self.game_id}: کاربر {user_id} در ({row},{col}) با {symbol}")
        
        # بررسی برنده
        winner = self.check_winner()
        if winner:
            self.winner = winner
            self.status = "finished"
            logger.info(f"🏆 بازی {self.game_id} - برنده: {winner}")
            return {
                "success": True,
                "winner": winner,
                "board": self.board,
                "is_draw": False
            }
        
        # بررسی مساوی
        if self.move_count >= 9:
            self.winner = "draw"
            self.status = "finished"
            logger.info(f"🤝 بازی {self.game_id} مساوی شد")
            return {
                "success": True,
                "winner": "draw",
                "board": self.board,
                "is_draw": True
            }
        
        # تغییر نوبت
        self.current_turn = "player" if self.current_turn == "host" else "host"
        
        return {
            "success": True,
            "winner": None,
            "board": self.board,
            "next_turn": self.current_turn,
            "is_draw": False
        }
    
    def check_winner(self) -> Optional[str]:
        """بررسی برنده"""
        board = self.board
        
        # بررسی سطرها
        for row in range(3):
            if board[row][0] == board[row][1] == board[row][2] != " ":
                return "host" if board[row][0] == self.host_symbol else "player"
        
        # بررسی ستون‌ها
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != " ":
                return "host" if board[0][col] == self.host_symbol else "player"
        
        # بررسی قطرها
        if board[0][0] == board[1][1] == board[2][2] != " ":
            return "host" if board[0][0] == self.host_symbol else "player"
        if board[0][2] == board[1][1] == board[2][0] != " ":
            return "host" if board[0][2] == self.host_symbol else "player"
        
        return None
    
    def get_board_display(self) -> str:
        """نمایش تخته به صورت متن"""
        lines = []
        for row in self.board:
            lines.append(" ┃ ".join(row))
        return "\n━━━┿━━━┿━━━\n".join(lines)
    
    def get_status_text(self) -> str:
        """دریافت متن وضعیت بازی"""
        if self.status == "waiting":
            return "⏳ در انتظار بازیکن دوم..."
        elif self.status == "playing":
            turn_name = self.host_name if self.current_turn == "host" else self.player_name
            turn_symbol = self.host_symbol if self.current_turn == "host" else self.player_symbol
            return f"🎯 نوبت: {turn_name} {turn_symbol}"
        elif self.status == "finished":
            if self.winner == "draw":
                return "🤝 بازی مساوی شد!"
            elif self.winner == "host":
                return f"🏆 {self.host_name} برنده شد!"
            else:
                return f"🏆 {self.player_name} برنده شد!"
        return ""
    
    def get_winner_name(self) -> Optional[str]:
        """دریافت نام برنده"""
        if self.status != "finished" or self.winner == "draw":
            return None
        return self.host_name if self.winner == "host" else self.player_name
    
    def get_player_names(self) -> Tuple[str, str]:
        """دریافت نام بازیکنان"""
        return self.host_name, self.player_name or "در انتظار..."


# ================================================================
# کلاس مدیریت بازی‌ها
# ================================================================

class GameManager:
    """مدیریت همه بازی‌ها"""
    
    def __init__(self):
        self.games: Dict[str, GameXO] = {}
        self.user_games: Dict[str, str] = {}
        self.user_cooldowns: Dict[str, float] = {}
        self.user_game_timeout: Dict[str, float] = {}  # تایم‌اوت بین بازی‌ها
        self.MAX_GAMES = 50
        self.TURN_TIMEOUT = 60  # 60 ثانیه
        self.GAME_COOLDOWN = 120  # 2 دقیقه بین بازی‌ها
        self.CLEANUP_DELAY = 300  # 5 دقیقه بعد از پایان بازی
        
        logger.info("🎮 GameManager راه‌اندازی شد")
        logger.info(f"📊 تنظیمات: حداکثر {self.MAX_GAMES} بازی, تایم‌اوت {self.TURN_TIMEOUT} ثانیه")
    
    # ================================================================
    # توابع کمکی
    # ================================================================
    
    def _to_str(self, value):
        return str(value) if value is not None else ""
    
    def _to_int(self, value, default=0):
        try:
            return int(value) if value is not None else default
        except:
            return default
    
    # ================================================================
    # مدیریت بازی‌ها
    # ================================================================
    
    def create_game(self, host_id: int, host_name: str, bet_amount: int) -> Tuple[bool, str, Optional[GameXO]]:
        """
        ایجاد بازی جدید
        
        Args:
            host_id: آیدی میزبان
            host_name: نام میزبان
            bet_amount: مبلغ شرط
        
        Returns:
            Tuple[bool, str, Optional[GameXO]]: (موفقیت, پیام, بازی)
        """
        host_id_str = str(host_id)
        
        # بررسی محدودیت تعداد بازی‌ها
        if len(self.games) >= self.MAX_GAMES:
            return False, f"❌ تعداد بازی‌های فعال به حداکثر ({self.MAX_GAMES}) رسیده است", None
        
        # بررسی اینکه کاربر در بازی دیگری نیست
        if host_id_str in self.user_games:
            return False, "❌ شما در حال حاضر در یک بازی دیگر هستید", None
        
        # بررسی خنک‌سازی
        on_cooldown, remaining = self.is_on_cooldown(host_id)
        if on_cooldown:
            minutes = remaining // 60
            seconds = remaining % 60
            return False, f"⏳ *به جیبت استراحت بده!*\n💤 {minutes} دقیقه و {seconds} ثانیه دیگه میتونی بازی کنی", None
        
        # بررسی تایم‌اوت بازی قبلی
        if host_id_str in self.user_game_timeout:
            elapsed = datetime.now().timestamp() - self.user_game_timeout[host_id_str]
            if elapsed < 120:  # 2 دقیقه
                remaining = 120 - elapsed
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                return False, f"⏳ *به جیبت استراحت بده!*\n💤 {minutes} دقیقه و {seconds} ثانیه دیگه میتونی بازی کنی", None
        
        # بررسی مبلغ شرط
        if bet_amount < 50:
            return False, f"❌ حداقل مبلغ شرط‌بندی 50 هاپو پوینت است", None
        if bet_amount > 1000000:
            return False, f"❌ حداکثر مبلغ شرط‌بندی 1,000,000 هاپو پوینت است", None
        
        # ایجاد بازی
        game = GameXO(host_id, host_name, bet_amount)
        self.games[game.game_id] = game
        self.user_games[host_id_str] = game.game_id
        self.user_game_timeout[host_id_str] = datetime.now().timestamp()  # ثبت زمان شروع
        
        logger.info(f"✅ بازی ساخته شد - game_id: {game.game_id}, میزبان: {host_name}, مبلغ: {bet_amount}")
        return True, game.game_id, game
    
    def join_game(self, game_id: str, player_id: int, player_name: str) -> Tuple[bool, str, Optional[GameXO]]:
        """
        پیوستن به بازی
        
        Args:
            game_id: آیدی بازی
            player_id: آیدی بازیکن
            player_name: نام بازیکن
        
        Returns:
            Tuple[bool, str, Optional[GameXO]]: (موفقیت, پیام, بازی)
        """
        player_id_str = str(player_id)
        
        # بررسی وجود بازی
        if game_id not in self.games:
            return False, "❌ بازی مورد نظر یافت نشد", None
        
        game = self.games[game_id]
        
        # بررسی وضعیت بازی
        if game.status != "waiting":
            return False, f"❌ این بازی در حال انجام است یا به پایان رسیده (وضعیت: {game.status})", None
        
        # بررسی اینکه کاربر در بازی دیگری نیست
        if player_id_str in self.user_games:
            return False, "❌ شما در حال حاضر در یک بازی دیگر هستید", None
        
        # بررسی اینکه کاربر میزبان نیست
        if str(player_id) == game.host_id:
            return False, "❌ شما میزبان این بازی هستید", None
        
        # بررسی خنک‌سازی برای بازیکن دوم
        on_cooldown, remaining = self.is_on_cooldown(player_id)
        if on_cooldown:
            minutes = remaining // 60
            seconds = remaining % 60
            return False, f"⏳ *به جیبت استراحت بده!*\n💤 {minutes} دقیقه و {seconds} ثانیه دیگه میتونی بازی کنی", None
        
        # بررسی تایم‌اوت بازی قبلی
        if player_id_str in self.user_game_timeout:
            elapsed = datetime.now().timestamp() - self.user_game_timeout[player_id_str]
            if elapsed < 120:
                remaining = 120 - elapsed
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                return False, f"⏳ *به جیبت استراحت بده!*\n💤 {minutes} دقیقه و {seconds} ثانیه دیگه میتونی بازی کنی", None
        
        # اضافه کردن بازیکن
        if not game.add_player(player_id, player_name):
            return False, "❌ خطا در پیوستن به بازی", None
        
        self.user_games[player_id_str] = game_id
        self.user_game_timeout[player_id_str] = datetime.now().timestamp()
        
        logger.info(f"✅ بازیکن {player_name} ({player_id}) به بازی {game_id} پیوست")
        return True, game_id, game
    
    def make_move(self, game_id: str, user_id: int, row: int, col: int) -> dict:
        """
        انجام حرکت در بازی
        
        Args:
            game_id: آیدی بازی
            user_id: آیدی کاربر
            row: ردیف (0-2)
            col: ستون (0-2)
        
        Returns:
            dict: نتیجه حرکت
        """
        if game_id not in self.games:
            return {"success": False, "reason": "❌ بازی یافت نشد"}
        
        game = self.games[game_id]
        result = game.make_move(user_id, row, col)
        
        # اگر بازی تمام شد، کاربران رو از لیست حذف کن
        if result.get("success") and result.get("winner"):
            if game.host_id in self.user_games:
                del self.user_games[game.host_id]
            if game.player_id and game.player_id in self.user_games:
                del self.user_games[game.player_id]
            
            # تنظیم تایم‌اوت برای هر دو بازیکن
            for uid in [game.host_id, game.player_id]:
                if uid:
                    self.user_game_timeout[uid] = datetime.now().timestamp()
            
            logger.info(f"🗑️ بازی {game_id} تمام شد - برنده: {result.get('winner')}")
        
        return result
    
    def get_game(self, game_id: str) -> Optional[GameXO]:
        """دریافت بازی با آیدی"""
        return self.games.get(game_id)
    
    def get_user_game(self, user_id: int) -> Optional[GameXO]:
        """دریافت بازی کاربر"""
        user_id_str = str(user_id)
        if user_id_str in self.user_games:
            game_id = self.user_games[user_id_str]
            if game_id in self.games:
                return self.games[game_id]
            else:
                # بازی حذف شده، پاک کردن از لیست کاربر
                del self.user_games[user_id_str]
        return None
    
    def remove_game(self, game_id: str):
        """حذف بازی"""
        if game_id in self.games:
            game = self.games[game_id]
            
            # تنظیم تایم‌اوت برای کاربران
            for user_id in [game.host_id, game.player_id]:
                if user_id and user_id in self.user_games:
                    del self.user_games[user_id]
                    self.user_game_timeout[user_id] = datetime.now().timestamp()
            
            del self.games[game_id]
            logger.info(f"🗑️ بازی {game_id} حذف شد")
    
    def check_timeout(self):
        """بررسی تایم‌اوت بازی‌ها"""
        now = datetime.now().timestamp()
        to_remove = []
        
        for game_id, game in self.games.items():
            # ======== بازی تمام شده و بیش از ۵ دقیقه گذشته ========
            if game.status == "finished":
                if now - game.last_move_at > self.CLEANUP_DELAY:
                    to_remove.append(game_id)
                    logger.info(f"⏰ بازی {game_id} بعد از {self.CLEANUP_DELAY} ثانیه حذف شد")
                continue
            
            # ======== بازی در حال انجام و ۶۰ ثانیه از آخرین حرکت گذشته ========
            if game.status == "playing":
                if now - game.last_move_at > self.TURN_TIMEOUT:
                    # تعیین بازنده (کسی که نوبتش بوده)
                    loser_id = game.host_id if game.current_turn == "host" else game.player_id
                    winner_id = game.player_id if game.current_turn == "host" else game.host_id
                    
                    game.winner = "player" if game.current_turn == "host" else "host"
                    game.status = "finished"
                    game.last_move_at = now
                    
                    logger.info(f"⏰ بازی {game_id} - بازیکن {loser_id} به خاطر تایم‌اوت ({self.TURN_TIMEOUT} ثانیه) بازنده شد")
                    
                    # حذف از لیست کاربران
                    if game.host_id in self.user_games:
                        del self.user_games[game.host_id]
                    if game.player_id and game.player_id in self.user_games:
                        del self.user_games[game.player_id]
                    
                    # تنظیم تایم‌اوت برای هر دو
                    for uid in [game.host_id, game.player_id]:
                        if uid:
                            self.user_game_timeout[uid] = now
                    
                    to_remove.append(game_id)
            
            # ======== بازی در حال انتظار و بیش از ۵ دقیقه گذشته ========
            if game.status == "waiting":
                if now - game.created_at > self.CLEANUP_DELAY:
                    to_remove.append(game_id)
                    logger.info(f"⏰ بازی {game_id} بعد از {self.CLEANUP_DELAY} ثانیه (بدون بازیکن) حذف شد")
        
        # حذف بازی‌های منقضی شده
        for game_id in to_remove:
            self.remove_game(game_id)
    
    def is_on_cooldown(self, user_id: int) -> Tuple[bool, int]:
        """
        بررسی خنک‌سازی بین بازی‌ها (۲ دقیقه)
        
        Returns:
            Tuple[bool, int]: (در خنک‌سازی است, زمان باقی‌مانده به ثانیه)
        """
        user_id_str = str(user_id)
        if user_id_str not in self.user_cooldowns:
            return False, 0
        
        elapsed = datetime.now().timestamp() - self.user_cooldowns[user_id_str]
        if elapsed < self.GAME_COOLDOWN:
            return True, int(self.GAME_COOLDOWN - elapsed)
        
        return False, 0
    
    def set_cooldown(self, user_id: int):
        """تنظیم خنک‌سازی برای کاربر"""
        self.user_cooldowns[str(user_id)] = datetime.now().timestamp()
        logger.info(f"⏳ خنک‌سازی برای کاربر {user_id} تنظیم شد ({self.GAME_COOLDOWN} ثانیه)")
    
    def get_active_games_count(self) -> int:
        """دریافت تعداد بازی‌های فعال"""
        return len(self.games)
    
    def get_game_stats(self) -> dict:
        """دریافت آمار بازی‌ها"""
        waiting = sum(1 for g in self.games.values() if g.status == "waiting")
        playing = sum(1 for g in self.games.values() if g.status == "playing")
        finished = sum(1 for g in self.games.values() if g.status == "finished")
        
        return {
            "total": len(self.games),
            "waiting": waiting,
            "playing": playing,
            "finished": finished,
            "users": len(self.user_games)
        }
    
    def cleanup_all(self):
        """پاک‌سازی کامل همه بازی‌ها"""
        count = len(self.games)
        self.games.clear()
        self.user_games.clear()
        logger.info(f"🧹 همه {count} بازی پاک شدند")


# ================================================================
# توابع کمکی برای نمایش کیبورد بازی
# ================================================================

def get_xo_board_keyboard(game: GameXO, user_id: int):
    """دریافت کیبورد تخته بازی"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    if not game or not game.game_id:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ خطا", callback_data="xo_no_move")
        ]])
    
    keyboard = []
    user_id_str = str(user_id)
    is_my_turn = False
    
    # بررسی نوبت
    if game.status == "playing":
        if game.current_turn == "host" and user_id_str == game.host_id:
            is_my_turn = True
        elif game.current_turn == "player" and user_id_str == game.player_id:
            is_my_turn = True
    
    # ساخت تخته
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
    
    # وضعیت بازی
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
    
    # دکمه‌های مدیریت
    if game.status == "finished":
        keyboard.append([InlineKeyboardButton("🔙 بستن بازی", callback_data=f"xo-close-{game.game_id}")])
    elif game.status == "waiting" and user_id_str == game.host_id:
        keyboard.append([InlineKeyboardButton("🗑️ لغو میز", callback_data=f"xo-cancel-{game.game_id}")])
    
    return InlineKeyboardMarkup(keyboard)


def get_xo_game_text(game: GameXO) -> str:
    """دریافت متن وضعیت بازی"""
    def format_number(n):
        if n is None:
            return "0"
        try:
            return f"{int(float(n)):,}"
        except:
            return "0"
    
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
    
    # نمایش تخته به صورت گرافیکی
    msg += f"\n┌───┬───┬───┐\n"
    msg += f"│ {game.board[0][0]} │ {game.board[0][1]} │ {game.board[0][2]} │\n"
    msg += f"├───┼───┼───┤\n"
    msg += f"│ {game.board[1][0]} │ {game.board[1][1]} │ {game.board[1][2]} │\n"
    msg += f"├───┼───┼───┤\n"
    msg += f"│ {game.board[2][0]} │ {game.board[2][1]} │ {game.board[2][2]} │\n"
    msg += f"└───┴───┴───┘\n"
    
    # راهنما
    if game.status == "waiting":
        msg += f"\n💡 *برای پیوستن به بازی، روی دکمه «پیوستن» کلیک کن*"
    
    return msg


def get_xo_invite_text(game: GameXO) -> str:
    """دریافت متن دعوتنامه بازی"""
    def format_number(n):
        if n is None:
            return "0"
        try:
            return f"{int(float(n)):,}"
        except:
            return "0"
    
    msg = f"🧩 *یک میز بازی XO ساخته شد!*\n\n"
    msg += f"👤 *میزبان:* {game.host_name}\n"
    msg += f"💰 *مبلغ شرط:* {format_number(game.bet_amount)} 🪙\n\n"
    msg += f"💡 *برای پیوستن، روی دکمه زیر کلیک کن.*"
    
    return msg


def get_xo_winner_text(game: GameXO) -> str:
    """دریافت متن نتیجه بازی"""
    def format_number(n):
        if n is None:
            return "0"
        try:
            return f"{int(float(n)):,}"
        except:
            return "0"
    
    if game.winner == "draw":
        return f"🤝 *بازی مساوی شد!*\n💰 *{format_number(game.bet_amount)} 🪙 به هر بازیکن برگشت*"
    else:
        winner_name = game.host_name if game.winner == "host" else game.player_name
        prize = game.bet_amount * 2
        return f"🏆 *{winner_name} برنده شد!*\n💰 *جایزه:* {format_number(prize)} 🪙"


# ================================================================
# نمونه global برای استفاده در کل پروژه
# ================================================================

game_manager = GameManager()


# ================================================================
# تست
# ================================================================

if __name__ == "__main__":
    # تست GameManager
    print("🧪 تست GameManager...")
    
    manager = GameManager()
    
    # تست ساخت بازی
    success, game_id, game = manager.create_game(123, "آرش", 1000)
    if success:
        print(f"✅ بازی ساخته شد: {game_id}")
        
        # تست پیوستن
        success2, _, game2 = manager.join_game(game_id, 456, "سارا")
        if success2:
            print(f"✅ بازیکن دوم پیوست: {game2.player_name}")
            
            # تست حرکت
            result = manager.make_move(game_id, 123, 0, 0)
            print(f"✅ حرکت میزبان: {result}")
            
            result = manager.make_move(game_id, 456, 1, 1)
            print(f"✅ حرکت بازیکن: {result}")
        else:
            print(f"❌ خطا در پیوستن: {success2}")
    else:
        print(f"❌ خطا در ساخت بازی: {success}")
    
    print("🎉 تست‌ها با موفقیت انجام شد!")
