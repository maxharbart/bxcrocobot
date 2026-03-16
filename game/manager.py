import random

from bitrix_client import send_chat_message, send_private_message
from game.models import ChatStats, GameState, PlayerStats
from services.word_service import get_random_word
from services.timer_service import start_timer, cancel_timer
from services.user_service import get_user_name
from storage.redis_storage import get_game, save_game, delete_game, get_stats, save_stats


def create_game(chat_id: int) -> str:
    existing = get_game(chat_id)
    if existing and existing.status not in ("finished", "waiting") and existing.players:
        return "🐊 Игра уже идёт! Используй /stop чтобы завершить."
    state = GameState()
    save_game(chat_id, state)
    return (
        "🐊 [B]Крокодил![/B]\n\n"
        "Новая игра создана!\n"
        "Присоединиться — /join\n"
        "Начать игру — /start"
    )


def add_player(chat_id: int, user_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "❌ Игра не найдена. Создай новую — /crocodile."
    if user_id in state.players:
        return "⚠️ Ты уже в игре!"
    state.players.append(user_id)
    state.scores.setdefault(str(user_id), 0)
    save_game(chat_id, state)
    name = get_user_name(user_id)
    return f"✅ [B]{name}[/B] в игре! (игроков: {len(state.players)})"


def remove_player(chat_id: int, user_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "❌ Игра не найдена."
    if user_id not in state.players:
        return "⚠️ Ты не в игре."
    state.players.remove(user_id)
    save_game(chat_id, state)
    name = get_user_name(user_id)
    if not state.players:
        delete_game(chat_id)
        return f"👋 [B]{name}[/B] вышел. Игроков не осталось — игра завершена."
    return f"👋 [B]{name}[/B] вышел из игры."


def start_round(chat_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "❌ Игра не найдена. Создай новую — /crocodile."
    if len(state.players) < 2:
        return "⚠️ Нужно минимум 2 игрока!"
    if state.status == "active":
        return "⚠️ Раунд уже идёт!"

    state.status = "active"
    state.round += 1
    state.drawer = random.choice(state.players)
    state.word = get_random_word()
    save_game(chat_id, state)

    drawer_name = get_user_name(state.drawer)
    send_private_message(state.drawer, f"🤫 Твоё слово: [B]{state.word.upper()}[/B]\nПропустить — /skip")
    start_timer(chat_id)
    return (
        f"🎨 [B]Раунд {state.round}![/B]\n\n"
        f"🎭 [B]{drawer_name}[/B] объясняет слово.\n"
        f"💬 Пишите свои догадки в чат!"
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
            f"⏰ [B]Время вышло![/B]\n\n"
            f"Слово было: [B]{word}[/B]\n"
            f"Следующий раунд — /start"
        )
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

        state.status = "waiting"
        state.word = ""
        state.drawer = None
        save_game(chat_id, state)

        guesser_name = get_user_name(user_id)
        drawer_name = get_user_name(drawer_id)
        return (
            f"🎉 [B]{guesser_name}[/B] угадал(а) слово: [B]{word}[/B]!\n\n"
            f"Объяснял(а): [B]{drawer_name}[/B]\n"
            f"Следующий раунд — /start"
        )
    return None


def get_scores(chat_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "❌ Игра не найдена."
    if not state.scores:
        return "📊 Очков пока нет."
    sorted_scores = sorted(state.scores.items(), key=lambda x: x[1], reverse=True)
    lines = ["[B]🏆 Таблица лидеров[/B]", ""]
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, score) in enumerate(sorted_scores):
        name = get_user_name(int(uid))
        medal = medals[i] if i < len(medals) else "  "
        lines.append(f"{medal} [B]{name}[/B] — {score} очков")
    return "\n".join(lines)


def get_chat_stats(chat_id: int) -> str:
    stats = get_stats(chat_id)
    if not stats.player_stats:
        return "📊 Статистика пока пуста."
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
    return "\n".join(lines)


def skip_word(chat_id: int, user_id: int) -> str | None:
    state = get_game(chat_id)
    if state is None:
        return "❌ Игра не найдена."
    if state.status != "active":
        return "⚠️ Нет активного раунда."
    if user_id != state.drawer:
        return "⚠️ Только объясняющий может пропустить слово."
    state.word = get_random_word()
    save_game(chat_id, state)
    send_private_message(state.drawer, f"🤫 Новое слово: [B]{state.word.upper()}[/B]\nПропустить — /skip")
    return None


def stop_game(chat_id: int) -> str:
    state = get_game(chat_id)
    if state is None:
        return "❌ Игра не найдена."
    cancel_timer(chat_id)

    # Update stats
    stats = get_stats(chat_id)
    stats.games_played += 1
    save_stats(chat_id, stats)

    scores = get_scores(chat_id)
    delete_game(chat_id)
    return (
        f"🛑 [B]Игра завершена![/B]\n\n"
        f"{scores}\n\n"
        f"Спасибо за игру! 🐊\n"
        f"Новая игра — /crocodile"
    )
