import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

load_dotenv()

# Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
BOT_USERNAME = os.getenv("BOT_USERNAME", "tictactoe_bot")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Database Setup ==============
class Database:
    def __init__(self, mongodb_url: str):
        self.client = AsyncIOMotorClient(mongodb_url, maxPoolSize=50, minPoolSize=10)
        self.db: AsyncIOMotorDatabase = self.client["tictactoe_bot"]
    
    async def init(self):
        """Initialize collections with optimized indexes"""
        try:
            # Leaderboard indexes
            await self.db.leaderboard.create_index("user_id", unique=False)
            await self.db.leaderboard.create_index("group_id", unique=False)
            await self.db.leaderboard.create_index([("group_id", 1), ("wins", -1)])
            
            # Games indexes
            await self.db.games.create_index("game_id", unique=True)
            await self.db.games.create_index("group_id", unique=False)
            await self.db.games.create_index("created_at", expireAfterSeconds=86400)  # Auto-delete after 24h
            
            # Tournaments indexes
            await self.db.tournaments.create_index("group_id", unique=False)
            await self.db.tournaments.create_index("status", unique=False)
            
            # Daily challenges indexes
            await self.db.daily_challenges.create_index([("user_id", 1), ("date", -1)])
            await self.db.daily_challenges.create_index([("streak", -1)])
            
            # Users & Groups
            await self.db.users.create_index("user_id", unique=True)
            await self.db.groups.create_index("group_id", unique=True)
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Database init error: {e}")
    
    # ========== User & Group Management ==========
    async def add_user(self, user_id: int, username: str):
        """Register/update user"""
        try:
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "username": username,
                    "last_seen": datetime.utcnow()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
    
    async def add_group(self, group_id: int, group_name: str):
        """Register group"""
        try:
            await self.db.groups.update_one(
                {"group_id": group_id},
                {"$set": {
                    "group_id": group_id,
                    "name": group_name,
                    "added_at": datetime.utcnow()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error adding group {group_id}: {e}")
    
    # ========== Stats Management ==========
    async def add_user_stats(self, user_id: int, username: str, group_id: int):
        """Add user stats for group"""
        try:
            filter_doc = {"user_id": user_id, "group_id": group_id}
            await self.db.leaderboard.update_one(
                filter_doc,
                {"$setOnInsert": {
                    "user_id": user_id,
                    "username": username,
                    "group_id": group_id,
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "created_at": datetime.utcnow()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error adding stats for user {user_id}: {e}")
    
    async def update_game_result(self, user_id: int, result: str, group_id: int):
        """Update game result (win/loss/draw)"""
        try:
            await self.db.leaderboard.update_one(
                {"user_id": user_id, "group_id": group_id},
                {"$inc": {f"{result}s": 1}}
            )
        except Exception as e:
            logger.error(f"Error updating game result for {user_id}: {e}")
    
    async def get_group_leaderboard(self, group_id: int, limit: int = 10) -> List[Dict]:
        """Get group leaderboard"""
        try:
            pipeline = [
                {"$match": {"group_id": group_id}},
                {"$addFields": {
                    "total_games": {"$add": ["$wins", "$losses", "$draws"]},
                    "win_rate": {"$cond": [
                        {"$gt": [{"$add": ["$wins", "$losses", "$draws"]}, 0]},
                        {"$multiply": [{"$divide": ["$wins", {"$add": ["$wins", "$losses", "$draws"]}]}, 100]},
                        0
                    ]}
                }},
                {"$sort": {"wins": -1}},
                {"$limit": limit}
            ]
            return await self.db.leaderboard.aggregate(pipeline).to_list(limit)
        except Exception as e:
            logger.error(f"Error getting group leaderboard: {e}")
            return []
    
    async def get_user_stats(self, user_id: int, group_id: int) -> Optional[Dict]:
        """Get user stats"""
        try:
            return await self.db.leaderboard.find_one({"user_id": user_id, "group_id": group_id})
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return None
    
    # ========== Game Management ==========
    async def save_game(self, game_id: str, game_data: Dict):
        """Save game state"""
        try:
            await self.db.games.update_one(
                {"game_id": game_id},
                {"$set": game_data},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving game {game_id}: {e}")
    
    async def get_game(self, game_id: str) -> Optional[Dict]:
        """Get game state"""
        try:
            return await self.db.games.find_one({"game_id": game_id})
        except Exception as e:
            logger.error(f"Error getting game {game_id}: {e}")
            return None
    
    async def delete_game(self, game_id: str):
        """Delete game"""
        try:
            await self.db.games.delete_one({"game_id": game_id})
        except Exception as e:
            logger.error(f"Error deleting game {game_id}: {e}")
    
    # ========== Daily Challenge ==========
    async def get_today_challenge(self, user_id: int):
        """Get today's challenge"""
        try:
            today = datetime.utcnow().date()
            return await self.db.daily_challenges.find_one({
                "user_id": user_id,
                "date": today
            })
        except Exception as e:
            logger.error(f"Error getting daily challenge: {e}")
            return None
    
    async def create_daily_challenge(self, user_id: int, username: str):
        """Create daily challenge"""
        try:
            today = datetime.utcnow().date()
            challenge = await self.get_today_challenge(user_id)
            
            if challenge:
                return challenge
            
            yesterday = today - timedelta(days=1)
            yesterday_challenge = await self.db.daily_challenges.find_one({
                "user_id": user_id,
                "date": yesterday,
                "completed": True
            })
            
            streak = (yesterday_challenge.get("streak", 0) + 1) if yesterday_challenge else 1
            
            new_challenge = {
                "user_id": user_id,
                "username": username,
                "date": today,
                "completed": False,
                "wins_needed": 1,
                "wins": 0,
                "streak": streak,
                "created_at": datetime.utcnow()
            }
            
            await self.db.daily_challenges.insert_one(new_challenge)
            return new_challenge
        except Exception as e:
            logger.error(f"Error creating daily challenge: {e}")
            return None
    
    async def complete_daily_challenge(self, user_id: int):
        """Mark challenge as complete"""
        try:
            today = datetime.utcnow().date()
            await self.db.daily_challenges.update_one(
                {"user_id": user_id, "date": today},
                {"$inc": {"wins": 1}, "$set": {"completed": True}}
            )
        except Exception as e:
            logger.error(f"Error completing daily challenge: {e}")

# ============== Game Logic ==============
class TicTacToe:
    def __init__(self):
        self.board = ['⬜'] * 9
        self.current_player = '❌'
        self.game_over = False
        self.winner = None
    
    def is_valid_move(self, position: int) -> bool:
        return 0 <= position <= 8 and self.board[position] == '⬜'
    
    def make_move(self, position: int) -> bool:
        if not self.is_valid_move(position):
            return False
        
        self.board[position] = self.current_player
        if self.check_winner():
            self.game_over = True
            self.winner = self.current_player
        elif all(cell != '⬜' for cell in self.board):
            self.game_over = True
            self.winner = 'Draw'
        else:
            self.current_player = '⭕' if self.current_player == '❌' else '❌'
        return True
    
    def check_winner(self) -> bool:
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        
        for combo in winning_combinations:
            if (self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != '⬜'):
                return True
        return False
    
    def get_bot_move(self) -> int:
        # Win
        for i in range(9):
            if self.board[i] == '⬜':
                self.board[i] = '⭕'
                if self.check_winner():
                    self.board[i] = '⬜'
                    return i
                self.board[i] = '⬜'
        
        # Block
        for i in range(9):
            if self.board[i] == '⬜':
                self.board[i] = '❌'
                if self.check_winner():
                    self.board[i] = '⬜'
                    return i
                self.board[i] = '⬜'
        
        # Center
        if self.board[4] == '⬜':
            return 4
        
        # Corners
        for corner in [0, 2, 6, 8]:
            if self.board[corner] == '⬜':
                return corner
        
        # Any
        for i in range(9):
            if self.board[i] == '⬜':
                return i
        
        return -1
    
    def get_board_display(self) -> str:
        return f"{self.board[0]} {self.board[1]} {self.board[2]}\n{self.board[3]} {self.board[4]} {self.board[5]}\n{self.board[6]} {self.board[7]} {self.board[8]}"
    
    def to_dict(self):
        return {
            "board": self.board,
            "current_player": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner
        }
    
    @staticmethod
    def from_dict(data):
        game = TicTacToe()
        game.board = data["board"]
        game.current_player = data["current_player"]
        game.game_over = data["game_over"]
        game.winner = data["winner"]
        return game

# ============== FSM States ==============
class GameStates(StatesGroup):
    playing_pvp = State()
    playing_pvb = State()
    waiting_opponent = State()
    selecting_mode = State()

# ============== Global Variables ==============
db: Database
bot: Bot
dp: Dispatcher

active_games: Dict[str, TicTacToe] = {}
waiting_players: Dict[int, Tuple[str, int]] = {}

# ============== UI Helper Functions ==============

def create_game_keyboard(game_id: str, game: TicTacToe) -> InlineKeyboardMarkup:
    """Create colored game board"""
    keyboard = []
    for row in range(3):
        row_buttons = []
        for col in range(3):
            pos = row * 3 + col
            callback = f"move_{game_id}_{pos}"
            row_buttons.append(InlineKeyboardButton(
                text=game.board[pos], 
                callback_data=callback
            ))
        keyboard.append(row_buttons)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def format_leaderboard(entries: List[Dict], title: str) -> str:
    """Format leaderboard"""
    if not entries:
        return f"<b>{title}</b>\n\nNo games played yet."
    
    text = f"<b>{title}</b>\n\n"
    for idx, entry in enumerate(entries, 1):
        total = entry.get("total_games", 0)
        username = entry.get("username", f"User {entry['user_id']}")
        
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
        text += f"{medal} {username}\n    {entry['wins']}W - {entry['losses']}L - {entry['draws']}D\n"
    
    return text

# ============== Command Handlers ==============

async def cmd_xo(message: types.Message, state: FSMContext):
    """Start game in group"""
    if message.chat.type == "private":
        await message.answer("Use /xo in a group to play!")
        return
    
    # Register group and user
    await db.add_group(message.chat.id, message.chat.title or "Group")
    await db.add_user(message.from_user.id, message.from_user.username or f"User{message.from_user.id}")
    
    # Create mode selection keyboard with colors
    await message.answer(
        "<b>Select Game Mode</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Play vs AI",
                    callback_data=f"mode_pvb_{message.from_user.id}"
                ),
                InlineKeyboardButton(
                    text="⚔️ Player vs Player",
                    callback_data=f"mode_pvp_{message.from_user.id}"
                )
            ]
        ])
    )
    
    await state.set_state(GameStates.selecting_mode)

async def cmd_top(message: types.Message):
    """Show group leaderboard"""
    if message.chat.type == "private":
        await message.answer("Use /top in a group to see rankings!")
        return
    
    entries = await db.get_group_leaderboard(message.chat.id, 10)
    text = format_leaderboard(entries, f"{message.chat.title or 'Group'} Leaderboard")
    await message.answer(text, parse_mode="HTML")

async def cmd_mystats(message: types.Message):
    """Show personal stats"""
    if message.chat.type == "private":
        await message.answer("Use /mystats in a group to see your stats!")
        return
    
    user_id = message.from_user.id
    group_id = message.chat.id
    
    stats = await db.get_user_stats(user_id, group_id)
    
    if not stats:
        text = "You haven't played any games yet."
    else:
        total = stats["wins"] + stats["losses"] + stats["draws"]
        win_rate = (stats["wins"] / total * 100) if total > 0 else 0
        text = f"<b>Your Stats</b>\n\n"
        text += f"Wins: {stats['wins']}\n"
        text += f"Losses: {stats['losses']}\n"
        text += f"Draws: {stats['draws']}\n"
        text += f"Win Rate: {win_rate:.1f}%\n"
        text += f"Total Games: {total}"
    
    await message.answer(text, parse_mode="HTML")

# ============== Callback Handlers ==============

async def handle_mode_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Handle game mode selection"""
    data_parts = callback_query.data.split('_')
    mode = data_parts[1]  # pvb or pvp
    user_id = int(data_parts[2])
    
    if callback_query.from_user.id != user_id:
        await callback_query.answer("This is not your game!", show_alert=False)
        return
    
    chat_id = callback_query.message.chat.id
    username = callback_query.from_user.username or f"User{user_id}"
    
    # PvB Mode
    if mode == "pvb":
        game_id = f"pvb_{user_id}_{chat_id}_{int(datetime.utcnow().timestamp())}"
        game = TicTacToe()
        active_games[game_id] = game
        
        await db.add_user_stats(user_id, username, chat_id)
        
        game_data = {
            "game_id": game_id,
            "player_id": user_id,
            "opponent_id": 0,
            "group_id": chat_id,
            "mode": "pvb",
            "game_state": game.to_dict(),
            "created_at": datetime.utcnow()
        }
        await db.save_game(game_id, game_data)
        
        text = f"<b>Battle vs AI</b>\n\nYou: ❌\n\n<code>{game.get_board_display()}</code>"
        await callback_query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=create_game_keyboard(game_id, game)
        )
        
        await state.set_state(GameStates.playing_pvb)
        await callback_query.answer()
    
    # PvP Mode
    elif mode == "pvp":
        await callback_query.message.edit_text(
            "<b>Waiting for opponent...</b>\n\nOthers can click below to accept the challenge.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⚔️ Accept Challenge",
                    callback_data=f"accept_pvp_{user_id}"
                )]
            ])
        )
        
        waiting_players[user_id] = (username, chat_id)
        await state.set_state(GameStates.waiting_opponent)
        await callback_query.answer()

async def handle_accept_pvp(callback_query: types.CallbackQuery, state: FSMContext):
    """Accept PvP challenge"""
    data_parts = callback_query.data.split('_')
    challenger_id = int(data_parts[-1])
    
    if challenger_id not in waiting_players:
        await callback_query.answer("Challenge expired!", show_alert=True)
        return
    
    if callback_query.from_user.id == challenger_id:
        await callback_query.answer("You can't challenge yourself!", show_alert=True)
        return
    
    challenger_name, chat_id = waiting_players[challenger_id]
    acceptor_id = callback_query.from_user.id
    acceptor_name = callback_query.from_user.username or f"User{acceptor_id}"
    
    # Create game
    game_id = f"game_{min(challenger_id, acceptor_id)}_{max(challenger_id, acceptor_id)}_{chat_id}_{int(datetime.utcnow().timestamp())}"
    game = TicTacToe()
    active_games[game_id] = game
    
    await db.add_user_stats(challenger_id, challenger_name, chat_id)
    await db.add_user_stats(acceptor_id, acceptor_name, chat_id)
    
    game_data = {
        "game_id": game_id,
        "player_id": challenger_id,
        "opponent_id": acceptor_id,
        "group_id": chat_id,
        "mode": "pvp",
        "game_state": game.to_dict(),
        "created_at": datetime.utcnow()
    }
    await db.save_game(game_id, game_data)
    
    text = f"<b>Player Battle</b>\n\n{challenger_name} (❌) vs {acceptor_name} (⭕)\n\n<code>{game.get_board_display()}</code>\n\nTurn: ❌"
    
    await callback_query.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=create_game_keyboard(game_id, game)
    )
    
    del waiting_players[challenger_id]
    await state.clear()
    await callback_query.answer()

async def handle_game_move(callback_query: types.CallbackQuery, state: FSMContext):
    """Handle game move"""
    data_parts = callback_query.data.split('_')
    game_id = '_'.join(data_parts[1:-1])
    position = int(data_parts[-1])
    
    if game_id not in active_games:
        await callback_query.answer("Game not found!", show_alert=True)
        return
    
    game = active_games[game_id]
    
    if game.game_over:
        await callback_query.answer("Game is over!", show_alert=True)
        return
    
    if not game.make_move(position):
        await callback_query.answer("Invalid move!", show_alert=True)
        return
    
    await callback_query.answer()
    
    game_data = await db.get_game(game_id)
    
    # PvB game
    if game_data.get("mode") == "pvb":
        text = f"<b>Battle vs AI</b>\n\nYou: ❌\n\n<code>{game.get_board_display()}</code>"
        
        if not game.game_over:
            bot_move = game.get_bot_move()
            if bot_move != -1:
                game.make_move(bot_move)
                
                if game.game_over:
                    text += "\n\n"
                    if game.winner == "Draw":
                        text += "<b>Draw!</b>"
                        await db.update_game_result(game_data["player_id"], "draw", game_data.get("group_id"))
                    elif game.winner == '❌':
                        text += "<b>You Won!</b>"
                        await db.update_game_result(game_data["player_id"], "win", game_data.get("group_id"))
                        await db.complete_daily_challenge(game_data["player_id"])
                    else:
                        text += "<b>AI Won!</b>"
                        await db.update_game_result(game_data["player_id"], "loss", game_data.get("group_id"))
                    
                    await db.delete_game(game_id)
                    del active_games[game_id]
        else:
            text += "\n\n"
            if game.winner == "Draw":
                text += "<b>Draw!</b>"
                await db.update_game_result(game_data["player_id"], "draw", game_data.get("group_id"))
            elif game.winner == '❌':
                text += "<b>You Won!</b>"
                await db.update_game_result(game_data["player_id"], "win", game_data.get("group_id"))
                await db.complete_daily_challenge(game_data["player_id"])
            else:
                text += "<b>AI Won!</b>"
                await db.update_game_result(game_data["player_id"], "loss", game_data.get("group_id"))
            
            await db.delete_game(game_id)
            del active_games[game_id]
        
        await callback_query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=create_game_keyboard(game_id, game) if not game.game_over else None
        )
    
    # PvP game
    else:
        text = f"<b>Player Battle</b>\n\n<code>{game.get_board_display()}</code>\n\nTurn: {game.current_player}"
        
        if game.game_over:
            text = text.replace(f"Turn: {game.winner}", "")
            text += "\n\n"
            if game.winner == "Draw":
                text += "<b>Draw!</b>"
                await db.update_game_result(game_data["player_id"], "draw", game_data.get("group_id"))
                await db.update_game_result(game_data["opponent_id"], "draw", game_data.get("group_id"))
            else:
                if game.winner == '❌':
                    text += f"<b>{game_data['player_id']} Won!</b>"
                    await db.update_game_result(game_data["player_id"], "win", game_data.get("group_id"))
                    await db.update_game_result(game_data["opponent_id"], "loss", game_data.get("group_id"))
                else:
                    text += f"<b>{game_data['opponent_id']} Won!</b>"
                    await db.update_game_result(game_data["opponent_id"], "win", game_data.get("group_id"))
                    await db.update_game_result(game_data["player_id"], "loss", game_data.get("group_id"))
            
            await db.delete_game(game_id)
            del active_games[game_id]
        
        await callback_query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=create_game_keyboard(game_id, game) if not game.game_over else None
        )

# ============== Bot Setup ==============

async def set_commands(bot: Bot):
    """Set bot commands"""
    commands = [
        BotCommand(command="xo", description="Start a game"),
        BotCommand(command="top", description="Group leaderboard"),
        BotCommand(command="mystats", description="Your statistics"),
    ]
    await bot.set_my_commands(commands)

async def main():
    global db, bot, dp
    
    logger.info("Starting bot...")
    
    # Initialize database
    db = Database(MONGODB_URL)
    await db.init()
    
    # Initialize bot
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Set commands
    await set_commands(bot)
    
    # Register handlers
    dp.message.register(cmd_xo, Command("xo"))
    dp.message.register(cmd_top, Command("top"))
    dp.message.register(cmd_mystats, Command("mystats"))
    
    # Callback handlers
    dp.callback_query.register(handle_mode_selection, F.data.startswith("mode_"))
    dp.callback_query.register(handle_accept_pvp, F.data.startswith("accept_pvp_"))
    dp.callback_query.register(handle_game_move, F.data.startswith("move_"))
    
    logger.info("Bot started successfully!")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        db.client.close()
        logger.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
