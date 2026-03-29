"""
words.py — Themed word lists for Word Search.

Each theme has 20–30 words. Games pick 6–10 per round.
Words are uppercase, 3–9 letters (fit in a 10×10 or 12×12 grid).
"""

import random

THEMES: dict[str, list[str]] = {
    "🚀 Space": [
        "STAR", "MOON", "SUN", "MARS", "ORBIT", "COMET",
        "VENUS", "EARTH", "PLUTO", "GALAXY", "ROCKET",
        "NEBULA", "SATURN", "METEOR", "ASTRO", "CRATER",
        "NOVA", "TITAN", "SOLAR", "LUNAR", "COSMOS",
        "QUASAR", "PULSAR", "PLASMA", "PROBE", "ALIEN",
    ],
    "🐾 Animals": [
        "LION", "BEAR", "WOLF", "DEER", "HAWK", "FROG",
        "EAGLE", "SHARK", "WHALE", "TIGER", "SNAKE",
        "ZEBRA", "PANDA", "KOALA", "CAMEL", "BISON",
        "OTTER", "RAVEN", "CRANE", "MOOSE", "HORSE",
        "FALCON", "PARROT", "JAGUAR", "COBRA", "GECKO",
    ],
    "🍕 Food": [
        "RICE", "CAKE", "SOUP", "TACO", "FISH", "CORN",
        "PIZZA", "PASTA", "BREAD", "STEAK", "SALAD",
        "SUSHI", "CANDY", "MANGO", "GRAPE", "PEACH",
        "LEMON", "MELON", "OLIVE", "BACON", "TOAST",
        "CURRY", "DONUT", "CREPE", "BAGEL", "WAFFLE",
    ],
    "🌿 Nature": [
        "TREE", "LAKE", "RAIN", "HILL", "SAND", "CAVE",
        "RIVER", "OCEAN", "STORM", "CLOUD", "CLIFF",
        "STONE", "BROOK", "MARSH", "RIDGE", "GROVE",
        "FIELD", "CREEK", "FROST", "CORAL", "BLOOM",
        "VINE", "FERN", "MOSS", "DELTA", "DUNE",
    ],
    "⚽ Sports": [
        "GOAL", "BALL", "RACE", "SWIM", "SURF", "KICK",
        "RUGBY", "SCORE", "MATCH", "PITCH", "SERVE",
        "TRACK", "ARENA", "COACH", "MEDAL", "RELAY",
        "VAULT", "SPRINT", "TACKLE", "BOXING", "TENNIS",
        "SOCCER", "HOCKEY", "SQUASH", "CATCH", "THROW",
    ],
    "💻 Tech": [
        "CODE", "DATA", "CHIP", "BYTE", "WIFI", "LINK",
        "PIXEL", "CLOUD", "ROBOT", "MOUSE", "LINUX",
        "VIRUS", "CYBER", "DEBUG", "CACHE", "TOKEN",
        "STACK", "ARRAY", "QUERY", "PATCH", "DRONE",
        "CODEC", "FIBER", "FLASH", "PROXY", "RADAR",
    ],
    "🎵 Music": [
        "BEAT", "DRUM", "BASS", "NOTE", "SONG", "JAZZ",
        "PIANO", "FLUTE", "VIOLA", "TEMPO", "CHORD",
        "LYRIC", "VOCAL", "GENRE", "ALBUM", "TRACK",
        "SYNTH", "METAL", "OPERA", "BLUES", "REMIX",
        "RIFF", "TUNE", "HARP", "BANJO", "CELLO",
    ],
    "🏰 History": [
        "KING", "FORT", "DUKE", "LORD", "ARMY", "SWORD",
        "CROWN", "QUEEN", "THRONE", "CASTLE", "KNIGHT",
        "EMPIRE", "LEGION", "SHIELD", "ARROW", "LANCE",
        "SIEGE", "TREATY", "COLONY", "BRONZE", "ROMAN",
        "VIKING", "SULTAN", "NOBLE", "REIGN", "TRIBE",
    ],
}

THEME_NAMES = list(THEMES.keys())


def pick_theme() -> str:
    return random.choice(THEME_NAMES)


def pick_words(theme: str, count: int = 8) -> list[str]:
    """Pick `count` words from theme, mix of lengths for varied difficulty."""
    pool = THEMES[theme]
    # Ensure a mix: some short (3-4), some medium (5), some long (6+)
    short  = [w for w in pool if len(w) <= 4]
    medium = [w for w in pool if len(w) == 5]
    long_  = [w for w in pool if len(w) >= 6]

    picked = []
    # Pick at least 2 short, 3 medium, 2 long (if possible)
    random.shuffle(short)
    random.shuffle(medium)
    random.shuffle(long_)

    picked.extend(short[:2])
    picked.extend(medium[:3])
    picked.extend(long_[:3])

    # If we don't have enough, fill from remaining
    remaining = [w for w in pool if w not in picked]
    random.shuffle(remaining)

    while len(picked) < count and remaining:
        picked.append(remaining.pop())

    return picked[:count]


def word_score(word: str) -> int:
    """Points based on word length."""
    n = len(word)
    if n <= 3:
        return 1
    elif n == 4:
        return 2
    elif n == 5:
        return 3
    elif n == 6:
        return 5
    else:
        return 8
