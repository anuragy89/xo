"""
i18n.py – Internationalization (English / Arabic / Hindi)
All strings use HTML formatting (<b>, <i>, <code>).
Usage:  from i18n import t
        t("welcome_dm", lang, name="Ahmed", users=1000, groups=50)
"""

STRINGS = {

# ──────────────────────────────────────────────────────────
"en": {
    "welcome_dm": (
        "👋 Hello, <b>{name}</b>!\n\n"
        "🎮 <b>XO Bot</b> — Tic-Tac-Toe for Telegram\n\n"
        "✨ <b>Features:</b>\n"
        "┣ ⚔️ PvP — Challenge your friends\n"
        "┣ 🤖 vs Bot — 3 difficulty levels\n"
        "┣ 🏆 Tournaments — Bracket system\n"
        "┣ 💰 Coins &amp; Betting system\n"
        "┣ 🔥 Streaks &amp; ELO rating\n"
        "┗ 📅 Daily challenges for free coins\n\n"
        "👥 <b>{users:,}</b> users  •  🏠 <b>{groups:,}</b> groups"
    ),
    "welcome_group": (
        "🎮 <b>XO Bot has entered the chat!</b>\n\n"
        "Play Tic-Tac-Toe right here — no links, no apps!\n\n"
        "┣ ⚔️ <code>/pvp @player</code> — Challenge someone\n"
        "┣ 🤖 <code>/pve</code> — Play vs AI bot\n"
        "┣ 🏆 <code>/tournament</code> — Start a bracket\n"
        "┣ 📅 <code>/daily</code> — Daily puzzle (+coins)\n"
        "┣ 💰 <code>/coins</code> — Your balance\n"
        "┣ 📊 <code>/stats</code> — Your stats\n"
        "┗ ❓ <code>/help</code> — All commands"
    ),
    "help": (
        "📖 <b>Help &amp; Commands</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎮 Game</b>\n"
        "<code>/pvp @user</code> — Challenge a player\n"
        "<code>/pve</code> — Play vs AI bot\n"
        "<code>/accept</code> — Accept a challenge\n"
        "<code>/decline</code> — Decline a challenge\n"
        "<code>/board</code> — Redisplay the board\n"
        "<code>/quit</code> — Abandon current game\n\n"
        "<b>🏆 Tournament</b>\n"
        "<code>/tournament</code> — Start or join a bracket (4 or 8 players)\n\n"
        "<b>💰 Economy</b>\n"
        "<code>/coins</code> — Your coin balance\n"
        "<code>/bet &lt;amount&gt;</code> — Bet before a game\n"
        "<code>/daily</code> — Daily puzzle for free coins\n\n"
        "<b>📊 Stats</b>\n"
        "<code>/stats</code> — Wins, losses, ELO, streak\n"
        "<code>/top</code> — Global ELO leaderboard\n"
        "<code>/grouptop</code> — This group's top 10\n\n"
        "<b>⚙️ Settings</b>\n"
        "<code>/language</code> — Change language 🌐\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Bot difficulty: Easy / Medium / Hard (unbeatable Minimax AI)</i>"
    ),
    "your_turn":          "➡️ <b>Your turn!</b>",
    "bot_thinking":       "🤖 <b>Bot is thinking...</b>",
    "game_started":       "🎮 <b>Game started!</b> Good luck!",
    "you_are_x":          "You are ❌ — make the first move!",
    "win":                "🏆 <b>{name}</b> wins! {mark}",
    "draw":               "🤝 <b>It's a Draw!</b>",
    "not_your_turn":      "⏳ It's not your turn!",
    "not_in_game":        "You're not in this game!",
    "cell_taken":         "That cell is already taken!",
    "game_running":       "⚠️ A game is already running here! Use /quit to end it first.",
    "no_game":            "No active game! Start one with /pvp @user or /pve",
    "quit_msg":           "🏳️ {name} quit the game.",
    "challenge_sent":     "⚔️ {challenger} challenges {target}!\n\nTap a button to respond: ❌ vs ⭕",
    "challenge_expired":  "❌ This challenge has expired.",
    "cant_self":          "You can't challenge yourself! 😄",
    "pvp_dm_only":        "⚠️ PvP mode only works in groups! Add me to a group first.",
    "choose_difficulty":  "🤖 <b>Player vs Bot</b>\n\n{name}, choose difficulty level:",
    "only_challenger":    "Only the challenger can pick the difficulty!",
    "elo_change":         "📈 <b>{name}</b> ELO: {before} → {after} ({delta:+d})",
    "coins_earned_win":   "💰 <b>{name}</b> earned <b>+{amount} coins!</b>",
    "coins_earned_draw":  "💰 Both players earned <b>+{amount} coins!</b>",
    "streak_msg":         "🔥 <b>{name}</b> is on a <b>{streak}-win streak!</b>",
    "streak_broken":      "💔 <b>{name}</b>'s {streak}-win streak is broken!",
    "milestone_10":       "🎉 <b>{name}</b> just hit <b>10 wins</b> in this group! Legend! 🏆",
    "milestone_25":       "🌟 <b>{name}</b> smashed <b>25 wins</b> in this group! Unstoppable! 💪",
    "milestone_50":       "👑 <b>{name}</b> reached <b>50 wins</b> in this group! Absolute GOD! 🔥",
    "milestone_100":      "🚀 <b>{name}</b> achieved <b>100 wins</b> in this group! HALL OF FAME! 🏅",
    "daily_title":        "📅 <b>Daily Challenge</b>",
    "daily_done":         "✅ You've already completed today's challenge!\nCome back tomorrow for a new puzzle! 🌅",
    "daily_reward":       "🎉 <b>Correct!</b> You earned <b>+{coins} coins!</b>",
    "daily_fail":         "❌ Wrong move!\n\nThe winning move was cell <b>#{cell}</b>.\nBetter luck tomorrow! 💪",
    "no_coins":           "💸 Not enough coins!\nYour balance: <b>{balance} coins</b>",
    "bet_placed":         "💰 Bet of <b>{amount} coins</b> placed!\nWinner takes the pot! 🎯",
    "bet_won":            "💰 Bet won! <b>+{amount} coins</b> 🎉",
    "bet_lost":           "💸 Bet lost! <b>-{amount} coins</b>",
    "balance":            "💰 Your balance: <b>{balance} coins</b>",
    "lang_changed":       "✅ Language set to <b>English</b>!",
},

# ──────────────────────────────────────────────────────────
"ar": {
    "welcome_dm": (
        "👋 مرحباً، <b>{name}</b>!\n\n"
        "🎮 <b>XO Bot</b> — لعبة إكس-أو على تيليغرام\n\n"
        "✨ <b>المميزات:</b>\n"
        "┣ ⚔️ لاعب ضد لاعب\n"
        "┣ 🤖 لاعب ضد البوت (3 مستويات)\n"
        "┣ 🏆 بطولات بنظام الأدوار\n"
        "┣ 💰 نظام العملات والرهانات\n"
        "┣ 🔥 سلاسل الفوز وتقييم ELO\n"
        "┗ 📅 تحديات يومية للعملات المجانية\n\n"
        "👥 <b>{users:,}</b> مستخدم  •  🏠 <b>{groups:,}</b> مجموعة"
    ),
    "welcome_group": (
        "🎮 <b>XO Bot وصل للمجموعة!</b>\n\n"
        "العب إكس-أو هنا مباشرة!\n\n"
        "┣ ⚔️ <code>/pvp @player</code> — تحدي لاعب\n"
        "┣ 🤖 <code>/pve</code> — العب ضد البوت\n"
        "┣ 🏆 <code>/tournament</code> — ابدأ بطولة\n"
        "┣ 📅 <code>/daily</code> — تحدي يومي (+عملات)\n"
        "┣ 💰 <code>/coins</code> — رصيدك\n"
        "┣ 📊 <code>/stats</code> — إحصائياتك\n"
        "┗ ❓ <code>/help</code> — جميع الأوامر"
    ),
    "help": (
        "📖 <b>المساعدة والأوامر</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎮 اللعبة</b>\n"
        "<code>/pvp @user</code> — تحدي لاعب\n"
        "<code>/pve</code> — العب ضد البوت\n"
        "<code>/accept</code> — قبول التحدي\n"
        "<code>/decline</code> — رفض التحدي\n"
        "<code>/board</code> — عرض اللوحة\n"
        "<code>/quit</code> — الخروج من اللعبة\n\n"
        "<b>🏆 البطولة</b>\n"
        "<code>/tournament</code> — ابدأ أو انضم (4 أو 8 لاعبين)\n\n"
        "<b>💰 الاقتصاد</b>\n"
        "<code>/coins</code> — رصيدك\n"
        "<code>/bet &lt;مبلغ&gt;</code> — راهن قبل اللعبة\n"
        "<code>/daily</code> — تحدي يومي مجاني\n\n"
        "<b>📊 الإحصاء</b>\n"
        "<code>/stats</code> — إحصائياتك وELO\n"
        "<code>/top</code> — أفضل 10 عالمياً\n"
        "<code>/grouptop</code> — أفضل 10 في المجموعة\n\n"
        "<b>⚙️ الإعدادات</b>\n"
        "<code>/language</code> — تغيير اللغة 🌐\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    ),
    "your_turn":          "➡️ <b>دورك!</b>",
    "bot_thinking":       "🤖 <b>البوت يفكر...</b>",
    "game_started":       "🎮 <b>بدأت اللعبة!</b> حظاً موفقاً!",
    "you_are_x":          "أنت ❌ — ابدأ أول حركة!",
    "win":                "🏆 <b>{name}</b> فاز! {mark}",
    "draw":               "🤝 <b>تعادل!</b>",
    "not_your_turn":      "⏳ ليس دورك!",
    "not_in_game":        "أنت لست في هذه اللعبة!",
    "cell_taken":         "هذه الخانة مشغولة!",
    "game_running":       "⚠️ توجد لعبة جارية! استخدم /quit أولاً.",
    "no_game":            "لا توجد لعبة! ابدأ بـ /pvp @user أو /pve",
    "quit_msg":           "🏳️ {name} خرج من اللعبة.",
    "challenge_sent":     "⚔️ {challenger} يتحدى {target}!\n\nاضغط للرد: ❌ vs ⭕",
    "challenge_expired":  "❌ انتهت صلاحية التحدي.",
    "cant_self":          "لا يمكنك تحدي نفسك! 😄",
    "pvp_dm_only":        "⚠️ PvP يعمل في المجموعات فقط! أضفني لمجموعة أولاً.",
    "choose_difficulty":  "🤖 <b>لاعب ضد البوت</b>\n\n{name}، اختر مستوى الصعوبة:",
    "only_challenger":    "فقط من أرسل التحدي يمكنه اختيار الصعوبة!",
    "elo_change":         "📈 <b>{name}</b> ELO: {before} → {after} ({delta:+d})",
    "coins_earned_win":   "💰 <b>{name}</b> كسب <b>+{amount} عملة!</b>",
    "coins_earned_draw":  "💰 كلا اللاعبين كسبا <b>+{amount} عملة!</b>",
    "streak_msg":         "🔥 <b>{name}</b> لديه <b>{streak} انتصارات متتالية!</b>",
    "streak_broken":      "💔 سلسلة انتصارات <b>{name}</b> ({streak}) انقطعت!",
    "milestone_10":       "🎉 <b>{name}</b> وصل لـ <b>10 انتصارات</b> في المجموعة! أسطورة! 🏆",
    "milestone_25":       "🌟 <b>{name}</b> حطم <b>25 انتصاراً</b>! لا يُوقف! 💪",
    "milestone_50":       "👑 <b>{name}</b> وصل لـ <b>50 انتصاراً</b>! إله! 🔥",
    "milestone_100":      "🚀 <b>{name}</b> حقق <b>100 انتصار</b>! 🏅",
    "daily_title":        "📅 <b>التحدي اليومي</b>",
    "daily_done":         "✅ أكملت تحدي اليوم! عد غداً! 🌅",
    "daily_reward":       "🎉 <b>صحيح!</b> ربحت <b>+{coins} عملة!</b>",
    "daily_fail":         "❌ إجابة خاطئة!\n\nالصحيح كان الخانة <b>#{cell}</b>.\nحظ أوفر غداً! 💪",
    "no_coins":           "💸 عملاتك غير كافية!\nرصيدك: <b>{balance} عملة</b>",
    "bet_placed":         "💰 رهان <b>{amount} عملة</b> تم! الفائز يأخذ الكل! 🎯",
    "bet_won":            "💰 ربحت الرهان! <b>+{amount} عملة</b> 🎉",
    "bet_lost":           "💸 خسرت الرهان! <b>-{amount} عملة</b>",
    "balance":            "💰 رصيدك: <b>{balance} عملة</b>",
    "lang_changed":       "✅ تم تغيير اللغة إلى <b>العربية</b>!",
},

# ──────────────────────────────────────────────────────────
"hi": {
    "welcome_dm": (
        "👋 नमस्ते, <b>{name}</b>!\n\n"
        "🎮 <b>XO Bot</b> — Telegram के लिए Tic-Tac-Toe\n\n"
        "✨ <b>खूबियाँ:</b>\n"
        "┣ ⚔️ PvP — दोस्तों को चुनौती दें\n"
        "┣ 🤖 vs Bot — 3 कठिनाई स्तर\n"
        "┣ 🏆 टूर्नामेंट — ब्रैकेट सिस्टम\n"
        "┣ 💰 कॉइन और बेटिंग सिस्टम\n"
        "┣ 🔥 स्ट्रीक और ELO रेटिंग\n"
        "┗ 📅 फ्री कॉइन के लिए डेली चैलेंज\n\n"
        "👥 <b>{users:,}</b> यूज़र  •  🏠 <b>{groups:,}</b> ग्रुप"
    ),
    "welcome_group": (
        "🎮 <b>XO Bot आ गया!</b>\n\n"
        "सीधे यहाँ Tic-Tac-Toe खेलें!\n\n"
        "┣ ⚔️ <code>/pvp @player</code> — किसी को चुनौती दें\n"
        "┣ 🤖 <code>/pve</code> — Bot से खेलें\n"
        "┣ 🏆 <code>/tournament</code> — टूर्नामेंट शुरू करें\n"
        "┣ 📅 <code>/daily</code> — डेली चैलेंज (+कॉइन)\n"
        "┣ 💰 <code>/coins</code> — आपका बैलेंस\n"
        "┣ 📊 <code>/stats</code> — आपके आँकड़े\n"
        "┗ ❓ <code>/help</code> — सभी कमांड"
    ),
    "help": (
        "📖 <b>सहायता और कमांड</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎮 गेम</b>\n"
        "<code>/pvp @user</code> — खिलाड़ी को चुनौती\n"
        "<code>/pve</code> — Bot से खेलें\n"
        "<code>/accept</code> — चुनौती स्वीकार\n"
        "<code>/decline</code> — चुनौती अस्वीकार\n"
        "<code>/board</code> — बोर्ड दिखाएँ\n"
        "<code>/quit</code> — गेम छोड़ें\n\n"
        "<b>🏆 टूर्नामेंट</b>\n"
        "<code>/tournament</code> — शुरू/जॉइन करें (4 या 8 खिलाड़ी)\n\n"
        "<b>💰 इकॉनमी</b>\n"
        "<code>/coins</code> — आपका बैलेंस\n"
        "<code>/bet &lt;राशि&gt;</code> — गेम से पहले बेट\n"
        "<code>/daily</code> — डेली चैलेंज (+कॉइन)\n\n"
        "<b>📊 आँकड़े</b>\n"
        "<code>/stats</code> — जीत/हार/ELO/स्ट्रीक\n"
        "<code>/top</code> — ग्लोबल टॉप 10\n"
        "<code>/grouptop</code> — इस ग्रुप का टॉप 10\n\n"
        "<b>⚙️ सेटिंग्स</b>\n"
        "<code>/language</code> — भाषा बदलें 🌐\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    ),
    "your_turn":          "➡️ <b>आपकी बारी!</b>",
    "bot_thinking":       "🤖 <b>Bot सोच रहा है...</b>",
    "game_started":       "🎮 <b>गेम शुरू!</b> शुभकामनाएँ!",
    "you_are_x":          "आप ❌ हैं — पहली चाल चलें!",
    "win":                "🏆 <b>{name}</b> जीत गया! {mark}",
    "draw":               "🤝 <b>ड्रॉ!</b>",
    "not_your_turn":      "⏳ अभी आपकी बारी नहीं है!",
    "not_in_game":        "आप इस गेम में नहीं हैं!",
    "cell_taken":         "यह सेल भरा हुआ है!",
    "game_running":       "⚠️ गेम चल रहा है! पहले /quit करें।",
    "no_game":            "कोई गेम नहीं! /pvp @user या /pve से शुरू करें",
    "quit_msg":           "🏳️ {name} ने गेम छोड़ दिया।",
    "challenge_sent":     "⚔️ {challenger} ने {target} को चुनौती दी!\n\nजवाब देने के लिए टैप करें: ❌ vs ⭕",
    "challenge_expired":  "❌ यह चुनौती समाप्त हो गई।",
    "cant_self":          "खुद को चुनौती नहीं दे सकते! 😄",
    "pvp_dm_only":        "⚠️ PvP ग्रुप के लिए है! पहले मुझे ग्रुप में जोड़ें।",
    "choose_difficulty":  "🤖 <b>खिलाड़ी vs Bot</b>\n\n{name}, कठिनाई स्तर चुनें:",
    "only_challenger":    "केवल चुनौती देने वाला कठिनाई चुन सकता है!",
    "elo_change":         "📈 <b>{name}</b> ELO: {before} → {after} ({delta:+d})",
    "coins_earned_win":   "💰 <b>{name}</b> को <b>+{amount} कॉइन</b> मिले!",
    "coins_earned_draw":  "💰 दोनों खिलाड़ियों को <b>+{amount} कॉइन</b> मिले!",
    "streak_msg":         "🔥 <b>{name}</b> की <b>{streak} जीत की लकीर!</b>",
    "streak_broken":      "💔 <b>{name}</b> की {streak}-जीत की लकीर टूट गई!",
    "milestone_10":       "🎉 <b>{name}</b> ने इस ग्रुप में <b>10 जीत</b> हासिल की! लीजेंड! 🏆",
    "milestone_25":       "🌟 <b>{name}</b> ने <b>25 जीत</b> तोड़ी! अजेय! 💪",
    "milestone_50":       "👑 <b>{name}</b> ने <b>50 जीत</b> छुई! देवता! 🔥",
    "milestone_100":      "🚀 <b>{name}</b> ने <b>100 जीत</b> हासिल की! 🏅",
    "daily_title":        "📅 <b>डेली चैलेंज</b>",
    "daily_done":         "✅ आज का चैलेंज पूरा हो गया!\nकल वापस आएँ! 🌅",
    "daily_reward":       "🎉 <b>सही!</b> आपको <b>+{coins} कॉइन</b> मिले!",
    "daily_fail":         "❌ गलत चाल!\n\nसही जवाब था सेल <b>#{cell}</b>।\nकल बेहतर करें! 💪",
    "no_coins":           "💸 पर्याप्त कॉइन नहीं!\nबैलेंस: <b>{balance} कॉइन</b>",
    "bet_placed":         "💰 <b>{amount} कॉइन</b> की बेट लगी! जीतने वाला सब लेगा! 🎯",
    "bet_won":            "💰 बेट जीती! <b>+{amount} कॉइन</b> 🎉",
    "bet_lost":           "💸 बेट हारी! <b>-{amount} कॉइन</b>",
    "balance":            "💰 आपका बैलेंस: <b>{balance} कॉइन</b>",
    "lang_changed":       "✅ भाषा <b>हिंदी</b> में सेट की गई!",
},

}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """
    Translate key in given language with optional format args.
    Falls back to English if key or language not found.
    """
    lang_strings = STRINGS.get(lang, STRINGS["en"])
    template = lang_strings.get(key) or STRINGS["en"].get(key, key)
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template
