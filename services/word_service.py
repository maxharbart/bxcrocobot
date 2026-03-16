import random
import re

from config import WORDS_FILE

_words: list[str] = []


def load_words() -> None:
    global _words
    with open(WORDS_FILE, encoding="utf-8") as f:
        content = f.read()

    if WORDS_FILE.endswith(".js"):
        # Parse JS array: extract strings from 'word' entries
        _words = re.findall(r"'([^']+)'", content)
    else:
        _words = [line.strip() for line in content.splitlines() if line.strip()]


def get_random_word() -> str:
    if not _words:
        load_words()
    return random.choice(_words)
