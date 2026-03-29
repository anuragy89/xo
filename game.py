"""
game.py – Core XO logic, Minimax AI, bot characters, move analysis.
"""

import random

from emojis import em, get_cell_emoji

EMPTY = 0
X     = 1    # human  → ❌
O     = -1   # bot    → ⭕

WIN_COMBOS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]

CELL_EMOJI = get_cell_emoji()


# ─────────────────────────────────────────────────────────
#  BOT CHARACTERS
# ─────────────────────────────────────────────────────────

CHARACTERS = {
    "devil": {
        "name":  f"{em('devil')} The Devil",
        "intro": f"{em('devil')} <b>The Devil</b> has entered the game.\n<i>\"Your soul is mine.\"</i>",
        "win":   [
            f"{em('devil')} Did you really think you could beat ME?",
            f"{em('fire')} Burned. Absolutely burned.",
            f"{em('skull')} Error 666: Your win not found.",
            f"{em('devil')} I've seen better plays from a toddler.",
            f"{em('fire')} Your suffering brings me joy.",
        ],
        "lose":  [
            "😤 A fluke. JUST a fluke.",
            "😡 This isn't over. I WILL have my revenge.",
            f"{em('fire')} I let you win. Obviously.",
        ],
        "draw":  [
            f"{em('devil')} I was going easy on you.",
            f"{em('fire')} A temporary mercy. Next time — no.",
        ],
        "think": [
            f"{em('devil')} <b>Consulting the dark arts...</b>",
            f"{em('fire')} <b>Summoning forbidden strategies...</b>",
            f"{em('skull')} <b>Calculating your demise...</b>",
        ],
    },
    "nerd": {
        "name":  f"{em('nerd')} The Nerd",
        "intro": f"{em('nerd')} <b>The Nerd</b> is ready.\n<i>\"Statistically, I will win 94.7% of the time.\"</i>",
        "win":   [
            f"{em('nerd')} Precisely as calculated. My model was 97.2% confident.",
            f"{em('chart_bar')} Center + corner opening: 68% win rate. Proven.",
            f"{em('nerd')} Your move sequence is a known losing pattern. See: Berlekamp 1991.",
            f"{em('laptop')} Algorithm executed flawlessly. Result: expected.",
        ],
        "lose":  [
            f"{em('nerd')} Fascinating. I must recalibrate my decision tree.",
            f"{em('chart_bar')} My model assigned 2.3% probability to this. Noted.",
            f"{em('laptop')} Logging anomaly. Initiating post-game analysis...",
        ],
        "draw":  [
            f"{em('nerd')} A draw. Both players played optimally from move 3.",
            f"{em('chart_bar')} Expected outcome when both parties use minimax correctly.",
        ],
        "think": [
            f"{em('nerd')} <b>Cross-referencing 47,293 game databases...</b>",
            f"{em('chart_bar')} <b>Running alpha-beta pruning depth 9...</b>",
            f"{em('laptop')} <b>Evaluating 8 candidate moves...</b>",
        ],
    },
    "grandma": {
        "name":  f"{em('grandma')} Grandma",
        "intro": f"{em('grandma')} <b>Grandma</b> wants to play!\n<i>\"She's been practicing since 1987.\"</i>",
        "win":   [
            f"{em('grandma')} Oh my, I won! Would you like some cookies, dear?",
            f"{em('cookie')} Grandma got you! Don't feel bad, sweetie.",
            f"{em('smile')} Oh goodness! I haven't won since bingo night!",
            f"{em('flower')} That was so fun! You almost had me on move 4, dear.",
        ],
        "lose":  [
            f"{em('grandma')} Oh well, you're so clever! Just like your grandfather.",
            f"{em('cookie')} You won! Here, have a virtual cookie {em('cookie')}",
            f"{em('smile')} Oh you're too good for old Grandma!",
        ],
        "draw":  [
            f"{em('grandma')} A tie! How nice, nobody had to lose.",
            f"{em('flower')} We're perfectly matched, dear.",
        ],
        "think": [
            f"{em('grandma')} <b>Hmm... let me think, dear...</b>",
            f"{em('flower')} <b>One moment, adjusting my glasses...</b>",
            f"{em('grandma')} <b>Now where did I put my strategy...</b>",
            f"{em('cookie')} <b>Thinking while the cookies bake...</b>",
        ],
    },
}

DEFAULT_CHARACTER = "nerd"


def char_thinking(character: str) -> str:
    c = CHARACTERS.get(character, CHARACTERS[DEFAULT_CHARACTER])
    return random.choice(c["think"])


def char_result_msg(character: str, result: str) -> str:
    """result: 'win' (bot won) | 'lose' (bot lost) | 'draw'"""
    c = CHARACTERS.get(character, CHARACTERS[DEFAULT_CHARACTER])
    msgs = c.get(result, c["win"])
    return "\n\n<i>" + random.choice(msgs) + "</i>"


# ─────────────────────────────────────────────────────────
#  BOARD LOGIC
# ─────────────────────────────────────────────────────────

def make_board() -> list:
    return [EMPTY] * 9


def check_winner(board: list):
    for a, b, c in WIN_COMBOS:
        if board[a] == board[b] == board[c] != EMPTY:
            return board[a]
    return None


def is_draw(board: list) -> bool:
    return EMPTY not in board and check_winner(board) is None


def available_moves(board: list) -> list:
    return [i for i, v in enumerate(board) if v == EMPTY]


def board_to_emoji(board: list) -> str:
    return "\n".join(
        "".join(CELL_EMOJI[board[r * 3 + c]] for c in range(3))
        for r in range(3)
    )


# ─────────────────────────────────────────────────────────
#  MINIMAX
# ─────────────────────────────────────────────────────────

_TRANSPOSITION: dict = {}   # board-tuple → score cache (persists across games)

def _minimax(board, depth, is_max, alpha, beta) -> int:
    w = check_winner(board)
    if w == O:         return 10 - depth
    if w == X:         return depth - 10
    if is_draw(board): return 0

    key = (tuple(board), is_max)
    cached = _TRANSPOSITION.get(key)
    if cached is not None:
        return cached

    if is_max:
        best = -100
        for i in available_moves(board):
            board[i] = O
            best  = max(best, _minimax(board, depth + 1, False, alpha, beta))
            board[i] = EMPTY
            alpha = max(alpha, best)
            if beta <= alpha:
                break
    else:
        best = 100
        for i in available_moves(board):
            board[i] = X
            best  = min(best, _minimax(board, depth + 1, True, alpha, beta))
            board[i] = EMPTY
            beta  = min(beta, best)
            if beta <= alpha:
                break

    _TRANSPOSITION[key] = best
    return best


def minimax_score(board: list) -> int:
    return _minimax(board[:], 0, True, -100, 100)


def bot_move(board: list, difficulty: str = "hard") -> int:
    moves = available_moves(board)
    if not moves:
        return -1
    if difficulty == "easy" and random.random() < 0.65:
        return random.choice(moves)
    if difficulty == "medium" and random.random() < 0.35:
        return random.choice(moves)

    # Prefer center on first bot move (known optimal)
    if board.count(EMPTY) >= 8 and board[4] == EMPTY:
        return 4

    best_score, best_move = -100, moves[0]
    for i in moves:
        board[i] = O
        score    = _minimax(board, 0, False, -100, 100)
        board[i] = EMPTY
        if score > best_score:
            best_score, best_move = score, i
    return best_move


# ─────────────────────────────────────────────────────────
#  POST-GAME ANALYSIS
# ─────────────────────────────────────────────────────────

def analyse_game(move_history: list) -> str:
    """
    move_history: list of (board_snapshot, player_mark, cell_idx)
    Returns a concise analysis string, or "" if too short.
    """
    if len(move_history) < 3:
        return ""

    prev_score     = 0
    turning_move   = None
    turning_idx    = -1

    for move_num, (board_snap, player_mark, cell_idx) in enumerate(move_history):
        score = minimax_score(board_snap)
        # Detect when the position swings from balanced to decisive
        if abs(prev_score) < 3 and abs(score) >= 5:
            turning_move = (move_num, player_mark, cell_idx, score)
            break
        prev_score = score

    if not turning_move:
        return ""  # evenly played — no clear turning point

    move_num, player_mark, cell_idx, score = turning_move
    row = cell_idx // 3 + 1
    col = cell_idx % 3  + 1
    pos = f"row {row}, col {col}"

    if player_mark == X:
        if score < 0:
            return f"{em('magnify')} <b>Analysis:</b> Move {move_num + 1} ({pos}) was a mistake by {em('x_mark')} — it gave the opponent the advantage."
        else:
            return f"{em('magnify')} <b>Analysis:</b> Move {move_num + 1} ({pos}) was the winning play by {em('x_mark')} — the game was decided there."
    else:
        if score > 0:
            return f"{em('magnify')} <b>Analysis:</b> Move {move_num + 1} ({pos}) sealed {em('o_mark')}'s advantage — the board was lost for {em('x_mark')} from that point."
        else:
            return f"{em('magnify')} <b>Analysis:</b> Move {move_num + 1} ({pos}) was a mistake by {em('o_mark')} — {em('x_mark')} took control after that."


# ─────────────────────────────────────────────────────────
#  GAME-STATE FACTORIES
# ─────────────────────────────────────────────────────────

def new_pvp_game(p1_id, p2_id, p1_name, p2_name) -> dict:
    return {
        "mode": "pvp", "status": "playing",
        "board": make_board(),
        "players": {p1_id: X, p2_id: O},
        "names":   {p1_id: p1_name, p2_id: p2_name},
        "turn": p1_id, "x_player": p1_id, "o_player": p2_id,
        "tournament": False, "blitz": False,
        "move_history": [], "msg_id": None,
    }


def new_pve_game(player_id, player_name,
                 difficulty="hard", character=DEFAULT_CHARACTER,
                 revenge=False) -> dict:
    char_name = CHARACTERS.get(character, CHARACTERS[DEFAULT_CHARACTER])["name"]
    return {
        "mode": "pve", "status": "playing",
        "board": make_board(),
        "players": {player_id: X},
        "names":   {player_id: player_name, "bot": char_name},
        "turn": player_id, "x_player": player_id, "o_player": "bot",
        "difficulty": difficulty, "character": character,
        "tournament": False, "revenge": revenge,
        "move_history": [], "msg_id": None,
    }
