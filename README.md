<h1 align="center">🎮 XO Bot — Competitive Tic-Tac-Toe for Telegram</h1>

<p align="center">
  <b>PvP • AI Characters • Tournaments • ELO Rating • Inline Mode • Coins & Betting</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white" alt="Python 3.13">
  <img src="https://img.shields.io/badge/python--telegram--bot-22.7+-blue?logo=telegram" alt="PTB 22.7">
  <img src="https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb" alt="MongoDB">
  <img src="https://img.shields.io/badge/Redis-Async-red?logo=redis" alt="Redis">
  <img src="https://img.shields.io/badge/Deploy-Heroku%20%7C%20Docker-purple?logo=heroku" alt="Heroku/Docker">
</p>

---

## ✨ Features

### 🎮 Game Modes
- **PvP (Player vs Player)** — Challenge friends with `/pvp @user` or create an open lobby with `/xo` that anyone can join
- **PvE (Player vs Bot)** — Play against AI with 3 difficulty levels and 3 unique bot characters
- **Inline Mode** — Start games in **any chat** by typing `@YourBotName` — supports both PvP and PvE
- **Tournaments** — Single-elimination bracket tournaments for 4 or 8 players in groups

### 🤖 AI Characters
Each character has unique personality dialogue for wins, losses, draws, and thinking:

| Character | Difficulty Behavior | Personality |
|-----------|-------------------|-------------|
| 😈 **The Devil** | Taunting, aggressive | *"Your soul is mine."* |
| 🤓 **The Nerd** | Statistical, analytical | *"Statistically, I will win 94.7% of the time."* |
| 😴 **Grandma** | Kind, wholesome | *"She's been practicing since 1987."* |

### 🧠 AI Difficulty Levels
| Level | Description |
|-------|-------------|
| **Easy** | 65% random moves, 35% optimal |
| **Medium** | 35% random moves, 65% optimal |
| **Hard** | Unbeatable Minimax AI with alpha-beta pruning and transposition table |

### 💰 Economy System
- **Coins** — Earn 50 coins per win, 20 per draw
- **Betting** — Place bets before games with `/bet <amount>`, winner takes the pot
- **Daily Puzzle** — Solve a "find the winning move" puzzle daily for +30 coins
- **Revenge Mode** — After losing to Hard AI, play a ×2 coins revenge match against The Devil
- Starting balance: 100 coins

### 📊 Stats & Rankings
- **ELO Rating** — Competitive ELO system (K=32, starting at 1500)
- **Win Streaks** — Tracked with milestone celebrations (3, 5, 10, 20 win streaks)
- **Group Milestones** — Announcements at 10, 25, 50, 100 wins in a group
- **Global Leaderboard** — Top 10 players by ELO (`/top`)
- **Group Leaderboard** — Per-group win rankings (`/grouptop`)
- **Head-to-Head** — Records between any two players (`/h2h @user`)
- **Post-Game Analysis** — AI-powered turning point detection after each game

### 🌐 Internationalization
Fully translated into 3 languages:
- 🇬🇧 English
- 🇸🇦 العربية (Arabic)
- 🇮🇳 हिंदी (Hindi)

### 🔧 Admin Tools
- `/broadcast` — Send messages to all users/groups with target selection (groups only, users only, all) and optional pinning
- `/adminstats` — View total users and groups count
- `/st` — Quick bot statistics (owner only)

### ⏰ Scheduled Jobs
- **Daily Stats Broadcast** — Sends global stats + per-group rankings to all groups at 01:30 UTC (7:00 AM IST)
- **Idle Game Reminder** — Hourly check: nudges groups with no games for 4+ hours (IST daytime only, 6 AM–10 PM)

---

## 📋 Bot Commands

### Game Commands
| Command | Description |
|---------|-------------|
| `/xo` | Open lobby — anyone in the group can join |
| `/pvp @user` | Direct PvP challenge to a specific player |
| `/pve` | Play vs AI bot (pick difficulty + character) |
| `/accept` | Accept a pending challenge |
| `/decline` | Decline a pending challenge |
| `/board` | Re-display the current game board |
| `/quit` | Abandon the current game/lobby |

### Tournament
| Command | Description |
|---------|-------------|
| `/tournament` | Start or join a bracket tournament (4 or 8 players) |

### Economy
| Command | Description |
|---------|-------------|
| `/coins` | Check your coin balance |
| `/bet <amount>` | Place a bet before starting a game |
| `/daily` | Daily puzzle challenge for free coins |

### Stats
| Command | Description |
|---------|-------------|
| `/stats` | Your personal stats (wins, losses, ELO, streak, coins) |
| `/top` | Global top 10 ELO leaderboard |
| `/grouptop` | This group's top 10 by wins |
| `/h2h @user` | Head-to-head record against another player |

### Settings & Admin
| Command | Description |
|---------|-------------|
| `/language` | Change language (English, Arabic, Hindi) |
| `/start` | Welcome message + interactive menu |
| `/help` | Full command reference |
| `/broadcast` | Send message to all chats (owner only) |
| `/adminstats` | Bot statistics (owner only) |
| `/st` | Quick stats (owner only) |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.13 |
| **Bot Framework** | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v22.7+ (async, webhooks, job-queue) |
| **Database** | MongoDB Atlas via [Motor](https://motor.readthedocs.io/) (async driver) + PyMongo |
| **Cache / State** | Redis (async via `redis-py`) — all game state, locks, lobbies, bets |
| **AI Engine** | Minimax with alpha-beta pruning + transposition table |
| **Package Manager** | [uv](https://github.com/astral-sh/uv) |
| **Deployment** | Docker / Heroku (webhook mode) |
| **Multi-Dyno Safe** | Redis distributed locks for broadcasts, reminders, and game moves |

---

## 🗄️ Database Schema

### MongoDB Collections

| Collection | Purpose | Key Fields |
|-----------|---------|------------|
| `users` | Per-user profiles & stats | `user_id`, `username`, `full_name`, `wins`, `losses`, `draws`, `elo`, `coins`, `streak`, `max_streak`, `daily_date`, `lang` |
| `groups` | Registered group chats | `chat_id`, `title`, `username` |
| `group_stats` | Per-group per-user stats | `chat_id`, `user_id`, `user_name`, `wins`, `losses`, `draws` |
| `tournaments` | Active bracket tournaments | `chat_id`, `creator_id`, `size`, `status`, `players`, `bracket`, `round` |
| `h2h` | Head-to-head records | `user_a`, `user_b`, `wins_a`, `wins_b`, `total_games`, `biggest_bet` |

### Redis Keys

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `game:{chat_id}` | Active game state | 1h |
| `lobby:{chat_id}` | Open PvP lobby | 10m |
| `pending:{chat_id}` | Pending challenge | 5m |
| `bets:{chat_id}` | Active bets for a chat | 1h |
| `rematch:{chat_id}` | Rematch cooldown timestamp | 30s |
| `tourn:{chat_id}` | Tournament match state | 1h |
| `igame:{iid}` | Inline mode game state | 1h |
| `last_game:{chat_id}` | Last game activity timestamp | 24h |
| `lock:game:{chat_id}` | Distributed game move lock | 10s |
| `lock:igame:{iid}` | Distributed inline game lock | 10s |
| `lock:daily_broadcast` | Single-dyno broadcast lock | 300s |
| `lock:idle_reminder` | Single-dyno reminder lock | 120s |

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `BOT_USERNAME` | ✅ | Bot username without `@` |
| `MONGO_URI` | ✅ | MongoDB Atlas connection string |
| `DB_NAME` | ❌ | Database name (default: `xobot`) |
| `REDIS_URL` | ✅ | Redis connection URL (supports `rediss://` TLS) |
| `OWNER_ID` | ❌ | Your Telegram user ID for admin commands |
| `WEBHOOK_URL` | ❌ | App URL for webhook mode (e.g. `https://myapp.herokuapp.com`). If empty, uses polling mode |
| `WEBHOOK_SECRET` | ❌ | Secret token for webhook verification |
| `PORT` | ❌ | Webhook port (default: `8443`, Heroku sets this automatically) |
| `UPDATE_CHANNEL` | ❌ | Your updates channel with `@` (default: `@YourChannel`) |
| `SUPPORT_USERNAME` | ❌ | Support username without `@` |
| `BOT_THINK_DELAY` | ❌ | Bot "thinking" pause in seconds (default: `0.8`) |

### BotFather Setup (Required for Inline Mode)
1. `/setinline` → select your bot → set a placeholder (e.g. `Play XO`)
2. `/setinlinefeedback` → select your bot → `100%`  
   ⚠️ Without step 2, inline games **will not work** (`inline_message_id` will be `None`)

---

## 📁 Project Structure

```
├── main.py                  # Entry point — webhook/polling, handler registration, scheduled jobs
├── config.py                # Environment variables & constants
├── game.py                  # Core game logic — board, Minimax AI, characters, post-game analysis
├── database.py              # MongoDB operations (Motor async) — users, groups, tournaments, H2H, ELO
├── state.py                 # Redis-backed shared state — games, lobbies, bets, locks
├── i18n.py                  # Internationalization — EN/AR/HI translations
├── keyboards.py             # All InlineKeyboardMarkup builders
├── handlers/
│   ├── game_handler.py      # /xo, /pvp, /pve, /accept, /decline, /quit, /board + all game callbacks
│   ├── user_handler.py      # /start, /help, /stats, /top, /grouptop, /h2h, /language, /st + menu callbacks
│   ├── inline_handler.py    # Inline query, chosen result, inline game callbacks
│   ├── tournament_handler.py# /tournament + bracket management
│   ├── daily_handler.py     # /daily puzzle challenge
│   ├── coins_handler.py     # /coins, /bet + bet resolution
│   └── admin_handler.py     # /broadcast, /adminstats (owner only)
├── pyproject.toml           # Dependencies (uv/pip)
├── Dockerfile               # Docker deployment
├── heroku.yml               # Heroku Docker deployment
├── Procfile                 # Heroku process definition
├── runtime.txt              # Python runtime version
└── app.json                 # Heroku app manifest
```

---

## 🚀 Deployment

### Local Development

```bash
# Clone and enter the project
git clone <your-repo-url>
cd game

# Install uv (if not installed)
pip install uv

# Create venv and install dependencies
uv sync

# Copy and fill environment variables
cp .env.example .env
# Edit .env with your BOT_TOKEN, MONGO_URI, REDIS_URL, etc.

# Run in polling mode (no WEBHOOK_URL needed)
uv run main.py
```

### 🐳 Docker (Heroku)

```bash
# Build and run locally
docker build -t xogame-bot .
docker run --env-file .env xogame-bot

# Deploy to Heroku
heroku create your-app-name
heroku stack:set container -a your-app-name
heroku addons:create heroku-redis:mini -a your-app-name
# Set config vars: BOT_TOKEN, MONGO_URI, WEBHOOK_URL, etc.
git push heroku main
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `python-telegram-bot[webhooks,job-queue]` | Telegram Bot API framework |
| `motor` | Async MongoDB driver |
| `redis` | Shared state for multi-dyno |
| `python-dotenv` | Environment variable loading |
| `APScheduler` | Scheduled jobs (daily broadcast, idle reminders) |

---

## 📄 License

**© 2026 [@sparrow9616](https://github.com/sparrow9616). All rights reserved.**

This project and its source code are the exclusive property of [@sparrow9616](https://github.com/sparrow9616). No part of this codebase may be copied, modified, distributed, or used in any form without prior written permission from the owner.

Unauthorized use, reproduction, or distribution of this software is strictly prohibited.
uv run main.py
```

### Docker

```bash
# Build
docker build -t xo-bot .

# Run
docker run --env-file .env xo-bot
```

### Heroku

1. **Create app and add Redis:**
   ```bash
   heroku create your-app-name
   heroku addons:create heroku-redis:mini
   ```

2. **Set environment variables:**
   ```bash
   heroku config:set BOT_TOKEN="your-token"
   heroku config:set MONGO_URI="mongodb+srv://..."
   heroku config:set BOT_USERNAME="your_bot_username"
   heroku config:set WEBHOOK_URL="https://your-app-name.herokuapp.com"
   heroku config:set OWNER_ID="your-telegram-id"
   ```

3. **Deploy:**
   ```bash
   # Via Docker (uses heroku.yml)
   heroku stack:set container
   git push heroku main

   # Or via buildpack (uses Procfile + runtime.txt)
   git push heroku main
   ```

The bot automatically switches between **webhook mode** (when `WEBHOOK_URL` is set) and **polling mode** (for local development).

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `python-telegram-bot[webhooks,job-queue]` | ≥22.7 | Telegram Bot API framework |
| `motor` | ≥3.7.1 | Async MongoDB driver |
| `pymongo` | ≥4.16.0 | MongoDB operations |
| `redis` | ≥7.4.0 | Async Redis client |
| `python-dotenv` | ≥1.2.2 | Environment variable loading |

---

## 📄 License

This project is open source. Feel free to fork and modify.
