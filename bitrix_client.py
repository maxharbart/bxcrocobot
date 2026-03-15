import logging

import requests

from config import BITRIX_WEBHOOK_URL

logger = logging.getLogger(__name__)


def _call(method: str, params: dict | None = None) -> dict:
    url = f"{BITRIX_WEBHOOK_URL}/{method}"
    try:
        resp = requests.post(url, json=params or {}, timeout=10)
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
    return _call("im.message.add", {
        "DIALOG_ID": str(user_id),
        "MESSAGE": text,
    })


def get_user_info(user_id: int) -> dict:
    result = _call("user.get", {"ID": user_id})
    users = result.get("result", [])
    if users:
        return users[0]
    return {}
