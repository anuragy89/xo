"""
state.py — Redis-backed shared state for multi-dyno deployment.

Replaces all in-memory dicts (games, lobbies, pending, bets, etc.)
with Redis keys so state is shared across Heroku dynos.
"""

import json
import logging

import redis.asyncio as aioredis

from config import REDIS_URL

logger = logging.getLogger(__name__)

_pool: aioredis.ConnectionPool | None = None


def r():
    """Return a Redis client using the shared pool."""
    global _pool
    if _pool is None:
        kw = {"decode_responses": True, "max_connections": 20}
        # Heroku Redis uses rediss:// (TLS) with self-signed certs
        if REDIS_URL.startswith("rediss://"):
            kw["ssl_cert_reqs"] = "none"
        _pool = aioredis.ConnectionPool.from_url(REDIS_URL, **kw)
    return aioredis.Redis(connection_pool=_pool)


# ─────────────────────────────────────────────────────────
#  SERIALIZATION HELPERS
#  Game dicts use int keys (user IDs) and "bot" string.
#  JSON only supports string keys, so we convert back & forth.
# ─────────────────────────────────────────────────────────

def _to_str(v):
    return str(v)


def _to_int_or_str(v):
    """'bot' stays 'bot', everything else → int."""
    if v == "bot" or v == "None" or v is None:
        return v if v != "None" else None
    try:
        return int(v)
    except (ValueError, TypeError):
        return v


def _serialize_game(game: dict) -> str:
    g = {}
    for k, v in game.items():
        if k in ("players", "names"):
            g[k] = {_to_str(pk): pv for pk, pv in v.items()}
        elif k == "move_history":
            g[k] = [[list(snap), mark, idx] for snap, mark, idx in v]
        elif k in ("turn", "x_player", "o_player"):
            g[k] = _to_str(v)
        else:
            g[k] = v
    return json.dumps(g)


def _deserialize_game(raw: str | None) -> dict | None:
    if not raw:
        return None
    g = json.loads(raw)
    g["players"] = {_to_int_or_str(k): v for k, v in g["players"].items()}
    g["names"] = {_to_int_or_str(k): v for k, v in g["names"].items()}
    g["turn"] = _to_int_or_str(g["turn"])
    g["x_player"] = _to_int_or_str(g["x_player"])
    g["o_player"] = _to_int_or_str(g["o_player"])
    g["move_history"] = [(snap, mark, idx) for snap, mark, idx in g["move_history"]]
    return g


def _serialize_lobby(lobby: dict) -> str:
    """Lobby stores a creator User object — extract needed fields."""
    creator = lobby["creator"]
    return json.dumps({
        "creator_id": creator.id if hasattr(creator, "id") else creator["id"],
        "creator_name": (
            creator.full_name if hasattr(creator, "full_name")
            else creator["full_name"]
        ),
        "creator_username": (
            getattr(creator, "username", None) if hasattr(creator, "id")
            else creator.get("username")
        ),
        "msg_id": lobby.get("msg_id"),
        "status": lobby.get("status", "waiting"),
        "mode": lobby.get("mode", "pvp_lobby"),
    })


class _FakeUser:
    """Minimal stand-in for telegram.User, sufficient for game creation."""
    def __init__(self, uid, full_name, username=None):
        self.id = uid
        self.full_name = full_name
        self.first_name = full_name.split()[0] if full_name else ""
        self.username = username


def _deserialize_lobby(raw: str | None) -> dict | None:
    if not raw:
        return None
    d = json.loads(raw)
    d["creator"] = _FakeUser(d["creator_id"], d["creator_name"], d.get("creator_username"))
    return d


def _serialize_pending(pending: dict) -> str:
    challenger = pending["challenger"]
    return json.dumps({
        "challenger_id": challenger.id if hasattr(challenger, "id") else challenger["id"],
        "challenger_name": (
            challenger.full_name if hasattr(challenger, "full_name")
            else challenger["full_name"]
        ),
        "target_username": pending.get("target_username", ""),
    })


def _deserialize_pending(raw: str | None) -> dict | None:
    if not raw:
        return None
    d = json.loads(raw)
    d["challenger"] = _FakeUser(d["challenger_id"], d["challenger_name"])
    return d


# ─────────────────────────────────────────────────────────
#  GAMES
# ─────────────────────────────────────────────────────────

async def get_game(chat_id) -> dict | None:
    raw = await r().get(f"game:{chat_id}")
    return _deserialize_game(raw)


async def set_game(chat_id, game: dict, ttl: int = 3600) -> None:
    await r().set(f"game:{chat_id}", _serialize_game(game), ex=ttl)


async def delete_game(chat_id) -> None:
    await r().delete(f"game:{chat_id}")


async def game_exists(chat_id) -> bool:
    return bool(await r().exists(f"game:{chat_id}"))


# ─────────────────────────────────────────────────────────
#  LOBBIES (xo_lobbies)
# ─────────────────────────────────────────────────────────

async def get_lobby(chat_id) -> dict | None:
    raw = await r().get(f"lobby:{chat_id}")
    return _deserialize_lobby(raw)


async def set_lobby(chat_id, lobby: dict, ttl: int = 600) -> None:
    await r().set(f"lobby:{chat_id}", _serialize_lobby(lobby), ex=ttl)


async def delete_lobby(chat_id) -> None:
    await r().delete(f"lobby:{chat_id}")


async def lobby_exists(chat_id) -> bool:
    return bool(await r().exists(f"lobby:{chat_id}"))


# ─────────────────────────────────────────────────────────
#  PENDING CHALLENGES
# ─────────────────────────────────────────────────────────

async def get_pending(chat_id) -> dict | None:
    raw = await r().get(f"pending:{chat_id}")
    return _deserialize_pending(raw)


async def set_pending(chat_id, pending: dict, ttl: int = 300) -> None:
    await r().set(f"pending:{chat_id}", _serialize_pending(pending), ex=ttl)


async def delete_pending(chat_id) -> None:
    await r().delete(f"pending:{chat_id}")


async def pending_exists(chat_id) -> bool:
    return bool(await r().exists(f"pending:{chat_id}"))


# ─────────────────────────────────────────────────────────
#  REMATCH COOLDOWN
# ─────────────────────────────────────────────────────────

async def get_rematch_ts(chat_id) -> float:
    raw = await r().get(f"rematch:{chat_id}")
    return float(raw) if raw else 0.0


async def set_rematch_ts(chat_id, ts: float) -> None:
    await r().set(f"rematch:{chat_id}", str(ts), ex=30)


# ─────────────────────────────────────────────────────────
#  BETS
# ─────────────────────────────────────────────────────────

async def get_bets(chat_id) -> dict:
    raw = await r().get(f"bets:{chat_id}")
    if not raw:
        return {}
    return {int(k): v for k, v in json.loads(raw).items()}


async def set_bet(chat_id, user_id: int, amount: int) -> None:
    bets = await get_bets(chat_id)
    bets[user_id] = amount
    await r().set(f"bets:{chat_id}", json.dumps({str(k): v for k, v in bets.items()}), ex=3600)


async def pop_bets(chat_id) -> dict:
    bets = await get_bets(chat_id)
    await r().delete(f"bets:{chat_id}")
    return bets


async def clear_bets(chat_id) -> None:
    await r().delete(f"bets:{chat_id}")


# ─────────────────────────────────────────────────────────
#  TOURNAMENT GAMES (in-match state)
# ─────────────────────────────────────────────────────────

async def get_tourn_game(chat_id) -> dict | None:
    raw = await r().get(f"tourn:{chat_id}")
    if not raw:
        return None
    data = json.loads(raw)
    data["game"] = _deserialize_game(json.dumps(data["game"])) if data.get("game") else None
    return data


async def set_tourn_game(chat_id, entry: dict, ttl: int = 3600) -> None:
    data = {
        "game": json.loads(_serialize_game(entry["game"])) if entry.get("game") else None,
        "match": entry["match"],
    }
    await r().set(f"tourn:{chat_id}", json.dumps(data), ex=ttl)


async def delete_tourn_game(chat_id) -> None:
    await r().delete(f"tourn:{chat_id}")


# ─────────────────────────────────────────────────────────
#  INLINE GAMES
# ─────────────────────────────────────────────────────────

async def get_inline_game(iid: str) -> dict | None:
    raw = await r().get(f"igame:{iid}")
    if not raw:
        return None
    data = json.loads(raw)
    # Lobby entries don't have "players" key
    if data.get("mode") == "pvp_lobby":
        data["creator"] = _FakeUser(
            data["creator_id"], data["creator_name"], data.get("creator_username"),
        )
        return data
    return _deserialize_game(raw)


async def set_inline_game(iid: str, game: dict, ttl: int = 3600) -> None:
    if game.get("mode") == "pvp_lobby":
        creator = game["creator"]
        data = {
            "mode": "pvp_lobby",
            "status": game.get("status", "waiting"),
            "creator_id": creator.id if hasattr(creator, "id") else creator["id"],
            "creator_name": (
                creator.full_name if hasattr(creator, "full_name")
                else creator["full_name"]
            ),
            "creator_username": (
                getattr(creator, "username", None) if hasattr(creator, "id")
                else creator.get("username")
            ),
        }
        await r().set(f"igame:{iid}", json.dumps(data), ex=ttl)
    else:
        await r().set(f"igame:{iid}", _serialize_game(game), ex=ttl)


async def delete_inline_game(iid: str) -> None:
    await r().delete(f"igame:{iid}")


# ─────────────────────────────────────────────────────────
#  DISTRIBUTED LOCKS  (replaces asyncio.Lock per game)
# ─────────────────────────────────────────────────────────

def game_lock(chat_id, timeout: int = 10):
    """Returns an async Redis lock for a game."""
    return r().lock(f"lock:game:{chat_id}", timeout=timeout, blocking_timeout=5)


def inline_lock(iid: str, timeout: int = 10):
    """Returns an async Redis lock for an inline game."""
    return r().lock(f"lock:igame:{iid}", timeout=timeout, blocking_timeout=5)
