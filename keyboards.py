"""
keyboards.py — All InlineKeyboardMarkup builders.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import UPDATE_CHANNEL, BOT_USERNAME, SUPPORT_USERNAME
from game import EMPTY, CELL_EMOJI
from emojis import btn_emoji, get_cell_emoji_plain

BTN_CELL = get_cell_emoji_plain()


def _b(text, data, style="", icon_key=""):
    kw = {}
    if style:
        kw["style"] = style
    icon_id = btn_emoji(icon_key) if icon_key else None
    if icon_id:
        kw["icon_custom_emoji_id"] = icon_id
    if kw:
        return InlineKeyboardButton(
            text, callback_data=data, api_kwargs=kw
        )
    return InlineKeyboardButton(text, callback_data=data)


def _u(text, url, style="", icon_key=""):
    kw = {}
    if style:
        kw["style"] = style
    icon_id = btn_emoji(icon_key) if icon_key else None
    if icon_id:
        kw["icon_custom_emoji_id"] = icon_id
    if kw:
        return InlineKeyboardButton(
            text, url=url, api_kwargs=kw
        )
    return InlineKeyboardButton(text, url=url)


# ── DM Welcome ───────────────────────────────────────────

def main_menu_kb():
    return InlineKeyboardMarkup([
        [
            _u("➕ Add to Group",
               f"https://t.me/{BOT_USERNAME}?startgroup=true", "success"),
            _u("📢 Updates",
               f"https://t.me/{UPDATE_CHANNEL.lstrip('@')}", "primary"),
        ],
        [
            _b("Help & Commands", "cb_help", "primary"),
            _b("My Stats", "cb_stats", "primary"),
        ],
        [
            _b("Leaderboard", "cb_leaderboard", "primary"),
            _b("Language", "cb_language"),
        ],
        [_u("Support", f"https://t.me/{SUPPORT_USERNAME}")],
    ])


# ── Group Welcome ────────────────────────────────────────

def group_welcome_kb():
    return InlineKeyboardMarkup([
        [
            _b("⚔️ PvP Game", "cb_mode_pvp", "primary", "swords"),
            _b("🤖 vs Bot", "cb_mode_pve", "primary", "robot"),
        ],
        [
            _b("🏆 Tournament", "cb_mode_tournament", "primary", "trophy"),
            _b("📅 Daily Puzzle", "cb_mode_daily", "primary", "calendar"),
        ],
        [
            _b("My Stats", "cb_stats", "primary"),
            _b("Leaderboard", "cb_leaderboard", "primary"),
        ],
        [_u("📢 Updates", f"https://t.me/{UPDATE_CHANNEL.lstrip('@')}")],
    ])


# ── Game Board ───────────────────────────────────────────

def board_kb(board, chat_id):
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            idx  = r * 3 + c
            cell = board[idx]
            if cell == EMPTY:
                row.append(
                    InlineKeyboardButton(
                        "　", callback_data=f"mv:{chat_id}:{idx}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        BTN_CELL[cell], callback_data="noop"
                    )
                )
        rows.append(row)
    return InlineKeyboardMarkup(rows)


# ── XO Open Lobby ────────────────────────────────────────

def xo_lobby_kb(chat_id, creator_id):
    return InlineKeyboardMarkup([
        [_b("⚡ Join Game", f"xo_join:{chat_id}:{creator_id}", "success", "lightning")],
        [_b("Cancel", f"xo_cancel:{chat_id}:{creator_id}", "danger")],
    ])


# ── PvP Challenge ────────────────────────────────────────

def challenge_kb(challenger_id):
    return InlineKeyboardMarkup([[
        _b("Accept", f"ch_accept:{challenger_id}", "success"),
        _b("Decline", f"ch_decline:{challenger_id}", "danger"),
    ]])


# ── PvE: Difficulty ──────────────────────────────────────

def difficulty_kb(user_id: int):
    return InlineKeyboardMarkup([[
        _b("Easy", f"diff:{user_id}:easy", "success"),
        _b("Medium", f"diff:{user_id}:medium"),
        _b("Hard", f"diff:{user_id}:hard", "danger"),
    ]])


# ── PvE: Character ─────────────────────────────────────────

def character_kb(difficulty, user_id: int):
    return InlineKeyboardMarkup([
        [
            _b("The Devil", f"char:{user_id}:{difficulty}:devil", icon_key="devil"),
            _b("The Nerd", f"char:{user_id}:{difficulty}:nerd", icon_key="nerd"),
            _b("Grandma", f"char:{user_id}:{difficulty}:grandma", icon_key="grandma"),
        ],
        [_b("Back", f"pick_diff:{user_id}")],
    ])


# ── Post-game: PvE ──────────────────────────────────────

def rematch_kb(mode):
    return InlineKeyboardMarkup([[
        _b("🔄 Rematch", f"rematch:{mode}", "primary", "refresh"),
        _b("Main Menu", "cb_main_menu"),
    ]])


# ── Post-game: PvP / xo ─────────────────────────────────

def pvp_rematch_kb():
    return InlineKeyboardMarkup([[
        _b("🎮 New /xo Game", "xo_new", "primary", "game"),
        _b("Main Menu", "cb_main_menu"),
    ]])


# ── Post-game: Revenge ──────────────────────────────────

def revenge_kb():
    return InlineKeyboardMarkup([
        [_b("🔥 REVENGE  ×2 Coins", "revenge", "danger", "fire")],
        [
            _b("🔄 Rematch", "rematch:pve", "primary", "refresh"),
            _b("Main Menu", "cb_main_menu"),
        ],
    ])


# ── Nav ──────────────────────────────────────────────────

def back_kb():
    return InlineKeyboardMarkup([[_b("Back", "cb_main_menu")]])


# ── Language ─────────────────────────────────────────────

def language_kb():
    return InlineKeyboardMarkup([
        [
            _b("🇬🇧 English", "lang:en", "primary"),
            _b("🇸🇦 العربية", "lang:ar"),
            _b("🇮🇳 हिंदी", "lang:hi"),
        ],
        [_b("Back", "cb_main_menu")],
    ])


# ── Tournament ───────────────────────────────────────────

def tourn_size_kb():
    return InlineKeyboardMarkup([[
        _b("4 Players", "t_create:4", "primary"),
        _b("8 Players", "t_create:8", "primary"),
    ]])


def tourn_lobby_kb(chat_id, creator_id):
    return InlineKeyboardMarkup([
        [
            _b("Join", f"t_join:{chat_id}", "success"),
            _b("Start Now", f"t_start:{chat_id}", "primary"),
        ],
        [_b("Cancel", f"t_cancel:{chat_id}", "danger")],
    ])


# ── Daily Puzzle ─────────────────────────────────────────

def daily_board_kb(board, chat_id, puzzle_idx):
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            idx  = r * 3 + c
            cell = board[idx]
            if cell == EMPTY:
                row.append(
                    InlineKeyboardButton(
                        "　",
                        callback_data=f"daily:{chat_id}:{puzzle_idx}:{idx}",
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        BTN_CELL[cell], callback_data="noop"
                    )
                )
        rows.append(row)
    return InlineKeyboardMarkup(rows)
