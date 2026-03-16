from pydantic import BaseModel


class GameState(BaseModel):
    players: list[int] = []
    scores: dict[str, int] = {}
    round: int = 0
    drawer: int | None = None
    word: str = ""
    status: str = "waiting"  # waiting | active | finished


class PlayerStats(BaseModel):
    guessed: int = 0
    drawn: int = 0
    points: int = 0


class ChatStats(BaseModel):
    games_played: int = 0
    total_rounds: int = 0
    words_guessed: int = 0
    player_stats: dict[str, PlayerStats] = {}
