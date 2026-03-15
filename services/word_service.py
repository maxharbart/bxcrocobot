import random

from config import WORDS_FILE

_words: list[str] = []


def load_words() -> None:
    global _words
    with open(WORDS_FILE, encoding="utf-8") as f:
        _words = [line.strip() for line in f if line.strip()]


def get_random_word() -> str:
    if not _words:
        load_words()
    return random.choice(_words)
