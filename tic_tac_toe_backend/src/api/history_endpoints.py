from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List

from .game_endpoints import games, game_histories

router = APIRouter(
    prefix="/history",
    tags=["History"],
)


class GameHistoryResponse(BaseModel):
    move_history: List[dict]
    game_id: str


class GameListResponse(BaseModel):
    games: List[dict]


# PUBLIC_INTERFACE
@router.get(
    "/by_game",
    response_model=GameHistoryResponse,
    summary="Get move history for a game",
    description="Returns move history for a given game ID."
)
def get_history_by_game(game_id: str = Query(..., description="Game ID to retrieve history for")):
    """
    Returns move history for a specific game.
    """
    if game_id not in game_histories:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameHistoryResponse(
        move_history=game_histories[game_id],
        game_id=game_id
    )


# PUBLIC_INTERFACE
@router.get(
    "/games_by_player",
    response_model=GameListResponse,
    summary="List games for a player",
    description="Get all games involving a given player name."
)
def list_games_for_player(player: str = Query(..., description="Player name to filter games by (either as X or O)")):
    """
    Returns a list of games the player participated in.
    """
    result = []
    for game_id, game in games.items():
        players = game["players"]
        if players.get("X") == player or players.get("O") == player:
            result.append({
                "game_id": game_id,
                "mode": game["mode"],
                "players": players,
                "winner": game.get("winner"),
                "draw": game.get("draw"),
            })
    return GameListResponse(games=result)


# PUBLIC_INTERFACE
@router.get(
    "/",
    summary="Legacy placeholder",
    description="Returns a static message for legacy compatibility."
)
def view_history():
    """
    Returns placeholder for legacy compatibility.
    """
    return {
        "message": (
            "Game history (placeholder) – use "
            "new endpoints."
        )
    }
