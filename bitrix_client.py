import logging
import os

import requests

logger = logging.getLogger(__name__)

BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL", "").rstrip("/")
BITRIX_CLIENT_ID = os.getenv("BITRIX_CLIENT_ID", "")

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
    if BITRIX_CLIENT_ID:
        payload["CLIENT_ID"] = BITRIX_CLIENT_ID

    try:
        resp = requests.post(url, json=payload, timeout=10)
        logger.info("Bitrix API %s -> %s: %s", method, resp.status_code, resp.text[:500])
        resp.raise_for_status()
        return resp.json()
    except Exception:
        logger.exception("Bitrix API call failed: %s", method)
        return {}


def send_chat_message(chat_id: int, text: str, keyboard: list | None = None) -> dict:
    params = {
        "DIALOG_ID": f"chat{chat_id}",
        "MESSAGE": text,
    }
    if keyboard:
        params["KEYBOARD"] = keyboard

    # Try imbot.message.add first (sends as bot, supports keyboard)
    if _bot_id:
        params["BOT_ID"] = _bot_id
        result = _call("imbot.message.add", params)
        if result.get("result"):
            return result
        logger.warning("imbot.message.add failed, falling back to im.message.add")
        params.pop("BOT_ID", None)
        params.pop("KEYBOARD", None)  # im.message.add doesn't support keyboards

    # Fallback to im.message.add (sends as webhook user, no keyboard)
    return _call("im.message.add", params)


def send_private_message(user_id: int, text: str, keyboard: list | None = None) -> dict:
    if _bot_id:
        params = {
            "BOT_ID": _bot_id,
            "DIALOG_ID": str(user_id),
            "MESSAGE": text,
        }
        if keyboard:
            params["KEYBOARD"] = keyboard
        result = _call("imbot.message.add", params)
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
