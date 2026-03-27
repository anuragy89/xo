"""handlers/admin_handler.py – Owner-only broadcast &amp; admin commands."""

import asyncio
import html

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError

from database import get_all_recipients, count_users, count_groups
from config import OWNER_ID


def _e(s) -> str:
    return html.escape(str(s))


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# ── /broadcast ────────────────────────────────────────────
# Usage:
#   /broadcast Your message here
#   — OR —  reply to any message with /broadcast

async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_owner(user.id):
        await update.message.reply_text("⛔ Owner only.")
        return

    # Resolve broadcast text
    text = None
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        text = msg.text or msg.caption
    elif ctx.args:
        text = " ".join(ctx.args)

    if not text:
        await update.message.reply_text(
            "📡 <b>Broadcast Usage</b>\n\n"
            "• <code>/broadcast Your message here</code>\n"
            "• Reply to a message with <code>/broadcast</code>\n\n"
            "Supports HTML formatting.",
            parse_mode=ParseMode.HTML,
        )
        return

    recipients = await get_all_recipients()
    if not recipients:
        await update.message.reply_text("No recipients found.")
        return

    status_msg = await update.message.reply_text(
        f"📡 <b>Broadcasting…</b>\n\nSending to <b>{len(recipients):,}</b> chats…",
        parse_mode=ParseMode.HTML,
    )

    success = 0
    failed  = 0
    for cid in recipients:
        try:
            await ctx.bot.send_message(cid, text, parse_mode=ParseMode.HTML)
            success += 1
        except TelegramError:
            failed += 1
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"✅ <b>Broadcast complete!</b>\n\n"
        f"• 🟢 Delivered: <b>{success:,}</b>\n"
        f"• 🔴 Failed:    <b>{failed:,}</b>",
        parse_mode=ParseMode.HTML,
    )


# ── /adminstats ───────────────────────────────────────────

async def cmd_admin_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_owner(user.id):
        await update.message.reply_text("⛔ Owner only.")
        return

    total_users  = await count_users()
    total_groups = await count_groups()

    await update.message.reply_text(
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users:   <b>{total_users:,}</b>\n"
        f"🏠 Total Groups:  <b>{total_groups:,}</b>\n"
        f"📊 Total Chats:   <b>{total_users + total_groups:,}</b>",
        parse_mode=ParseMode.HTML,
    )
