"""
emojis.py — Central emoji configuration for the XO bot.

Telegram Bot API 9.4+ allows bots to use custom (premium) emoji in messages
if the bot owner has a Telegram Premium subscription.

HTML syntax:  <tg-emoji emoji-id="ID">FALLBACK</tg-emoji>

HOW TO USE:
  1. Set USE_CUSTOM_EMOJI = True below (requires bot owner Telegram Premium).
  2. Replace the empty strings "" with custom emoji sticker IDs.
     To find an emoji ID, forward a custom emoji sticker to @RawDataBot.
  3. The bot will render <tg-emoji> tags automatically.
     If a custom ID is empty, the Unicode fallback is used instead.

Button emoji:
  Bot API 9.4 also added icon_custom_emoji_id to InlineKeyboardButton.
  The btn_emoji() helper returns the ID (or None) for use in keyboard builders.
"""

import os

# ── Master Toggle ─────────────────────────────────────────
# Set via env var or flip here directly.
USE_CUSTOM_EMOJI = os.getenv("USE_CUSTOM_EMOJI", "1").lower() in ("1", "true", "yes")


# ── Emoji Definitions ─────────────────────────────────────
# Format:  "key": ("custom_emoji_id", "unicode_fallback")
#
# Leave custom_emoji_id as "" to use the Unicode fallback.
# When you have premium custom emoji IDs, paste them here.

EMOJIS: dict[str, tuple[str, str]] = {

    # ── Game Board ────────────────────────────────
    "x_mark":       ("5854929766146118183", "❌"),
    "o_mark":       ("", "⭕"),
    "empty_cell":   ("", "⬜"),

    # ── Game UI ───────────────────────────────────
    "game":         ("", "🎮"),
    "trophy":       ("", "🏆"),
    "swords":       ("5985307458376044631", "⚔️"),    # 🗡 animated sword
    "robot":        ("", "🤖"),
    "fire":         ("", "🔥"),
    "lightning":    ("", "⚡"),
    "sparkles":     ("4956259055468282692", "✨"),     # 🌟 animated star
    "target":       ("", "🎯"),
    "handshake":    ("", "🤝"),
    "arrow_right":  ("", "➡️"),
    "hourglass":    ("5451732530048802485", "⏳"),     # ⏳ animated hourglass
    "warning":      ("5220197908342648622", "⚠️"),    # ❗ animated exclamation
    "white_flag":   ("", "🏳️"),
    "refresh":      ("", "🔄"),
    "magnify":      ("5942826671290715541", "🔍"),    # 🔎 animated magnifier
    "calendar":     ("", "📅"),
    "chart_up":     ("", "📈"),
    "chart_bar":    ("", "📊"),

    # ── Economy ───────────────────────────────────
    "coins":        ("5375296873982604963", "💰"),    # 💰 animated money bag
    "money_fly":    ("5258391025281408576", "💸"),    # 💸 animated money wings
    "party":        ("5388674524583572460", "🎉"),    # 🎉 animated party popper
    "check":        ("5778393650794860280", "✅"),    # ✅ animated check mark
    "cross":        ("5854929766146118183", "❌"),    # ❌ animated cross mark

    # ── Streaks & Milestones ──────────────────────
    "streak":       ("", "🔥"),
    "broken_heart": ("", "💔"),
    "star":         ("4956259055468282692", "🌟"),    # 🌟 animated star
    "crown":        ("", "👑"),
    "rocket":       ("", "🚀"),
    "medal":        ("", "🏅"),
    "muscle":       ("", "💪"),

    # ── Characters: Devil ─────────────────────────
    "devil":        ("5472015727852526093", "😈"),    # 👿 animated imp
    "skull":        ("", "💀"),

    # ── Characters: Nerd ──────────────────────────
    "nerd":         ("5472100935708711380", "🤓"),    # 😎 animated cool face
    "laptop":       ("5366288132834599020", "💻"),    # 💻 animated laptop

    # ── Characters: Grandma ───────────────────────
    "grandma":      ("", "😴"),
    "cookie":       ("", "🍪"),
    "smile":        ("5472291035256201250", "😊"),    # 😋 animated yummy face
    "flower":       ("", "🌸"),

    # ── Navigation / Info ─────────────────────────
    "wave":         ("5472427507842032538", "👋"),    # 👋 animated wave
    "people":       ("5258513401784573443", "👥"),    # 👥 animated people
    "house":        ("", "🏠"),
    "book":         ("", "📖"),
    "globe":        ("5447410659077661506", "🌐"),    # 🌐 animated globe
    "megaphone":    ("", "📢"),
    "gear":         ("5258096772776991776", "⚙️"),    # ⚙️ animated gear
    "sunrise":      ("", "🌅"),
    "question":     ("", "❓"),
    "world":        ("5417875345804108985", "🌍"),    # 🌍 animated earth

    # ── Leaderboard Medals ────────────────────────
    "gold":         ("", "🥇"),
    "silver":       ("", "🥈"),
    "bronze":       ("", "🥉"),
    "blue_diamond": ("", "🔹"),
}


# ── Helper Functions ──────────────────────────────────────

def em(key: str) -> str:
    """
    Return the emoji for the given key.

    If USE_CUSTOM_EMOJI is True and a custom emoji ID is set,
    returns an HTML <tg-emoji> tag.  Otherwise returns the Unicode fallback.
    """
    entry = EMOJIS.get(key)
    if not entry:
        return "❓"
    eid, fallback = entry
    if USE_CUSTOM_EMOJI and eid:
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    return fallback


def btn_emoji(key: str) -> str | None:
    """
    Return the custom emoji ID for use in InlineKeyboardButton(icon_custom_emoji_id=...).

    Returns None if custom emoji is disabled or no ID is set for this key.
    """
    entry = EMOJIS.get(key)
    if not entry:
        return None
    eid, _ = entry
    if USE_CUSTOM_EMOJI and eid:
        return eid
    return None


# ── Pre-built game board emoji dict ───────────────────────
# This mirrors game.py's CELL_EMOJI but respects custom emoji config.

def get_cell_emoji() -> dict:
    """Return {0: empty, 1: X, -1: O} emoji mapping."""
    return {
        0:  em("empty_cell"),
        1:  em("x_mark"),
        -1: em("o_mark"),
    }
