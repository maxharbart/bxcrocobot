from typing import Callable

from game.manager import (
    create_game,
    add_player,
    remove_player,
    start_round,
    get_scores,
    skip_word,
    stop_game,
)


def _cmd_crocodile(chat_id: int, user_id: int) -> str:
    return create_game(chat_id)


def _cmd_join(chat_id: int, user_id: int) -> str:
    return add_player(chat_id, user_id)


def _cmd_leave(chat_id: int, user_id: int) -> str:
    return remove_player(chat_id, user_id)


def _cmd_start(chat_id: int, user_id: int) -> str:
    return start_round(chat_id)


def _cmd_score(chat_id: int, user_id: int) -> str:
    return get_scores(chat_id)


def _cmd_skip(chat_id: int, user_id: int) -> str:
    return skip_word(chat_id, user_id)


def _cmd_stop(chat_id: int, user_id: int) -> str:
    return stop_game(chat_id)


COMMAND_HANDLERS: dict[str, Callable[[int, int], str]] = {
    "/crocodile": _cmd_crocodile,
    "/join": _cmd_join,
    "/leave": _cmd_leave,
    "/start": _cmd_start,
    "/score": _cmd_score,
    "/skip": _cmd_skip,
    "/stop": _cmd_stop,
}
