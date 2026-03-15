import logging

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config import BOT_PUBLIC_URL
from handlers.dispatcher import dispatch
from services.word_service import load_words

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bitrix24 Crocodile Bot")


def _parse_form_nested(form: dict) -> tuple[str, dict]:
    """Parse Bitrix form-encoded payload with nested keys like data[PARAMS][MESSAGE]."""
    event = form.get("event", "")
    data = {}
    for key, value in form.items():
        if key.startswith("data["):
            parts = key.replace("data[", "").rstrip("]").split("][")
            d = data
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            d[parts[-1]] = value
    return event, data


@app.on_event("startup")
async def startup() -> None:
    load_words()
    logger.info("Word dictionary loaded. Bot ready.")


@app.post("/bitrix/events")
async def bitrix_event(request: Request) -> JSONResponse:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        event = payload.get("event", "")
        data = payload.get("data", {})
    else:
        form = await request.form()
        event, data = _parse_form_nested(dict(form))

    logger.info("Event: %s, data keys: %s", event, list(data.keys()))
    dispatch(event, data)
    return JSONResponse({"status": "ok"})


@app.post("/bitrix/install")
async def bitrix_install(request: Request) -> JSONResponse:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        access_token = payload.get("auth", {}).get("access_token", "")
        domain = payload.get("auth", {}).get("domain", "")
    else:
        form = await request.form()
        payload = dict(form)
        access_token = payload.get("auth[access_token]", "") or payload.get("AUTH_ID", "")
        domain = payload.get("auth[domain]", "") or payload.get("DOMAIN", "")

    logger.info("Install payload keys: %s", list(payload.keys()) if isinstance(payload, dict) else payload)

    if not domain:
        domain = request.query_params.get("DOMAIN", "")

    if not access_token or not domain:
        logger.error("Missing auth data. access_token=%s, domain=%s", bool(access_token), domain)
        return JSONResponse({"error": "missing auth"}, status_code=400)

    # Register the bot via imbot.register
    event_url = f"{BOT_PUBLIC_URL}/bitrix/events"
    register_url = f"https://{domain}/rest/imbot.register"

    resp = requests.post(register_url, json={
        "auth": access_token,
        "CODE": "crocodile_bot",
        "TYPE": "B",
        "EVENT_MESSAGE_ADD": event_url,
        "PROPERTIES": {
            "NAME": "Crocodile",
            "LAST_NAME": "Bot",
            "COLOR": "GREEN",
            "DESCRIPTION": "Crocodile (Pictionary) game bot. Use /crocodile to start!",
        },
    }, timeout=10)

    result = resp.json()
    logger.info("imbot.register result: %s", result)

    bot_id = result.get("result")
    if bot_id:
        logger.info("Bot registered with ID: %s", bot_id)
    else:
        logger.error("Bot registration failed: %s", result)

    return JSONResponse({"status": "installed", "bot_id": bot_id})


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}
