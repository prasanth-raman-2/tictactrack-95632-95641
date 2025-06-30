from fastapi import APIRouter

router = APIRouter(
    prefix="/game",
    tags=["Game"],
)

# PUBLIC_INTERFACE


@router.post("/start")
def start_game():
    """
    Starts a new tic tac toe game session.

    Returns:
        dict: Placeholder for game initiation response.
    """
    return {"message": "Game started (placeholder)"}


# PUBLIC_INTERFACE


@router.post("/move")
def make_move():
    """
    Registers a move for the current game.

    Returns:
        dict: Placeholder for move response.
    """
    return {"message": "Move registered (placeholder)"}
