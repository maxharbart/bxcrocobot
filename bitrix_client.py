import logging
import os

import requests

logger = logging.getLogger(__name__)

BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL", "").rstrip("/")

# OAuth token from events (used when registered via app, not webhook)
_auth: dict = {"access_token": "", "domain": ""}

# Bot ID — set from events or config
_bot_id: int = int(os.getenv("BITRIX_BOT_ID", "0"))


def set_auth(access_token: str, domain: str) -> None:
    _auth["access_token"] = access_token
    _auth["domain"] = domain


def set_bot_id(bot_id: int) -> None:
    global _bot_id
    _bot_id = bot_id


def _call(method: str, params: dict | None = None) -> dict:
    if BITRIX_WEBHOOK_URL:
        url = f"{BITRIX_WEBHOOK_URL}/{method}"
        payload = dict(params or {})
    elif _auth["access_token"] and _auth["domain"]:
        url = f"https://{_auth['domain']}/rest/{method}"
        payload = dict(params or {})
        payload["auth"] = _auth["access_token"]
    else:
        logger.error("No auth available for Bitrix API call: %s", method)
        return {}

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
    result = _call("im.notify.personal.add", {
        "USER_ID": user_id,
        "MESSAGE": text,
    })
    if result.get("result"):
        return result
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
