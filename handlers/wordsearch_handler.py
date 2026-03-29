"""
handlers/wordsearch_handler.py — Word Search game for groups.

Flow:
  /wordsearch (or /ws)  →  pick theme  →  generate grid image  →  players type words
  Bot checks guesses, highlights found words, updates image.
  Game ends when all words found or /endws called.

Multiplayer: everyone in the group can type answers simultaneously.
Scoring: word length determines points (longer = harder = more pts).
"""

import html
import logging
import time

from telegram import Update, InputMediaPhoto
from telegram.error import TelegramError
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from words import THEME_NAMES, pick_theme, pick_words, word_score
from wordsearch import generate_grid, render_grid_image
from database import save_user, get_user_lang, add_coins
import state

logger = logging.getLogger(__name__)

GAME_TTL = 600  # 10 minutes max per game


def _e(s) -> str:
    return html.escape(str(s))


# ─────────────────────────────────────────────────────────
#  IMAGE HELPER
# ─────────────────────────────────────────────────────────

def _build_image(ws: dict) -> bytes:
    return render_grid_image(
        grid=ws["grid"],
        size=ws["size"],
        theme=ws["theme"],
        total_words=len(ws["words"]),
        found_words=ws["found"],
        placements=ws["placements"],
    )


def _scoreboard(ws: dict) -> str:
    """Build a scoreboard string from player scores."""
    scores = ws.get("scores", {})
    if not scores:
        return ""
    # Sort by score desc
    ranked = sorted(scores.items(), key=lambda x: x[1]["pts"], reverse=True)
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, info) in enumerate(ranked):
        medal = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{medal} <b>{_e(info['name'])}</b> — {info['pts']} pts ({info['count']} words)")
    return "\n".join(lines)


def _words_status(ws: dict) -> str:
    """Show word list with found/unfound status."""
    lines = []
    for word in ws["words"]:
        pts = word_score(word)
        if word in ws["found"]:
            finder = ws.get("finders", {}).get(word, "")
            lines.append(f"  ✅ <s>{word}</s> (+{pts}) — {_e(finder)}")
        else:
            # Show as blanks with first letter hint
            hidden = word[0] + "·" * (len(word) - 1)
            lines.append(f"  ❔ {hidden} ({len(word)} letters, +{pts} pts)")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
#  /wordsearch  or  /ws  — start a game
# ─────────────────────────────────────────────────────────

async def cmd_wordsearch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user    = update.effective_user
    await save_user(user)
    lang = await get_user_lang(user.id)

    # Only in groups
    if chat_id == user.id:
        await update.message.reply_text(
            "🔍 Word Search works in groups! Add me to a group first.",
        )
        return

    # Check for existing game
    if await state.ws_exists(chat_id):
        await update.message.reply_text(
            "⚠️ A Word Search is already running! "
            "Finish it or use /endws to cancel.",
        )
        return

    # Pick theme and words
    theme = pick_theme()
    words = pick_words(theme, count=8)
    grid_data = generate_grid(words, size=10)

    # Only keep words that were actually placed
    placed_words = list(grid_data["placements"].keys())
    if len(placed_words) < 3:
        # Retry once if too few placed
        grid_data = generate_grid(words, size=12)
        placed_words = list(grid_data["placements"].keys())

    # Convert placements to JSON-safe (list of lists)
    safe_placements = {}
    for w, positions in grid_data["placements"].items():
        safe_placements[w] = [[r, c] for r, c in positions]

    ws = {
        "grid": grid_data["grid"],
        "size": grid_data["size"],
        "theme": theme,
        "words": placed_words,
        "placements": safe_placements,
        "found": [],
        "finders": {},
        "scores": {},
        "started_by": user.id,
        "started_at": time.time(),
        "msg_id": None,
    }

    # Generate image
    img = _build_image(ws)

    # Send grid
    msg = await update.message.reply_photo(
        photo=img,
        caption=(
            f"🔍 <b>Word Search!</b>  •  {theme}\n\n"
            f"Find <b>{len(placed_words)} hidden words</b> in the grid!\n"
            f"Type a word to guess. Longer words = more points!\n\n"
            f"{_words_status(ws)}"
        ),
        parse_mode=ParseMode.HTML,
    )

    ws["msg_id"] = msg.message_id
    await state.set_ws(chat_id, ws, ttl=GAME_TTL)


# ─────────────────────────────────────────────────────────
#  /endws — end current word search
# ─────────────────────────────────────────────────────────

async def cmd_endws(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ws = await state.get_ws(chat_id)

    if not ws:
        await update.message.reply_text("No active Word Search game!")
        return

    await _finish_game(update, ctx, chat_id, ws, cancelled=True)


# ─────────────────────────────────────────────────────────
#  /hint — reveal a random unfound word's extra letter
# ─────────────────────────────────────────────────────────

async def cmd_hint(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ws = await state.get_ws(chat_id)

    if not ws:
        await update.message.reply_text("No active Word Search game!")
        return

    unfound = [w for w in ws["words"] if w not in ws["found"]]
    if not unfound:
        return

    import random
    hint_word = random.choice(unfound)
    n = len(hint_word)
    # Show first letter, last letter, and one random middle letter
    if n <= 3:
        revealed = hint_word[0] + "·" * (n - 1)
    else:
        mid = random.randint(1, n - 2)
        chars = list("·" * n)
        chars[0] = hint_word[0]
        chars[-1] = hint_word[-1]
        chars[mid] = hint_word[mid]
        revealed = "".join(chars)

    await update.message.reply_text(
        f"💡 <b>Hint:</b> {revealed} ({n} letters, +{word_score(hint_word)} pts)",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────────────────
#  MESSAGE HANDLER — checks every group message for word guesses
# ─────────────────────────────────────────────────────────

async def handle_ws_guess(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Called for every text message in groups with an active WS game."""
    if not update.message or not update.message.text:
        return
    chat_id = update.effective_chat.id
    user    = update.effective_user
    text    = update.message.text.strip().upper()

    # Quick filters: single word only, reasonable length
    if " " in text or len(text) < 3 or len(text) > 12:
        return

    async with state.ws_lock(chat_id):
        ws = await state.get_ws(chat_id)
        if not ws:
            return

        # Is it one of the hidden words?
        if text not in ws["words"]:
            return

        # Already found?
        if text in ws["found"]:
            try:
                await update.message.reply_text(
                    f"⚠️ <b>{text}</b> was already found!",
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError:
                pass
            return

        # Found a new word!
        await save_user(user)
        pts = word_score(text)
        ws["found"].append(text)
        ws["finders"][text] = user.full_name

        uid_str = str(user.id)
        if uid_str not in ws["scores"]:
            ws["scores"][uid_str] = {"name": user.full_name, "pts": 0, "count": 0}
        ws["scores"][uid_str]["pts"] += pts
        ws["scores"][uid_str]["count"] += 1

        # Award coins immediately
        await add_coins(user.id, pts * 10)

        all_found = len(ws["found"]) == len(ws["words"])

        # Update image with highlighted found word
        img = _build_image(ws)

        # Build caption
        if all_found:
            caption = (
                f"🎉 <b>All words found!</b>  •  {ws['theme']}\n\n"
                f"{_words_status(ws)}\n\n"
                f"🏆 <b>Scoreboard:</b>\n{_scoreboard(ws)}"
            )
        else:
            remaining = len(ws["words"]) - len(ws["found"])
            caption = (
                f"🔍 <b>Word Search!</b>  •  {ws['theme']}\n\n"
                f"✅ <b>{_e(user.full_name)}</b> found <b>{text}</b>! (+{pts} pts, +{pts*10} coins)\n"
                f"📝 <b>{remaining}</b> words left!\n\n"
                f"{_words_status(ws)}"
            )

        # Edit the original message with updated grid
        try:
            await ctx.bot.edit_message_media(
                chat_id=chat_id,
                message_id=ws["msg_id"],
                media=InputMediaPhoto(
                    media=img,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                ),
            )
        except TelegramError as exc:
            logger.warning(f"Failed to edit WS image: {exc}")
            # Send a new message as fallback
            msg = await update.message.reply_photo(
                photo=img,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
            ws["msg_id"] = msg.message_id

        if all_found:
            await state.delete_ws(chat_id)
            # Bonus for the person who found the last word
            await add_coins(user.id, 50)
            try:
                await update.message.reply_text(
                    f"🎊 <b>Game Complete!</b>\n\n"
                    f"🏆 <b>Final Scores:</b>\n{_scoreboard(ws)}\n\n"
                    f"💰 Bonus <b>+50 coins</b> to {_e(user.full_name)} for finding the last word!",
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError:
                pass
        else:
            await state.set_ws(chat_id, ws, ttl=GAME_TTL)


# ─────────────────────────────────────────────────────────
#  FINISH GAME (cancel or timeout)
# ─────────────────────────────────────────────────────────

async def _finish_game(update: Update, ctx, chat_id: int, ws: dict, cancelled: bool = False):
    await state.delete_ws(chat_id)

    unfound = [w for w in ws["words"] if w not in ws["found"]]
    unfound_str = ", ".join(f"<b>{w}</b>" for w in unfound) if unfound else "None"

    sb = _scoreboard(ws)
    score_block = f"\n\n🏆 <b>Scores:</b>\n{sb}" if sb else ""

    if cancelled:
        text = (
            f"🛑 <b>Word Search ended!</b>  •  {ws['theme']}\n\n"
            f"Found: <b>{len(ws['found'])}/{len(ws['words'])}</b>\n"
            f"Missed: {unfound_str}"
            f"{score_block}"
        )
    else:
        text = (
            f"⏰ <b>Time's up!</b>  •  {ws['theme']}\n\n"
            f"Found: <b>{len(ws['found'])}/{len(ws['words'])}</b>\n"
            f"Missed: {unfound_str}"
            f"{score_block}"
        )

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
