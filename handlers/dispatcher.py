import logging

from handlers.commands import COMMAND_HANDLERS
from game.manager import check_guess, Reply
from bitrix_client import send_chat_message

logger = logging.getLogger(__name__)


def _send_reply(chat_id: int, reply: Reply | str | None) -> None:
    if reply is None:
        return
    if isinstance(reply, str):
        send_chat_message(chat_id, reply)
    elif isinstance(reply, Reply):
        send_chat_message(chat_id, reply.text, keyboard=reply.keyboard)


def dispatch(event: str, data: dict) -> None:
    if event != "ONIMBOTMESSAGEADD":
        logger.debug("Ignoring event: %s", event)
        return

    message = data.get("PARAMS", {}).get("MESSAGE", "") or data.get("MESSAGE", "")
    user_id = int(data.get("PARAMS", {}).get("FROM_USER_ID", 0) or data.get("FROM_USER_ID", 0))
    chat_id = int(data.get("PARAMS", {}).get("CHAT_ID", 0) or data.get("CHAT_ID", 0))

    if not message or not user_id or not chat_id:
        logger.warning("Incomplete event data: %s", data)
        return

    message = message.strip()

    if message.startswith("/"):
        parts = message.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        handler = COMMAND_HANDLERS.get(cmd)
        if handler:
            reply = handler(chat_id, user_id, args)
        else:
            reply = Reply(f"❓ Неизвестная команда: {cmd}")
        _send_reply(chat_id, reply)
    else:
        result = check_guess(chat_id, user_id, message)
        _send_reply(chat_id, result)
