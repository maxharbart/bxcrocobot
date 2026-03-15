import random

from bitrix_client import send_chat_message, send_private_message
from game.models import GameState
from services.word_service import get_random_word
from services.timer_service import start_timer, cancel_timer
from storage.redis_storage import get_game, save_game, delete_game


def create_game(chat_id: int) -> str:
    existing = get_game(chat_id)
    if existing and existing.status != "finished":
        return "A game is already running. Use /stop to end it first."
    state = GameState()
    save_game(chat_id, state)
    return "Game created! Players can join using /join. Start with /start."


def add_player(chat_id: int, user_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "No game found. Create one with /crocodile."
    if user_id in state.players:
        return "You already joined!"
    state.players.append(user_id)
    state.scores.setdefault(str(user_id), 0)
    save_game(chat_id, state)
    return f"Player {user_id} joined! ({len(state.players)} players)"


def remove_player(chat_id: int, user_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "No game found."
    if user_id not in state.players:
        return "You are not in the game."
    state.players.remove(user_id)
    save_game(chat_id, state)
    if not state.players:
        delete_game(chat_id)
        return "You left. No players remaining — game ended."
    return "You left the game."


def start_round(chat_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "No game found. Create one with /crocodile."
    if len(state.players) < 2:
        return "Need at least 2 players to start."
    if state.status == "active":
        return "A round is already in progress!"

    state.status = "active"
    state.round += 1
    state.drawer = random.choice(state.players)
    state.word = get_random_word()
    save_game(chat_id, state)

    send_private_message(state.drawer, f"Your word: {state.word.upper()}")
    start_timer(chat_id)
    return f"Round {state.round} started! Player {state.drawer} is drawing. Guess the word!"


def end_round(chat_id: int, timed_out: bool = False) -> str:
    state = get_game(chat_id)
    if state is None:
        return "No game found."
    cancel_timer(chat_id)
    word = state.word
    state.status = "waiting"
    state.word = ""
    state.drawer = None
    save_game(chat_id, state)
    if timed_out:
        msg = f"Time's up! The word was: {word}. Use /start for the next round."
        send_chat_message(chat_id, msg)
        return msg
    return ""


def check_guess(chat_id: int, user_id: int, message: str) -> str | None:
    state = get_game(chat_id)
    if state is None or state.status != "active":
        return None
    if user_id == state.drawer:
        return None
    if user_id not in state.players:
        return None
    if message.strip().lower() == state.word.lower():
        state.scores[str(user_id)] = state.scores.get(str(user_id), 0) + 10
        state.scores[str(state.drawer)] = state.scores.get(str(state.drawer), 0) + 5
        word = state.word
        cancel_timer(chat_id)
        state.status = "waiting"
        state.word = ""
        state.drawer = None
        save_game(chat_id, state)
        return (
            f"Correct! Player {user_id} guessed the word: {word}!\n"
            f"Use /start for the next round."
        )
    return None


def get_scores(chat_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "No game found."
    if not state.scores:
        return "No scores yet."
    sorted_scores = sorted(state.scores.items(), key=lambda x: x[1], reverse=True)
    lines = ["Leaderboard:", ""]
    for uid, score in sorted_scores:
        lines.append(f"Player {uid} — {score}")
    return "\n".join(lines)


def skip_word(chat_id: int, user_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "No game found."
    if state.status != "active":
        return "No active round."
    if user_id != state.drawer:
        return "Only the drawer can skip."
    old_word = state.word
    state.word = get_random_word()
    save_game(chat_id, state)
    send_private_message(state.drawer, f"New word: {state.word.upper()}")
    return f"Word skipped! (was: {old_word}). Drawer received a new word."


def stop_game(chat_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "No game found."
    cancel_timer(chat_id)
    scores = get_scores(chat_id)
    delete_game(chat_id)
    return f"Game stopped!\n\n{scores}"
