import logging

import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from bitrix_client import set_auth, set_bot_id
from config import BOT_PUBLIC_URL
from handlers.dispatcher import dispatch
from services.word_service import load_words

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bitrix24 Crocodile Bot")


def _parse_form_nested(form: dict) -> tuple[str, dict, dict]:
    """Parse Bitrix form-encoded payload with nested keys like data[PARAMS][MESSAGE]."""
    event = form.get("event", "")
    data = {}
    auth = {}
    for key, value in form.items():
        if key.startswith("data["):
            parts = key.replace("data[", "").rstrip("]").split("][")
            d = data
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            d[parts[-1]] = value
        elif key.startswith("auth["):
            auth_key = key.replace("auth[", "").rstrip("]")
            auth[auth_key] = value
    return event, data, auth


@app.on_event("startup")
async def startup() -> None:
    load_words()
    logger.info("Word dictionary loaded. Bot ready.")


@app.post("/bitrix/events")
async def bitrix_event(request: Request) -> JSONResponse:
    # Log raw body for debugging
    body = await request.body()
    logger.info("RAW EVENT BODY: %s", body[:2000])

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        import json
        payload = json.loads(body)
        event = payload.get("event", "")
        data = payload.get("data", {})
        auth = payload.get("auth", {})
    else:
        from urllib.parse import parse_qs
        parsed = parse_qs(body.decode("utf-8", errors="replace"))
        # parse_qs returns lists, flatten to single values
        flat = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        logger.info("PARSED FORM FIELDS: %s", flat)
        event = flat.get("event", "")
        data = {}
        auth = {}
        for key, value in flat.items():
            if key.startswith("data["):
                parts = key.replace("data[", "").rstrip("]").split("][")
                d = data
                for p in parts[:-1]:
                    d = d.setdefault(p, {})
                d[parts[-1]] = value
            elif key.startswith("auth["):
                auth_key = key.replace("auth[", "").rstrip("]")
                auth[auth_key] = value

    logger.info("Event: %s, data: %s, auth: %s", event, data, {k: v[:8] + "..." if k == "access_token" else v for k, v in auth.items()})

    # Update bot auth token from event
    if auth.get("access_token") and auth.get("domain"):
        set_auth(auth["access_token"], auth["domain"])

    # Extract bot ID from event data
    bot_data = data.get("BOT", {})
    if isinstance(bot_data, dict) and bot_data.get("BOT_ID"):
        set_bot_id(int(bot_data["BOT_ID"]))

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
        access_token = payload.get("AUTH_ID", "") or payload.get("auth[access_token]", "")
        domain = payload.get("DOMAIN", "") or payload.get("auth[domain]", "")

    logger.info("Install form payload: %s", payload)
    logger.info("Install query params: %s", dict(request.query_params))

    # DOMAIN usually comes in query params
    if not domain:
        domain = request.query_params.get("DOMAIN", "")

    # Fallback to SERVER_ENDPOINT from form body
    if not domain:
        server_endpoint = payload.get("SERVER_ENDPOINT", "") if isinstance(payload, dict) else ""
        if server_endpoint:
            domain = server_endpoint.replace("https://", "").replace("http://", "").rstrip("/")

    logger.info("Resolved auth: access_token=%s, domain=%s", access_token[:8] + "..." if access_token else "NONE", domain)

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
        "EVENT_WELCOME_MESSAGE": event_url,
        "EVENT_BOT_DELETE": event_url,
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

    if bot_id:
        return HTMLResponse("<html><body><h3>Crocodile Bot installed successfully!</h3><p>Add the bot to a group chat to start playing.</p></body></html>")
    else:
        error_msg = result.get("error_description", result.get("error", "Unknown error"))
        return HTMLResponse(f"<html><body><h3>Installation failed</h3><p>{error_msg}</p></body></html>", status_code=500)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}
