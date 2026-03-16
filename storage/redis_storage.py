import redis

from config import REDIS_URL
from game.models import ChatStats, GameState


_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)


def _conn() -> redis.Redis:
    return redis.Redis(connection_pool=_pool)


def get_game(chat_id: int) -> GameState | None:
    data = _conn().get(f"game:{chat_id}")
    if data is None:
        return None
    return GameState.model_validate_json(data)


def save_game(chat_id: int, state: GameState) -> None:
    _conn().set(f"game:{chat_id}", state.model_dump_json())


def delete_game(chat_id: int) -> None:
    r = _conn()
    r.delete(f"game:{chat_id}")
    r.delete(f"timer:{chat_id}")


def set_timer(chat_id: int, ttl: int) -> None:
    _conn().setex(f"timer:{chat_id}", ttl, "1")


def timer_active(chat_id: int) -> bool:
    return _conn().exists(f"timer:{chat_id}") == 1


def get_stats(chat_id: int) -> ChatStats:
    data = _conn().get(f"stats:{chat_id}")
    if data is None:
        return ChatStats()
    return ChatStats.model_validate_json(data)


def save_stats(chat_id: int, stats: ChatStats) -> None:
    _conn().set(f"stats:{chat_id}", stats.model_dump_json())
