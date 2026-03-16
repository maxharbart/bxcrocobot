import random

from bitrix_client import send_chat_message, send_private_message
from game.models import ChatStats, GameState, PlayerStats
from services.word_service import get_random_word
from services.timer_service import start_timer, cancel_timer
from services.user_service import get_user_name
from storage.redis_storage import get_game, save_game, delete_game, get_stats, save_stats


# Button helpers
def _btn(text: str, command: str, bg: str = "#3bc8f5", text_color: str = "#fff", block: str = "Y") -> dict:
    return {"TEXT": text, "COMMAND": command, "COMMAND_PARAMS": "", "BG_COLOR": bg, "TEXT_COLOR": text_color, "BLOCK": block}


def _btn_newline() -> dict:
    return {"TYPE": "NEWLINE"}


# Return type: (message, keyboard) or just message
class Reply:
    def __init__(self, text: str, keyboard: list | None = None):
        self.text = text
        self.keyboard = keyboard


def create_game(chat_id: int) -> Reply:
    existing = get_game(chat_id)
    if existing and existing.status not in ("finished", "waiting") and existing.players:
        return Reply("🐊 Игра уже идёт! Используй /stop чтобы завершить.")
    state = GameState()
    save_game(chat_id, state)
    return Reply(
        "🐊 [B]Крокодил![/B]\n\n"
        "Новая игра создана! Нажмите кнопку чтобы присоединиться.",
        keyboard=[
            _btn("✅ Присоединиться", "/join", bg="#4CAF50"),
        ],
    )


def add_player(chat_id: int, user_id: int) -> Reply:
    state = get_game(chat_id)
    if state is None:
        return Reply("❌ Игра не найдена. Создай новую — /crocodile.")
    if user_id in state.players:
        return Reply("⚠️ Ты уже в игре!")
    state.players.append(user_id)
    state.scores.setdefault(str(user_id), 0)
    save_game(chat_id, state)
    name = get_user_name(user_id)
    count = len(state.players)

    keyboard = [_btn("✅ Присоединиться", "/join", bg="#4CAF50")]
    if count >= 2:
        keyboard.append(_btn("🚀 Начать игру", "/start", bg="#FF9800"))

    return Reply(
        f"✅ [B]{name}[/B] в игре! (игроков: {count})",
        keyboard=keyboard,
    )


def remove_player(chat_id: int, user_id: int) -> Reply:
    state = get_game(chat_id)
    if state is None:
        return Reply("❌ Игра не найдена.")
    if user_id not in state.players:
        return Reply("⚠️ Ты не в игре.")
    state.players.remove(user_id)
    save_game(chat_id, state)
    name = get_user_name(user_id)
    if not state.players:
        delete_game(chat_id)
        return Reply(f"👋 [B]{name}[/B] вышел. Игроков не осталось — игра завершена.")
    return Reply(f"👋 [B]{name}[/B] вышел из игры.")


def start_round(chat_id: int) -> Reply:
    state = get_game(chat_id)
    if state is None:
        return Reply("❌ Игра не найдена. Создай новую — /crocodile.")
    if len(state.players) < 2:
        return Reply("⚠️ Нужно минимум 2 игрока!", keyboard=[
            _btn("✅ Присоединиться", "/join", bg="#4CAF50"),
        ])
    if state.status == "active":
        return Reply("⚠️ Раунд уже идёт!")

    state.status = "active"
    state.round += 1
    state.drawer = random.choice(state.players)
    state.word = get_random_word()
    state.votes = {}
    state.voted_users = []
    save_game(chat_id, state)

    drawer_name = get_user_name(state.drawer)
    send_private_message(state.drawer, f"🤫 Твоё слово: [B]{state.word.upper()}[/B]", keyboard=[
        _btn("🔄 Другое слово", "/skip", bg="#FF5722"),
    ])
    start_timer(chat_id)
    return Reply(
        f"🎨 [B]Раунд {state.round}![/B]\n\n"
        f"🎭 [B]{drawer_name}[/B] объясняет слово.\n"
        f"💬 Пишите свои догадки в чат!",
    )


def end_round(chat_id: int, timed_out: bool = False) -> str:
    state = get_game(chat_id)
    if state is None:
        return "❌ Игра не найдена."
    cancel_timer(chat_id)
    word = state.word

    # Update stats
    stats = get_stats(chat_id)
    stats.total_rounds += 1
    if state.drawer:
        uid = str(state.drawer)
        if uid not in stats.player_stats:
            stats.player_stats[uid] = PlayerStats()
        stats.player_stats[uid].drawn += 1
    save_stats(chat_id, stats)

    state.status = "waiting"
    state.word = ""
    state.drawer = None
    save_game(chat_id, state)
    if timed_out:
        send_chat_message(chat_id,
            f"⏰ [B]Время вышло![/B]\n\nСлово было: [B]{word}[/B]",
            keyboard=[
                _btn("🚀 Следующий раунд", "/start", bg="#FF9800"),
                _btn("🛑 Закончить", "/stop", bg="#f44336"),
            ],
        )
    return ""


def check_guess(chat_id: int, user_id: int, message: str) -> Reply | None:
    state = get_game(chat_id)
    if state is None or state.status != "active":
        return None
    if user_id == state.drawer:
        return None
    if user_id not in state.players:
        return None
    if message.strip().lower() == state.word.lower():
        drawer_id = state.drawer
        state.scores[str(user_id)] = state.scores.get(str(user_id), 0) + 10
        state.scores[str(drawer_id)] = state.scores.get(str(drawer_id), 0) + 5
        word = state.word
        cancel_timer(chat_id)

        # Update stats
        stats = get_stats(chat_id)
        stats.words_guessed += 1
        guesser_uid = str(user_id)
        drawer_uid = str(drawer_id)
        if guesser_uid not in stats.player_stats:
            stats.player_stats[guesser_uid] = PlayerStats()
        if drawer_uid not in stats.player_stats:
            stats.player_stats[drawer_uid] = PlayerStats()
        stats.player_stats[guesser_uid].guessed += 1
        stats.player_stats[guesser_uid].points += 10
        stats.player_stats[drawer_uid].drawn += 1
        stats.player_stats[drawer_uid].points += 5
        stats.total_rounds += 1
        save_stats(chat_id, stats)

        # Set voting state
        state.status = "voting"
        state.last_drawer = drawer_id
        state.word = ""
        state.drawer = None
        state.votes = {}
        state.voted_users = []
        save_game(chat_id, state)

        guesser_name = get_user_name(user_id)
        drawer_name = get_user_name(drawer_id)
        return Reply(
            f"🎉 [B]{guesser_name}[/B] угадал(а) слово: [B]{word}[/B]!\n\n"
            f"Как [B]{drawer_name}[/B] объяснял(а)? Голосуйте!",
            keyboard=[
                _btn("🔥 Огонь!", "/vote fire", bg="#FF5722"),
                _btn("👍 Хорошо", "/vote good", bg="#4CAF50"),
                _btn("😐 Ну такое", "/vote meh", bg="#9E9E9E"),
                _btn_newline(),
                _btn("🚀 Следующий раунд", "/start", bg="#FF9800"),
                _btn("🛑 Закончить", "/stop", bg="#f44336"),
            ],
        )
    return None


def handle_vote(chat_id: int, user_id: int, vote_type: str) -> Reply | None:
    state = get_game(chat_id)
    if state is None:
        return None
    if state.status != "voting":
        return None
    if user_id in state.voted_users:
        return Reply("⚠️ Ты уже голосовал!")
    if user_id == state.last_drawer:
        return Reply("⚠️ Нельзя голосовать за себя!")

    vote_labels = {"fire": "🔥", "good": "👍", "meh": "😐"}
    label = vote_labels.get(vote_type, "❓")

    state.votes[str(user_id)] = vote_type
    state.voted_users.append(user_id)
    save_game(chat_id, state)

    voter_name = get_user_name(user_id)
    return Reply(f"{label} [B]{voter_name}[/B] проголосовал(а)!")


def get_scores(chat_id: int) -> Reply:
    state = get_game(chat_id)
    if state is None:
        return Reply("❌ Игра не найдена.")
    if not state.scores:
        return Reply("📊 Очков пока нет.")
    sorted_scores = sorted(state.scores.items(), key=lambda x: x[1], reverse=True)
    lines = ["[B]🏆 Таблица лидеров[/B]", ""]
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, score) in enumerate(sorted_scores):
        name = get_user_name(int(uid))
        medal = medals[i] if i < len(medals) else "  "
        lines.append(f"{medal} [B]{name}[/B] — {score} очков")
    return Reply("\n".join(lines))


def get_chat_stats(chat_id: int) -> Reply:
    stats = get_stats(chat_id)
    if not stats.player_stats:
        return Reply("📊 Статистика пока пуста.")
    lines = [
        "[B]📊 Статистика чата[/B]",
        "",
        f"🎮 Игр сыграно: [B]{stats.games_played}[/B]",
        f"🔄 Раундов: [B]{stats.total_rounds}[/B]",
        f"✅ Слов угадано: [B]{stats.words_guessed}[/B]",
        "",
        "[B]👥 Игроки:[/B]",
    ]
    sorted_players = sorted(
        stats.player_stats.items(),
        key=lambda x: x[1].points,
        reverse=True,
    )
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, ps) in enumerate(sorted_players):
        name = get_user_name(int(uid))
        medal = medals[i] if i < len(medals) else "  "
        lines.append(f"{medal} [B]{name}[/B] — {ps.points} оч. (угадал: {ps.guessed}, объяснял: {ps.drawn})")
    return Reply("\n".join(lines))


def skip_word(chat_id: int, user_id: int) -> Reply | None:
    state = get_game(chat_id)
    if state is None:
        return Reply("❌ Игра не найдена.")
    if state.status != "active":
        return Reply("⚠️ Нет активного раунда.")
    if user_id != state.drawer:
        return Reply("⚠️ Только объясняющий может пропустить слово.")
    state.word = get_random_word()
    save_game(chat_id, state)
    send_private_message(state.drawer, f"🤫 Новое слово: [B]{state.word.upper()}[/B]", keyboard=[
        _btn("🔄 Другое слово", "/skip", bg="#FF5722"),
    ])
    return None


def stop_game(chat_id: int) -> Reply:
    state = get_game(chat_id)
    if state is None:
        return Reply("❌ Игра не найдена.")
    cancel_timer(chat_id)

    # Update stats
    stats = get_stats(chat_id)
    stats.games_played += 1
    save_stats(chat_id, stats)

    scores = get_scores(chat_id)
    delete_game(chat_id)
    return Reply(
        f"🛑 [B]Игра завершена![/B]\n\n{scores.text}\n\n"
        f"Спасибо за игру! 🐊",
        keyboard=[
            _btn("🐊 Новая игра", "/crocodile", bg="#4CAF50"),
        ],
    )
