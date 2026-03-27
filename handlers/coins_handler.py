"""handlers/coins_handler.py – Coin balance &amp; pre-game betting."""

import html

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import (
    save_user, get_user_coins, deduct_coins, add_coins, get_user_lang,
)
from i18n import t
import state


def _e(s) -> str:
    return html.escape(str(s))


# ── /coins ────────────────────────────────────────────────

async def cmd_coins(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await save_user(user)
    lang = await get_user_lang(user.id)
    bal  = await get_user_coins(user.id)
    await update.message.reply_text(
        t("balance", lang, balance=bal),
        parse_mode=ParseMode.HTML,
    )


# ── /bet ──────────────────────────────────────────────────

async def cmd_bet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    await save_user(user)
    lang = await get_user_lang(user.id)

    if not ctx.args:
        await update.message.reply_text(
            "💰 <b>Betting</b>\n\n"
            "Place a bet before starting a game.\n"
            "If you win, you take the pot!\n\n"
            "Usage: <code>/bet &lt;amount&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        amount = int(ctx.args[0])
        if amount <= 0:
            raise ValueError("Must be positive")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid positive number.")
        return

    bal = await get_user_coins(user.id)
    if bal < amount:
        await update.message.reply_text(
            t("no_coins", lang, balance=bal),
            parse_mode=ParseMode.HTML,
        )
        return

    await state.set_bet(chat_id, user.id, amount)

    await update.message.reply_text(
        t("bet_placed", lang, amount=amount),
        parse_mode=ParseMode.HTML,
    )


# ── Helpers used by game_handler ──────────────────────────

async def get_bet(chat_id: int, user_id: int) -> int:
    bets = await state.get_bets(chat_id)
    return bets.get(user_id, 0)


async def clear_bets(chat_id: int) -> None:
    await state.clear_bets(chat_id)


async def resolve_bets(chat_id: int, winner_id: int, loser_id: int, lang: str = "en") -> str:
    """
    Deduct from loser, credit to winner.
    Returns a formatted result string (or empty string if no bet).
    """
    bets = await state.pop_bets(chat_id)
    if not bets:
        return ""

    winner_bet = bets.get(winner_id, 0)
    loser_bet  = bets.get(loser_id,  0)
    pot        = min(winner_bet, loser_bet)

    if pot <= 0:
        return ""

    # Deduct from loser first; if they can't afford it, skip
    ok = await deduct_coins(loser_id, pot)
    if not ok:
        return ""

    await add_coins(winner_id, pot)
    return f"\n\n{t('bet_won', lang, amount=pot)}"
