from fastapi import APIRouter

router = APIRouter(
    prefix="/history",
    tags=["History"],
)

# PUBLIC_INTERFACE


@router.get("/")
def view_history():
    """
    Returns the game history for the user.

    Returns:
        dict: Placeholder for game history.
    """
    return {"message": "Game history (placeholder)"}
