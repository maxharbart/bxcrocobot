import logging

import requests

logger = logging.getLogger(__name__)

# Stored from the most recent event — the bot's OAuth token
_auth: dict = {"access_token": "", "domain": ""}


def set_auth(access_token: str, domain: str) -> None:
    _auth["access_token"] = access_token
    _auth["domain"] = domain


def _call(method: str, params: dict | None = None) -> dict:
    domain = _auth["domain"]
    token = _auth["access_token"]
    if not domain or not token:
        logger.error("No auth token available for Bitrix API call: %s", method)
        return {}

    url = f"https://{domain}/rest/{method}"
    payload = dict(params or {})
    payload["auth"] = token

    try:
        resp = requests.post(url, json=payload, timeout=10)
        logger.info("Bitrix API %s -> %s: %s", method, resp.status_code, resp.text[:500])
        resp.raise_for_status()
        return resp.json()
    except Exception:
        logger.exception("Bitrix API call failed: %s params=%s", method, params)
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
