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
    body = await request.body()

    from urllib.parse import parse_qs
    parsed = parse_qs(body.decode("utf-8", errors="replace"))
    flat = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}

    event = flat.get("event", "")
    data = {}
    for key, value in flat.items():
        if key.startswith("data["):
            parts = key.replace("data[", "").rstrip("]").split("][")
            d = data
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            d[parts[-1]] = value

    logger.info("Event: %s", event)
    dispatch(event, data)
    return JSONResponse({"status": "ok"})


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}
