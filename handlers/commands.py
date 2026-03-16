from typing import Callable

from game.manager import (
    Reply,
    create_game,
    add_player,
    remove_player,
    start_round,
    get_scores,
    get_chat_stats,
    skip_word,
    stop_game,
    handle_vote,
)


def _cmd_crocodile(chat_id: int, user_id: int, args: str) -> Reply | None:
    return create_game(chat_id)


def _cmd_join(chat_id: int, user_id: int, args: str) -> Reply | None:
    return add_player(chat_id, user_id)


def _cmd_leave(chat_id: int, user_id: int, args: str) -> Reply | None:
    return remove_player(chat_id, user_id)


def _cmd_start(chat_id: int, user_id: int, args: str) -> Reply | None:
    return start_round(chat_id)


def _cmd_score(chat_id: int, user_id: int, args: str) -> Reply | None:
    return get_scores(chat_id)


def _cmd_stats(chat_id: int, user_id: int, args: str) -> Reply | None:
    return get_chat_stats(chat_id)


def _cmd_skip(chat_id: int, user_id: int, args: str) -> Reply | None:
    return skip_word(chat_id, user_id)


def _cmd_stop(chat_id: int, user_id: int, args: str) -> Reply | None:
    return stop_game(chat_id)


def _cmd_vote(chat_id: int, user_id: int, args: str) -> Reply | None:
    return handle_vote(chat_id, user_id, args.strip())


COMMAND_HANDLERS: dict[str, Callable] = {
    "/crocodile": _cmd_crocodile,
    "/join": _cmd_join,
    "/leave": _cmd_leave,
    "/start": _cmd_start,
    "/score": _cmd_score,
    "/stats": _cmd_stats,
    "/skip": _cmd_skip,
    "/stop": _cmd_stop,
    "/vote": _cmd_vote,
}
