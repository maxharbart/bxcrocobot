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


@app.on_event("startup")
async def startup() -> None:
    load_words()
    logger.info("Word dictionary loaded. Bot ready.")


@app.post("/bitrix/events")
async def bitrix_event(request: Request) -> JSONResponse:
    payload = await request.json()
    event = payload.get("event", "")
    data = payload.get("data", {})
    dispatch(event, data)
    return JSONResponse({"status": "ok"})


@app.post("/bitrix/install")
async def bitrix_install(request: Request) -> JSONResponse:
    payload = await request.json()
    logger.info("Install payload: %s", payload)

    auth = payload.get("auth", {})
    access_token = auth.get("access_token", "")
    domain = auth.get("domain", "")

    if not access_token or not domain:
        logger.error("Missing auth data in install payload")
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
