"""handlers/tournament_handler.py – Single-elimination bracket (4 or 8 players)."""

import html
import random

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# Top-level imports (fixed)
from keyboards import board_kb, tourn_lobby_kb, tourn_size_kb
from game import new_pvp_game
from database import (
    save_user, get_tournament, create_tournament,
    update_tournament, delete_tournament,
)

# In-memory: chat_id → active match info
tourn_games: dict = {}   # { chat_id: { "game": dict, "match": dict } }


def _e(s) -> str:
    return html.escape(str(s))


def _mention_html(user) -> str:
    name = user.full_name or user.username or str(user.id)
    return f'<a href="tg://user?id={user.id}">{_e(name)}</a>'


def _bracket_text(tourn: dict) -> str:
    players = tourn.get("players", [])
    size    = tourn.get("size", 0)
    bracket = tourn.get("bracket", [])
    status  = tourn.get("status", "waiting")

    lines = [f"🟣 <b>Tournament Bracket</b>\n({len(players)}/{size} players)\n"]

    if not bracket:
        lines.append("<b>Waiting for players…</b>")
        for i, p in enumerate(players):
            lines.append(f"  {i + 1}. {_e(p['name'])} ✅")
    else:
        for rnd_idx, rnd in enumerate(bracket):
            lines.append(f"\n<b>🔹 Round {rnd_idx + 1}</b>")
            for match in rnd:
                p1 = _e(match["p1"]["name"])
                p2 = _e(match["p2"]["name"])
                winner = _e(match.get("winner_name") or "")
                if match["status"] == "done":
                    lines.append(f"  ✅ {p1} vs {p2}  →  <b>{winner}</b>")
                elif match["status"] == "active":
                    lines.append(f"  ⚔️ {p1} vs {p2}  ← <b>LIVE</b>")
                else:
                    lines.append(f"  ⏳ {p1} vs {p2}")
    return "\n".join(lines)


# ── /tournament ───────────────────────────────────────────

async def cmd_tournament(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user    = update.effective_user

    if chat_id == user.id:
        await update.message.reply_text("🟣 Tournaments are for groups only!")
        return

    tourn = await get_tournament(chat_id)

    if not tourn:
        await update.message.reply_text(
            "🟣 <b>Start a Tournament!</b>\n\nChoose bracket size:",
            reply_markup=tourn_size_kb(),
            parse_mode=ParseMode.HTML,
        )
    elif tourn["status"] == "waiting":
        await update.message.reply_text(
            _bracket_text(tourn),
            reply_markup=tourn_lobby_kb(chat_id, tourn["creator_id"]),
            parse_mode=ParseMode.HTML,
        )
    elif tourn["status"] == "active":
        await update.message.reply_text(
            _bracket_text(tourn),
            parse_mode=ParseMode.HTML,
        )
    else:
        await delete_tournament(chat_id)
        await update.message.reply_text(
            "No active tournament. Start a new one:",
            reply_markup=tourn_size_kb(),
        )


# ── Callbacks (prefix: t_) ────────────────────────────────

async def handle_tournament_callbacks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    data    = query.data
    user    = query.from_user
    chat_id = query.message.chat_id
    await query.answer()
    await save_user(user)

    # ── Create ───────────────────────────────────
    if data.startswith("t_create:"):
        size = int(data.split(":")[1])

        existing = await get_tournament(chat_id)
        if existing:
            await query.answer("A tournament already exists! Use /tournament to view.", show_alert=True)
            return

        await create_tournament(chat_id, user.id, size)
        first_player = {"user_id": user.id, "name": user.full_name}
        await update_tournament(chat_id, {"players": [first_player]})

        await query.edit_message_text(
            f"🟣 <b>Tournament Created!</b>\n\n"
            f"Size: <b>{size} players</b>\n"
            f"Joined: <b>1/{size}</b>\n\n"
            f"1. {_e(user.full_name)} ✅\n\n"
            f"Others tap <b>Join</b> to enter!\n"
            f"Creator taps <b>Start Now</b> to begin early.",
            reply_markup=tourn_lobby_kb(chat_id, user.id),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Join ─────────────────────────────────────
    if data.startswith("t_join:"):
        tourn = await get_tournament(chat_id)
        if not tourn or tourn["status"] != "waiting":
            await query.answer("No open tournament to join!", show_alert=True)
            return

        players = tourn["players"]
        if any(p["user_id"] == user.id for p in players):
            await query.answer("You're already in the tournament!", show_alert=True)
            return
        if len(players) >= tourn["size"]:
            await query.answer("Tournament is full!", show_alert=True)
            return

        players.append({"user_id": user.id, "name": user.full_name})
        await update_tournament(chat_id, {"players": players})

        full = len(players) == tourn["size"]
        lines = [f"🟣 <b>Tournament Lobby</b> ({len(players)}/{tourn['size']})\n"]
        for i, p in enumerate(players):
            lines.append(f"  {i + 1}. {_e(p['name'])} ✅")
        if full:
            lines.append(f"\n✅ <b>Lobby is full!</b> Creator can start now.")

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=tourn_lobby_kb(chat_id, tourn["creator_id"]),
            parse_mode=ParseMode.HTML,
        )
        return

    # ── Cancel ───────────────────────────────────
    if data.startswith("t_cancel:"):
        tourn = await get_tournament(chat_id)
        if tourn and user.id != tourn["creator_id"]:
            await query.answer("Only the creator can cancel!", show_alert=True)
            return
        await delete_tournament(chat_id)
        await query.edit_message_text("❌ Tournament cancelled.")
        return

    # ── Start ────────────────────────────────────
    if data.startswith("t_start:"):
        tourn = await get_tournament(chat_id)
        if not tourn:
            await query.answer("No tournament found!", show_alert=True)
            return
        if user.id != tourn["creator_id"]:
            await query.answer("Only the creator can start the tournament!", show_alert=True)
            return

        players = tourn["players"]
        if len(players) < 2:
            await query.answer("Need at least 2 players to start!", show_alert=True)
            return

        # Shuffle and pad to even count
        shuffled = players[:]
        random.shuffle(shuffled)
        while len(shuffled) % 2 != 0:
            shuffled.append({"user_id": None, "name": "BYE"})

        round1 = []
        for i in range(0, len(shuffled), 2):
            round1.append({
                "p1":          shuffled[i],
                "p2":          shuffled[i + 1],
                "winner_id":   None,
                "winner_name": None,
                "status":      "pending",
            })

        await update_tournament(chat_id, {
            "status":  "active",
            "bracket": [round1],
            "round":   0,
        })

        bracket_msg = _bracket_text({**tourn, "bracket": [round1], "status": "active"})
        await query.edit_message_text(
            bracket_msg + "\n\n⚔️ <b>Round 1 — Fight!</b>",
            parse_mode=ParseMode.HTML,
        )
        await _start_next_match(ctx.bot, chat_id, round1)
        return


# ── Match management ──────────────────────────────────────

async def _start_next_match(bot, chat_id: int, matches: list):
    """Start the first pending (non-BYE) match in the given round."""
    for match in matches:
        if match["status"] != "pending":
            continue

        p1 = match["p1"]
        p2 = match["p2"]

        # Auto-advance BYE matches
        if p1["user_id"] is None:
            match.update(winner_id=p2["user_id"], winner_name=p2["name"], status="done")
            continue
        if p2["user_id"] is None:
            match.update(winner_id=p1["user_id"], winner_name=p1["name"], status="done")
            continue

        match["status"] = "active"
        game = new_pvp_game(p1["user_id"], p2["user_id"], p1["name"], p2["name"])
        game["tournament"] = True
        tourn_games[chat_id] = {"game": game, "match": match}

        header = (
            f"🏆 <b>Tournament Match!</b>\n"
            f"❌ <b>{_e(p1['name'])}</b>  ⚔️  ⭕ <b>{_e(p2['name'])}</b>"
        )
        await bot.send_message(
            chat_id,
            f"{header}\n\n➡️ <b>Turn:</b> {_e(p1['name'])}",
            reply_markup=board_kb(game["board"], chat_id),
            parse_mode=ParseMode.HTML,
        )
        return   # only start one match at a time


async def record_tournament_result(bot, chat_id: int, winner_id: int, winner_name: str):
    """Called by game_handler after a tournament match finishes."""
    entry = tourn_games.pop(chat_id, None)
    if not entry:
        return

    match               = entry["match"]
    match["winner_id"]   = winner_id
    match["winner_name"] = winner_name
    match["status"]      = "done"

    tourn = await get_tournament(chat_id)
    if not tourn:
        return

    bracket   = tourn.get("bracket", [])
    cur_round = bracket[-1]

    # Check if the whole round is done
    if not all(m["status"] == "done" for m in cur_round):
        # Some matches are still going — save and start next
        await update_tournament(chat_id, {"bracket": bracket})
        await _start_next_match(bot, chat_id, cur_round)
        return

    # Collect winners who are real players (skip BYE entries)
    winners = [
        {"user_id": m["winner_id"], "name": m["winner_name"]}
        for m in cur_round
        if m["winner_id"] is not None
    ]

    if len(winners) == 1:
        # Tournament over!
        await bot.send_message(
            chat_id,
            f"🏆 <b>Tournament Champion!</b>\n\n"
            f"👑 <b>{_e(winners[0]['name'])}</b> wins the whole tournament! 🎉🎊",
            parse_mode=ParseMode.HTML,
        )
        await delete_tournament(chat_id)
        return

    # Build next round
    next_round = []
    for i in range(0, len(winners), 2):
        if i + 1 < len(winners):
            next_round.append({
                "p1":          winners[i],
                "p2":          winners[i + 1],
                "winner_id":   None,
                "winner_name": None,
                "status":      "pending",
            })
        else:
            # Odd player out gets a bye
            next_round.append({
                "p1":          winners[i],
                "p2":          {"user_id": None, "name": "BYE"},
                "winner_id":   winners[i]["user_id"],
                "winner_name": winners[i]["name"],
                "status":      "done",
            })

    bracket.append(next_round)
    rnd_num = len(bracket)
    await update_tournament(chat_id, {"bracket": bracket, "round": tourn["round"] + 1})
    await bot.send_message(
        chat_id,
        f"⚔️ <b>Round {rnd_num} begins!</b>",
        parse_mode=ParseMode.HTML,
    )
    await _start_next_match(bot, chat_id, next_round)
