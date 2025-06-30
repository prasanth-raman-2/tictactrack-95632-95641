from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
import uuid
import random

router = APIRouter(
    prefix="/game",
    tags=["Game"],
)

# In-memory storage for games and history (to be replaced with persistent storage)
games: Dict[str, dict] = {}  # {game_id: {board, players, ...}}
game_histories: Dict[str, List[dict]] = {}  # {game_id: [move1, move2, ...]}


class CreateGameRequest(BaseModel):
    mode: Literal["human", "ai"] = Field(
        ..., description="Game mode, 'human' or 'ai'"
    )
    player_name: str = Field(
        ..., description="Name of player creating game"
    )


class CreateGameResponse(BaseModel):
    game_id: str = Field(
        ..., description="Unique ID for the game"
    )
    board: List[List[Optional[str]]] = Field(
        ..., description="Initial game board"
    )
    next_turn: str = Field(
        ..., description="'X' or 'O', player to move first"
    )
    players: Dict[str, str] = Field(
        ..., description="Mapping of symbol to player name or AI"
    )


class JoinGameRequest(BaseModel):
    game_id: str = Field(
        ..., description="ID of game to join"
    )
    player_name: str = Field(
        ..., description="Joining player's name"
    )


class JoinGameResponse(BaseModel):
    game_id: str
    board: List[List[Optional[str]]]
    next_turn: str
    players: Dict[str, str]
    mode: str


class MoveRequest(BaseModel):
    game_id: str = Field(
        ..., description="ID of the game"
    )
    player: str = Field(
        ..., description="'X' or 'O'"
    )
    row: int = Field(
        ..., ge=0, le=2
    )
    col: int = Field(
        ..., ge=0, le=2
    )


class MoveResult(BaseModel):
    board: List[List[Optional[str]]]
    next_turn: Optional[str]
    winner: Optional[str]
    draw: bool
    move_history: List[dict]
    ai_move: Optional[dict] = None


def create_empty_board():
    return [[None, None, None], [None, None, None], [None, None, None]]


def check_winner(board):
    # Returns 'X', 'O', or None
    lines = (
        [board[0], board[1], board[2]]
        + [[board[r][c] for r in range(3)] for c in range(3)]
        + [[board[i][i] for i in range(3)]]
        + [[board[i][2 - i] for i in range(3)]]
    )
    for line in lines:
        if all(cell == 'X' for cell in line):
            return 'X'
        if all(cell == 'O' for cell in line):
            return 'O'
    return None


def is_draw(board):
    return all(cell in ('X', 'O') for row in board for cell in row) and not check_winner(board)


def get_available_moves(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]


def ai_move_logic(board):
    # Trivial AI: pick random empty cell
    available = get_available_moves(board)
    if available:
        return random.choice(available)
    return None


def move_to_dict(player, row, col):
    return {"player": player, "row": row, "col": col}


# PUBLIC_INTERFACE
@router.post(
    "/start",
    response_model=CreateGameResponse,
    summary="Create a new game",
    description=(
        "Creates a new Tic Tac Toe game. Specify mode as 'human' or 'ai'. "
        "Returns new game ID."
    ),
    status_code=201,
    responses={201: {"model": CreateGameResponse}},
)
def start_game(req: CreateGameRequest):
    """
    Creates a new Tic Tac Toe game session.

    Args:
        req (CreateGameRequest): Request containing mode and player name.

    Returns:
        CreateGameResponse: Details of the new game.
    """
    try:
        game_id = str(uuid.uuid4())
        mode = req.mode
        players = {}
        players['X'] = req.player_name
        if mode == "ai":
            players['O'] = 'AI'
        else:
            # Return a placeholder until another player joins, must be a string not None
            players['O'] = "Waiting"

        board = create_empty_board()
        games[game_id] = {
            "board": board,
            "players": players,
            "mode": mode,
            "next_turn": 'X',
            "winner": None,
            "draw": False,
        }
        game_histories[game_id] = []

        # Defensive: ensure object values are list-of-list-of-None-or-str for board
        api_board = [[cell if cell is not None else None for cell in row] for row in board]

        return CreateGameResponse(
            game_id=game_id,
            board=api_board,
            next_turn="X",
            players=players
        )
    except Exception as e:
        # Log the exception and return a well-formed HTTP error
        import traceback
        print("Exception in /game/start:", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# PUBLIC_INTERFACE
@router.post(
    "/join",
    response_model=JoinGameResponse,
    summary="Join an existing game",
    description=(
        "Join a game by ID if it is in human mode and has only one player."
    ),
    responses={200: {"model": JoinGameResponse}},
)
def join_game(req: JoinGameRequest):
    """
    Allows a user to join an existing human-vs-human game by game ID.

    Args:
        req (JoinGameRequest): Request containing game_id and player_name.

    Returns:
        JoinGameResponse: Game state after join.
    """
    game_id = req.game_id
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    if game["mode"] == "ai":
        raise HTTPException(status_code=400, detail="Cannot join AI-mode games.")
    if game["players"]["O"] is not None:
        raise HTTPException(status_code=400, detail="Game already has two players.")
    game["players"]["O"] = req.player_name

    return JoinGameResponse(
        game_id=game_id,
        board=game["board"],
        next_turn=game["next_turn"],
        players=game["players"],
        mode=game["mode"],
    )


# PUBLIC_INTERFACE
@router.post(
    "/move",
    response_model=MoveResult,
    summary="Submit a move",
    description=(
        "Registers a move for a game. If in AI mode and AI's turn, also returns the AI move."
    ),
    responses={200: {"model": MoveResult}},
)
def make_move(req: MoveRequest):
    """
    Registers a user move and, if in AI mode, also processes AI's move if required.

    Args:
        req (MoveRequest): Contains game_id, player ('X' or 'O'), row, col.

    Returns:
        MoveResult: Updated board, status, and possibly AI move.
    """
    game_id = req.game_id
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found.")
    game = games[game_id]
    board = game["board"]
    if game["winner"] or game["draw"]:
        raise HTTPException(status_code=400, detail="Game is already over.")

    if board[req.row][req.col] is not None:
        raise HTTPException(status_code=400, detail="Cell is already filled.")

    turn = game["next_turn"]
    if req.player != turn:
        raise HTTPException(status_code=400, detail="Not your turn.")

    # Register player's move
    board[req.row][req.col] = req.player
    game_histories[game_id].append(move_to_dict(req.player, req.row, req.col))
    winner = check_winner(board)
    draw = is_draw(board)
    game["winner"] = winner
    game["draw"] = draw

    # Figure out if AI should move (only in AI mode, if not over, and it's AI's turn)
    ai_move_resp = None
    if (
        game["mode"] == "ai"
        and not winner
        and not draw
        and game["players"][game["next_turn"]] == "AI"
    ):
        # Switch turn for AI
        ai_player = game["next_turn"] = "O" if turn == "X" else "X"
        ai_move = ai_move_logic(board)
        if ai_move:
            board[ai_move[0]][ai_move[1]] = ai_player
            game_histories[game_id].append(move_to_dict(ai_player, ai_move[0], ai_move[1]))
            winner = check_winner(board)
            draw = is_draw(board)
            game["winner"] = winner
            game["draw"] = draw
            ai_move_resp = {"player": ai_player, "row": ai_move[0], "col": ai_move[1]}
            game["next_turn"] = "X" if ai_player == "O" else "O"
        else:
            ai_move_resp = None
    else:
        # Normal next player
        if not (winner or draw):
            game["next_turn"] = "O" if turn == "X" else "X"

    return MoveResult(
        board=board,
        next_turn=None if (winner or draw) else game["next_turn"],
        winner=winner,
        draw=draw,
        move_history=game_histories[game_id],
        ai_move=ai_move_resp,
    )
