# games.py - منطق بازی‌ها (XO - دوز)

import random
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)

# ================================================================
# کلاس بازی XO
# ================================================================

class GameXO:
    """بازی دوز (XO) با شرط‌بندی هاپو پوینت"""
    
    def __init__(self, host_id: int, host_name: str, bet_amount: int):
        self.game_id = f"xo_{host_id}_{int(datetime.now().timestamp())}"
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
    
    def to_dict(self) -> dict:
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
            return False
        if str(player_id) == self.host_id:
            return False
        self.player_id = str(player_id)
        self.player_name = player_name
        self.status = "playing"
        self.current_turn = "host"
        self.last_move_at = datetime.now().timestamp()
        return True
    
    def make_move(self, user_id: int, row: int, col: int) -> dict:
        """انجام حرکت"""
        if self.status != "playing":
            return {"success": False, "reason": "بازی در حال انجام نیست"}
        
        user_id_str = str(user_id)
        
        if self.current_turn == "host" and user_id_str != self.host_id:
            return {"success": False, "reason": "نوبت میزبان است"}
        if self.current_turn == "player" and user_id_str != self.player_id:
            return {"success": False, "reason": "نوبت بازیکن دوم است"}
        
        if row < 0 or row > 2 or col < 0 or col > 2:
            return {"success": False, "reason": "خانه نامعتبر"}
        if self.board[row][col] != " ":
            return {"success": False, "reason": "این خانه پر است"}
        
        symbol = self.host_symbol if user_id_str == self.host_id else self.player_symbol
        self.board[row][col] = symbol
        self.move_count += 1
        self.last_move_at = datetime.now().timestamp()
        
        winner = self.check_winner()
        if winner:
            self.winner = winner
            self.status = "finished"
            return {
                "success": True,
                "winner": winner,
                "board": self.board,
                "is_draw": False
            }
        
        if self.move_count >= 9:
            self.winner = "draw"
            self.status = "finished"
            return {
                "success": True,
                "winner": "draw",
                "board": self.board,
                "is_draw": True
            }
        
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
        
        for row in range(3):
            if board[row][0] == board[row][1] == board[row][2] != " ":
                return "host" if board[row][0] == self.host_symbol else "player"
        
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != " ":
                return "host" if board[0][col] == self.host_symbol else "player"
        
        if board[0][0] == board[1][1] == board[2][2] != " ":
            return "host" if board[0][0] == self.host_symbol else "player"
        if board[0][2] == board[1][1] == board[2][0] != " ":
            return "host" if board[0][2] == self.host_symbol else "player"
        
        return None
    
    def get_board_display(self) -> str:
        """نمایش تخته"""
        lines = []
        for row in self.board:
            lines.append(" ┃ ".join(row))
        return "\n━━━┿━━━┿━━━\n".join(lines)
    
    def get_status_text(self) -> str:
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


# ================================================================
# کلاس مدیریت بازی‌ها
# ================================================================

class GameManager:
    """مدیریت همه بازی‌ها"""
    
    def __init__(self):
        self.games: Dict[str, GameXO] = {}
        self.user_games: Dict[str, str] = {}
        self.user_cooldowns: Dict[str, float] = {}
    
    def create_game(self, host_id: int, host_name: str, bet_amount: int) -> Tuple[bool, str, Optional[GameXO]]:
        """ایجاد بازی جدید"""
        host_id_str = str(host_id)
        
        if len(self.games) >= 50:
            return False, "تعداد بازی‌های فعال به حداکثر رسیده است", None
        
        if host_id_str in self.user_games:
            return False, "شما در حال حاضر در یک بازی دیگر هستید", None
        
        if bet_amount < 50:
            return False, f"حداقل مبلغ شرط‌بندی {50} هاپو پوینت است", None
        if bet_amount > 1000000:
            return False, f"حداکثر مبلغ شرط‌بندی {1000000} هاپو پوینت است", None
        
        game = GameXO(host_id, host_name, bet_amount)
        self.games[game.game_id] = game
        self.user_games[host_id_str] = game.game_id
        return True, game.game_id, game
    
    def join_game(self, game_id: str, player_id: int, player_name: str) -> Tuple[bool, str, Optional[GameXO]]:
        """پیوستن به بازی"""
        player_id_str = str(player_id)
        
        if game_id not in self.games:
            return False, "بازی مورد نظر یافت نشد", None
        
        game = self.games[game_id]
        
        if game.status != "waiting":
            return False, "این بازی در حال انجام است یا به پایان رسیده", None
        
        if player_id_str in self.user_games:
            return False, "شما در حال حاضر در یک بازی دیگر هستید", None
        
        if not game.add_player(player_id, player_name):
            return False, "خطا در پیوستن به بازی", None
        
        self.user_games[player_id_str] = game_id
        return True, game_id, game
    
    def make_move(self, game_id: str, user_id: int, row: int, col: int) -> dict:
        """انجام حرکت"""
        if game_id not in self.games:
            return {"success": False, "reason": "بازی یافت نشد"}
        
        game = self.games[game_id]
        result = game.make_move(user_id, row, col)
        
        if result.get("success") and result.get("winner"):
            if game.host_id in self.user_games:
                del self.user_games[game.host_id]
            if game.player_id and game.player_id in self.user_games:
                del self.user_games[game.player_id]
            return result
        
        return result
    
    def get_game(self, game_id: str) -> Optional[GameXO]:
        return self.games.get(game_id)
    
    def get_user_game(self, user_id: int) -> Optional[GameXO]:
        user_id_str = str(user_id)
        if user_id_str in self.user_games:
            game_id = self.user_games[user_id_str]
            if game_id in self.games:
                return self.games[game_id]
            else:
                del self.user_games[user_id_str]
        return None
    
    def remove_game(self, game_id: str):
        if game_id in self.games:
            game = self.games[game_id]
            if game.host_id in self.user_games:
                del self.user_games[game.host_id]
            if game.player_id and game.player_id in self.user_games:
                del self.user_games[game.player_id]
            del self.games[game_id]
    
    def check_timeout(self):
        """بررسی تایم‌اوت بازی‌ها"""
        now = datetime.now().timestamp()
        to_remove = []
        
        for game_id, game in self.games.items():
            if game.status == "finished":
                if now - game.last_move_at > 300:
                    to_remove.append(game_id)
                continue
            
            if game.status == "playing":
                if now - game.last_move_at > 60:
                    loser_id = game.host_id if game.current_turn == "host" else game.player_id
                    game.winner = "player" if game.current_turn == "host" else "host"
                    game.status = "finished"
                    game.last_move_at = now
                    
                    if game.host_id in self.user_games:
                        del self.user_games[game.host_id]
                    if game.player_id and game.player_id in self.user_games:
                        del self.user_games[game.player_id]
                    
                    logger.info(f"⏰ بازی {game_id} - بازیکن {loser_id} به خاطر تایم‌اوت بازنده شد")
                    to_remove.append(game_id)
            
            if game.status == "waiting":
                if now - game.created_at > 300:
                    to_remove.append(game_id)
        
        for game_id in to_remove:
            self.remove_game(game_id)
    
    def is_on_cooldown(self, user_id: int) -> Tuple[bool, int]:
        """بررسی خنک‌سازی"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_cooldowns:
            return False, 0
        
        elapsed = datetime.now().timestamp() - self.user_cooldowns[user_id_str]
        if elapsed < 120:
            return True, int(120 - elapsed)
        
        return False, 0
    
    def set_cooldown(self, user_id: int):
        self.user_cooldowns[str(user_id)] = datetime.now().timestamp()


# ================================================================
# نمونه global
# ================================================================

game_manager = GameManager()
