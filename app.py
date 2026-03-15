import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
    logger.info("Bot installed: %s", payload)
    return JSONResponse({"status": "installed"})


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}
