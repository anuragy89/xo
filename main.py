"""
main.py — Entry point for the XO Telegram Bot.

Supports both webhook (production) and polling (development) modes.
Set USE_WEBHOOK=true in .env for production webhook mode.
"""

import logging

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
from handlers.admin_handler import cmd_broadcast, cmd_admin_stats
from handlers.wordsearch_handler import (
    cmd_wordsearch, cmd_endws, cmd_hint, handle_ws_guess,
)

from database import ensure_indexes

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── Post-init: DB indexes ────────────────────────────────
async def post_init(application: Application) -> None:
    await ensure_indexes()
    logger.info("Database indexes ensured.")


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

    app.add_handler(CommandHandler("wordsearch", cmd_wordsearch))
    app.add_handler(CommandHandler("ws",         cmd_wordsearch))
    app.add_handler(CommandHandler("endws",      cmd_endws))
    app.add_handler(CommandHandler("hint",       cmd_hint))

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
    # ── Word Search guess handler (text messages in groups) ──
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        handle_ws_guess,
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
