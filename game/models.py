from pydantic import BaseModel


class GameState(BaseModel):
    players: list[int] = []
    scores: dict[str, int] = {}
    round: int = 0
    drawer: int | None = None
    word: str = ""
    status: str = "waiting"  # waiting | active | finished
