import logging
import os

import requests

logger = logging.getLogger(__name__)

BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL", "").rstrip("/")

_bot_id: int = int(os.getenv("BITRIX_BOT_ID", "0"))


def set_bot_id(bot_id: int) -> None:
    global _bot_id
    _bot_id = bot_id


def _call(method: str, params: dict | None = None) -> dict:
    if not BITRIX_WEBHOOK_URL:
        logger.error("BITRIX_WEBHOOK_URL not set")
        return {}

    url = f"{BITRIX_WEBHOOK_URL}/{method}"
    payload = dict(params or {})

    try:
        resp = requests.post(url, json=payload, timeout=10)
        logger.info("Bitrix API %s -> %s: %s", method, resp.status_code, resp.text[:500])
        resp.raise_for_status()
        return resp.json()
    except Exception:
        logger.exception("Bitrix API call failed: %s params=%s", method, params)
        return {}


def send_chat_message(chat_id: int, text: str) -> dict:
    if _bot_id:
        return _call("imbot.message.add", {
            "BOT_ID": _bot_id,
            "DIALOG_ID": f"chat{chat_id}",
            "MESSAGE": text,
        })
    return _call("im.message.add", {
        "DIALOG_ID": f"chat{chat_id}",
        "MESSAGE": text,
    })


def send_private_message(user_id: int, text: str) -> dict:
    if _bot_id:
        result = _call("imbot.message.add", {
            "BOT_ID": _bot_id,
            "DIALOG_ID": str(user_id),
            "MESSAGE": text,
        })
        if result.get("result"):
            return result
    # Fallback to notification
    return _call("im.notify.personal.add", {
        "USER_ID": user_id,
        "MESSAGE": text,
    })


def get_user_info(user_id: int) -> dict:
    result = _call("user.get", {"ID": user_id})
    users = result.get("result", [])
    if users:
        return users[0]
    return {}
