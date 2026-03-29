"""handlers/admin_handler.py – Owner-only broadcast & admin commands."""

import asyncio
import html

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
# Then pick target + pin option from inline buttons.

async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_owner(user.id):
        await update.message.reply_text("⛔ Owner only.")
        return

    # Resolve broadcast text
    text = None
    reply_msg = None
    if update.message.reply_to_message:
        reply_msg = update.message.reply_to_message
        text = reply_msg.text_html or reply_msg.caption
    elif ctx.args:
        text = " ".join(ctx.args)

    if not text:
        await update.message.reply_text(
            "📡 <b>Broadcast Usage</b>\n\n"
            "• <code>/broadcast Your message here</code>\n"
            "• Reply to a message with <code>/broadcast</code>\n\n"
            "Supports HTML formatting.\n"
            "You'll pick target audience &amp; pin option next.",
            parse_mode=ParseMode.HTML,
        )
        return

    # Store in context for callback
    ctx.user_data["bc_text"] = text
    if reply_msg:
        ctx.user_data["bc_photo_id"] = reply_msg.photo[-1].file_id if reply_msg.photo else None
        ctx.user_data["bc_video_id"] = reply_msg.video.file_id if reply_msg.video else None
        ctx.user_data["bc_doc_id"] = reply_msg.document.file_id if reply_msg.document else None
    else:
        ctx.user_data["bc_photo_id"] = None
        ctx.user_data["bc_video_id"] = None
        ctx.user_data["bc_doc_id"] = None

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Groups Only", callback_data="bc:groups:nopin"),
         InlineKeyboardButton("👤 Users Only",  callback_data="bc:users:nopin")],
        [InlineKeyboardButton("🌐 All Chats",   callback_data="bc:all:nopin")],
        [InlineKeyboardButton("📌 Groups + Pin", callback_data="bc:groups:pin"),
         InlineKeyboardButton("📌 All + Pin",    callback_data="bc:all:pin")],
        [InlineKeyboardButton("❌ Cancel",       callback_data="bc:cancel:x")],
    ])

    total_users  = await count_users()
    total_groups = await count_groups()
    preview = text[:200] + ('\u2026' if len(text) > 200 else '')

    await update.message.reply_text(
        f"📡 <b>Broadcast Preview</b>\n\n"
        f"<blockquote>{preview}</blockquote>\n\n"
        f"👤 Users: <b>{total_users:,}</b> | 👥 Groups: <b>{total_groups:,}</b>\n\n"
        f"Choose target &amp; pin option:",
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )


async def handle_broadcast_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = query.from_user

    if not _is_owner(user.id):
        await query.answer("⛔ Owner only.", show_alert=True)
        return

    await query.answer()

    parts  = query.data.split(":")
    target = parts[1]  # groups / users / all / cancel
    pin    = parts[2]  # pin / nopin / x

    if target == "cancel":
        for k in ("bc_text", "bc_photo_id", "bc_video_id", "bc_doc_id"):
            ctx.user_data.pop(k, None)
        await query.edit_message_text("❌ Broadcast cancelled.")
        return

    text     = ctx.user_data.pop("bc_text", None)
    photo_id = ctx.user_data.pop("bc_photo_id", None)
    video_id = ctx.user_data.pop("bc_video_id", None)
    doc_id   = ctx.user_data.pop("bc_doc_id", None)

    if not text:
        await query.edit_message_text("⚠️ Broadcast text expired. Run /broadcast again.")
        return

    do_pin = pin == "pin"
    recipients = await get_all_recipients(target)

    target_label = {"groups": "groups", "users": "users", "all": "all chats"}[target]
    await query.edit_message_text(
        f"📡 <b>Broadcasting\u2026</b>\n\n"
        f"Sending to <b>{len(recipients):,}</b> {target_label}\u2026"
        f"{'  📌 with pin' if do_pin else ''}",
        parse_mode=ParseMode.HTML,
    )

    success = 0
    failed  = 0
    pinned  = 0

    for cid in recipients:
        try:
            if photo_id:
                sent = await ctx.bot.send_photo(
                    cid, photo_id, caption=text, parse_mode=ParseMode.HTML,
                )
            elif video_id:
                sent = await ctx.bot.send_video(
                    cid, video_id, caption=text, parse_mode=ParseMode.HTML,
                )
            elif doc_id:
                sent = await ctx.bot.send_document(
                    cid, doc_id, caption=text, parse_mode=ParseMode.HTML,
                )
            else:
                sent = await ctx.bot.send_message(
                    cid, text, parse_mode=ParseMode.HTML,
                )
            success += 1

            if do_pin and cid < 0:  # only pin in groups (negative IDs)
                try:
                    await ctx.bot.pin_chat_message(
                        cid, sent.message_id, disable_notification=True,
                    )
                    pinned += 1
                except TelegramError:
                    pass
        except TelegramError:
            failed += 1
        await asyncio.sleep(0.05)

    pin_line = f"\n• 📌 Pinned:    <b>{pinned:,}</b>" if do_pin else ""
    await query.edit_message_text(
        f"✅ <b>Broadcast complete!</b>\n\n"
        f"• 🟢 Delivered: <b>{success:,}</b>\n"
        f"• 🔴 Failed:    <b>{failed:,}</b>"
        f"{pin_line}",
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
