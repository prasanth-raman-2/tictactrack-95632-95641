from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .game_endpoints import router as game_router
from .history_endpoints import router as history_router

app = FastAPI(
    title="Tic Tac Toe Backend API",
    version="0.1.0",
    description=(
        "Backend API for a fullstack tic tac toe game. Provides endpoints for gameplay, "
        "move registration, game state, and history management."
    ),
    openapi_tags=[
        {"name": "Game", "description": "Gameplay operations"},
        {"name": "History", "description": "Game history management"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for game and history endpoints
app.include_router(game_router)
app.include_router(history_router)


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint. Returns service status."""
    return {"message": "Healthy"}
