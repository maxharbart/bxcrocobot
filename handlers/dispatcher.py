import logging

from handlers.commands import COMMAND_HANDLERS
from game.manager import check_guess
from bitrix_client import send_chat_message

logger = logging.getLogger(__name__)


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
        cmd = message.split()[0].lower()
        handler = COMMAND_HANDLERS.get(cmd)
        if handler:
            reply = handler(chat_id, user_id)
        else:
            reply = f"Unknown command: {cmd}"
        send_chat_message(chat_id, reply)
    else:
        result = check_guess(chat_id, user_id, message)
        if result:
            send_chat_message(chat_id, result)
