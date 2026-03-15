import asyncio
import logging

from config import ROUND_DURATION
from storage.redis_storage import timer_active, set_timer

logger = logging.getLogger(__name__)

_tasks: dict[int, asyncio.Task] = {}


async def _round_timeout(chat_id: int) -> None:
    await asyncio.sleep(ROUND_DURATION)
    if timer_active(chat_id):
        from game.manager import end_round
        end_round(chat_id, timed_out=True)


def start_timer(chat_id: int) -> None:
    cancel_timer(chat_id)
    set_timer(chat_id, ROUND_DURATION)
    loop = asyncio.get_event_loop()
    _tasks[chat_id] = loop.create_task(_round_timeout(chat_id))


def cancel_timer(chat_id: int) -> None:
    task = _tasks.pop(chat_id, None)
    if task and not task.done():
        task.cancel()
