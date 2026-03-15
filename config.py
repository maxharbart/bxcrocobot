import os


BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL", "")
BITRIX_BOT_ID = os.getenv("BITRIX_BOT_ID", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ROUND_DURATION = int(os.getenv("ROUND_DURATION", "90"))
WORDS_FILE = os.getenv("WORDS_FILE", "words.txt")
BOT_PUBLIC_URL = os.getenv("BOT_PUBLIC_URL", "")  # e.g. https://myserver.com:8000
