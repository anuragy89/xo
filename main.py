"""
main.py — Entry point for the XO Telegram Bot.

Supports both webhook (production) and polling (development) modes.
Set USE_WEBHOOK=true in .env for production webhook mode.
"""

import logging
import random
from datetime import time as dt_time, timezone, timedelta

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, USE_WEBHOOK, WEBHOOK_URL, PORT, WEBHOOK_SECRET

# ── Handlers ──────────────────────────────────────────────
from handlers.user_handler import (
    cmd_start, cmd_help, cmd_stats, cmd_top, cmd_grouptop,
    cmd_h2h, cmd_language, cmd_st,
    handle_menu_callbacks, handle_lang_callbacks, on_bot_added,
)
from handlers.game_handler import (
    cmd_xo, cmd_pvp, cmd_pve, cmd_accept, cmd_decline,
    cmd_quit, cmd_board, handle_game_callbacks,
)
from handlers.inline_handler import (
    handle_inline_query, handle_chosen_inline_result,
    handle_inline_callbacks,
)
from handlers.tournament_handler import (
    cmd_tournament, handle_tournament_callbacks,
)
from handlers.daily_handler import cmd_daily, handle_daily_callback
from handlers.coins_handler import cmd_coins, cmd_bet
from handlers.admin_handler import cmd_broadcast, cmd_admin_stats, handle_broadcast_callback

from database import (
    ensure_indexes, get_leaderboard, get_global_daily_stats,
    get_all_group_ids, get_group_leaderboard,
)
import state

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── Daily Stats + Group Rankings Broadcast ────────────────
async def _daily_stats_broadcast(ctx):
    """Sends daily stats + per-group rankings at 1:30 UTC.
    Uses a Redis lock so only one dyno sends the broadcast."""
    from html import escape
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    lock = state.r().lock("lock:daily_broadcast", timeout=300, blocking_timeout=0)
    acquired = await lock.acquire(blocking=False)
    if not acquired:
        logger.info("Daily broadcast: another dyno is handling it.")
        return

    # Inline buttons shown below every broadcast message
    broadcast_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 Global Top", callback_data="cb_leaderboard"),
            InlineKeyboardButton("📢 Updates", url=f"https://t.me/{UPDATE_CHANNEL.lstrip('@')}"),
        ],
        [
            InlineKeyboardButton(
                "➕ Add to Your Group",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
            ),
        ],
    ])

    try:
        logger.info("Daily broadcast: starting...")
        stats  = await get_global_daily_stats()
        board  = await get_leaderboard(5)
        groups = await get_all_group_ids()

        total_games = stats["total_games"]
        total_users = stats["total_users"]

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        # Compact global top-5
        lb_lines = []
        for idx, d in enumerate(board):
            name = escape(d.get("full_name") or d.get("username") or "Unknown")
            elo  = d.get("elo", 1500)
            wins = d.get("wins", 0)
            lb_lines.append(f"{medals[idx]} <b>{name}</b>  <code>{elo} ELO</code>  {wins}W")

        lb_text = "\n".join(lb_lines) if lb_lines else "No players yet!"

        sent = 0
        for gid in groups:
            try:
                # Per-group top-3 only (keep message short)
                grp_board = await get_group_leaderboard(gid, 3)
                grp_block = ""
                if grp_board:
                    grp_lines = []
                    for j, gd in enumerate(grp_board):
                        gname = escape(gd.get("user_name") or "Unknown")
                        gw    = gd.get("wins", 0)
                        gl    = gd.get("losses", 0)
                        grp_lines.append(f"{medals[j]} <b>{gname}</b>  {gw}W/{gl}L")
                    grp_block = "\n\n🏅 <b>Group Top 3</b>\n" + "\n".join(grp_lines)

                text = (
                    "🎮 <b>Daily XO Update</b>\n"
                    f"👥 {total_users:,} players · 🎯 {total_games:,} games\n\n"
                    "🏆 <b>Global Top 5</b>\n"
                    f"{lb_text}"
                    f"{grp_block}\n\n"
                    "📅 /daily  ·  ⚔️ /xo  ·  🤖 /pve"
                )

                await ctx.bot.send_message(
                    gid, text,
                    parse_mode="HTML",
                    reply_markup=broadcast_kb,
                )
                sent += 1
            except Exception:
                pass

        logger.info(f"Daily broadcast: sent to {sent}/{len(groups)} groups.")
    finally:
        try:
            await lock.release()
        except Exception:
            pass


# ── Idle Game Reminder ────────────────────────────────────
# IST = UTC+5:30.  10 PM IST = 16:30 UTC,  6 AM IST = 00:30 UTC
# So "awake hours" in UTC: 00:30 – 16:30
# Runs every hour; checks Redis key for last game activity.

_NUDGE_MESSAGES = [
    "🎮 It's been a while! Who's up for a quick XO match?\n\n/xo — Play with friends\n/pve — Challenge the bot",
    "⚡ The board is gathering dust! Time to make a move.\n\n/xo to start a PvP game\n/pve to play vs Bot",
    "🤖 The bot is bored and wants to play! Challenge it with /pve\nOr play with friends: /xo",
    "❌⭕ Missing some XO action? Jump in!\n\n/xo — Open game, anyone can join\n/pve — Solo challenge",
    "🔥 No games in a while! Let's change that.\n\n/xo for PvP\n/pve for a bot challenge\n/daily for today's puzzle",
    "🏆 Your ELO is waiting to go up! Start a game now.\n\n/xo — PvP\n/pve — vs Bot\n/tournament — Bracket mode!",
    "⬜⬜⬜\n⬜❓⬜\n⬜⬜⬜\n\nThis board needs some action! /xo or /pve",
]


async def _idle_game_reminder(ctx):
    """Checks each group for inactivity. Sends nudge if idle 4-5h during IST daytime."""
    lock = state.r().lock("lock:idle_reminder", timeout=120, blocking_timeout=0)
    acquired = await lock.acquire(blocking=False)
    if not acquired:
        return

    try:
        from datetime import datetime, timezone as tz
        now_utc = datetime.now(tz.utc)
        # IST = UTC + 5:30
        ist_hour = (now_utc.hour + 5 + (1 if now_utc.minute >= 30 else 0)) % 24
        # Skip 10 PM to 6 AM IST (22, 23, 0, 1, 2, 3, 4, 5)
        if ist_hour >= 22 or ist_hour < 6:
            logger.info("Idle reminder: skipping (IST nighttime).")
            return

        groups = await get_all_group_ids()
        import time
        now = time.time()
        sent = 0

        for gid in groups:
            try:
                last_raw = await state.r().get(f"last_game:{gid}")
                last_ts = float(last_raw) if last_raw else 0.0
                hours_idle = (now - last_ts) / 3600.0

                if hours_idle >= 4.0:
                    msg = random.choice(_NUDGE_MESSAGES)
                    await ctx.bot.send_message(gid, msg, parse_mode="HTML")
                    # Reset timer so we don't spam
                    await state.r().set(f"last_game:{gid}", str(now), ex=86400)
                    sent += 1
            except Exception:
                pass

        if sent:
            logger.info(f"Idle reminder: nudged {sent} groups.")
    finally:
        try:
            await lock.release()
        except Exception:
            pass


# ── Post-init: DB indexes + scheduled jobs ───────────────
async def post_init(application: Application) -> None:
    await ensure_indexes()
    logger.info("Database indexes ensured.")

    # Schedule daily stats broadcast at 01:30 UTC (7:00 AM IST)
    application.job_queue.run_daily(
        _daily_stats_broadcast,
        time=dt_time(hour=1, minute=30, tzinfo=timezone.utc),
        name="daily_stats_broadcast",
    )
    logger.info("Scheduled daily stats broadcast at 01:30 UTC.")

    # Schedule idle game reminder — runs every hour
    application.job_queue.run_repeating(
        _idle_game_reminder,
        interval=timedelta(hours=1),
        first=timedelta(minutes=5),
        name="idle_game_reminder",
    )
    logger.info("Scheduled idle game reminder (hourly).")


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # ── Command handlers ─────────────────────────
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("help",       cmd_help))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CommandHandler("top",        cmd_top))
    app.add_handler(CommandHandler("grouptop",   cmd_grouptop))
    app.add_handler(CommandHandler("h2h",        cmd_h2h))
    app.add_handler(CommandHandler("language",   cmd_language))
    app.add_handler(CommandHandler("st",         cmd_st))

    app.add_handler(CommandHandler("xo",         cmd_xo))
    app.add_handler(CommandHandler("pvp",        cmd_pvp))
    app.add_handler(CommandHandler("pve",        cmd_pve))
    app.add_handler(CommandHandler("accept",     cmd_accept))
    app.add_handler(CommandHandler("decline",    cmd_decline))
    app.add_handler(CommandHandler("quit",       cmd_quit))
    app.add_handler(CommandHandler("board",      cmd_board))

    app.add_handler(CommandHandler("tournament", cmd_tournament))
    app.add_handler(CommandHandler("daily",      cmd_daily))
    app.add_handler(CommandHandler("coins",      cmd_coins))
    app.add_handler(CommandHandler("bet",        cmd_bet))

    app.add_handler(CommandHandler("broadcast",  cmd_broadcast))
    app.add_handler(CommandHandler("adminstats", cmd_admin_stats))

    # ── Callback query handlers (pattern-based) ──
    # Order matters: more specific patterns first

    # Inline game callbacks (prefixes: ij, ix, im, irem, ir, in)
    app.add_handler(CallbackQueryHandler(
        handle_inline_callbacks,
        pattern=r"^(ij:|ix:|im:|irem:|ir:|in:)"
    ))

    # Tournament callbacks (prefix: t_)
    app.add_handler(CallbackQueryHandler(
        handle_tournament_callbacks,
        pattern=r"^t_(create|join|cancel|start):"
    ))

    # Daily puzzle callbacks
    app.add_handler(CallbackQueryHandler(
        handle_daily_callback,
        pattern=r"^daily:"
    ))

    # Broadcast callbacks (admin)
    app.add_handler(CallbackQueryHandler(
        handle_broadcast_callback,
        pattern=r"^bc:"
    ))

    # Language callbacks
    app.add_handler(CallbackQueryHandler(
        handle_lang_callbacks,
        pattern=r"^lang:"
    ))

    # Menu callbacks (cb_)
    app.add_handler(CallbackQueryHandler(
        handle_menu_callbacks,
        pattern=r"^cb_"
    ))

    # Game callbacks — catch-all for game-related data
    # (xo_join, xo_cancel, xo_new, ch_accept, ch_decline,
    #  diff, char, rematch, revenge, mv, noop, cb_pick_difficulty)
    app.add_handler(CallbackQueryHandler(handle_game_callbacks))

    # ── Inline mode ──────────────────────────────
    app.add_handler(InlineQueryHandler(handle_inline_query))
    app.add_handler(ChosenInlineResultHandler(handle_chosen_inline_result))

    # ── Bot added to group ───────────────────────
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        on_bot_added,
    ))

    # ── Run ──────────────────────────────────────
    if USE_WEBHOOK:
        logger.info(f"Starting webhook on port {PORT}...")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}",
            secret_token=WEBHOOK_SECRET,
        )
    else:
        logger.info("Starting polling...")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
