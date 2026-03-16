import logging

from bitrix_client import get_user_info

logger = logging.getLogger(__name__)

_name_cache: dict[int, str] = {}


def get_user_name(user_id: int) -> str:
    if user_id in _name_cache:
        return _name_cache[user_id]

    info = get_user_info(user_id)
    if info:
        name = info.get("NAME", "")
        last_name = info.get("LAST_NAME", "")
        full_name = f"{name} {last_name}".strip()
        if full_name:
            _name_cache[user_id] = full_name
            return full_name

    fallback = f"Игрок {user_id}"
    _name_cache[user_id] = fallback
    return fallback
