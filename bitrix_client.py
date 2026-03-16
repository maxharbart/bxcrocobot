import logging
import os

import requests

logger = logging.getLogger(__name__)

BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL", "").rstrip("/")


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
        logger.exception("Bitrix API call failed: %s", method)
        return {}


def send_chat_message(chat_id: int, text: str) -> dict:
    return _call("im.message.add", {
        "DIALOG_ID": f"chat{chat_id}",
        "MESSAGE": text,
    })


def send_private_message(user_id: int, text: str) -> dict:
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


def get_chat_users(chat_id: int) -> list[int]:
    result = _call("im.chat.user.list", {"CHAT_ID": chat_id})
    users = result.get("result", [])
    return [int(uid) for uid in users if uid]
