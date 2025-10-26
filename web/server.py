"""
FastAPI backend for Threesome web game.
Wraps the existing game logic and exposes REST API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import sys
from pathlib import Path

# Add parent directory to path to import game modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.board import Board
from game.entities import Color

app = FastAPI(title="Threesome Game API")

# In-memory game sessions (use Redis/DB for production)
games: Dict[str, Board] = {}

class NewGameRequest(BaseModel):
    width: int = 8
    height: int = 8
    num_pieces: int = 3
    colors: Optional[List[str]] = None

class MoveRequest(BaseModel):
    piece_id: int
    target_x: int
    target_y: int

class SkillMoveRequest(BaseModel):
    piece_id: int
    target_x: int
    target_y: int

def serialize_board(board: Board) -> Dict[str, Any]:
    """Convert Board object to JSON-serializable dict."""
    pieces_data = []
    for piece in board.pieces:
        pieces_data.append({
            "piece_id": piece.piece_id,
            "player": piece.player,
            "loc": piece.loc,
            "color": piece.color.value if piece.color else None,
            "tile_color": piece.tile_color.value if piece.tile_color else None,
            "dest": piece.dest
        })
    
    # Serialize color grid
    color_grid = []
    for row in board.color_grid:
        color_grid.append([c.value if c else None for c in row])
    
    # Get blocked tiles
    blocked_tiles = {}
    for y in range(board.h):
        for x in range(board.w):
            if hasattr(board, 'blocked_tiles') and (x, y) in board.blocked_tiles:
                blocked_tiles[f"{x},{y}"] = board.blocked_tiles[(x, y)]
    
    # Serialize color skills mapping
    color_skills = {}
    for color, skill in board.color_skills.skills.items():
        color_skills[color.value] = skill.name
    
    return {
        "width": board.w,
        "height": board.h,
        "turn": board.turn,
        "rounds": board.rounds,
        "pieces": pieces_data,
        "color_grid": color_grid,
        "blocked_tiles": blocked_tiles,
        "color_skills": color_skills,
        "winner": board.winner(return_ids=True)
    }

@app.post("/api/new_game")
def new_game(req: NewGameRequest):
    """Create a new game session."""
    game_id = str(uuid.uuid4())
    
    # Parse colors if provided
    colors = None
    if req.colors:
        colors = [Color(c) for c in req.colors]
    
    board = Board(
        w=req.width,
        h=req.height,
        color_pallete=colors,
        num_of_pieces=req.num_pieces
    )
    games[game_id] = board
    
    return {
        "game_id": game_id,
        "state": serialize_board(board)
    }

@app.get("/api/game/{game_id}")
def get_game_state(game_id: str):
    """Get current game state."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return serialize_board(games[game_id])

@app.post("/api/game/{game_id}/move")
def make_move(game_id: str, move: MoveRequest):
    """Make a normal move."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = games[game_id]
    
    # Find the piece
    piece = next((p for p in board.pieces if p.piece_id == move.piece_id), None)
    if not piece:
        raise HTTPException(status_code=400, detail="Piece not found")
    
    # Check if it's the right player's turn
    if piece.player != board.turn:
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # Get legal moves
    legal_moves = board.get_legal_moves(piece)
    target = (move.target_x, move.target_y)
    
    if target not in legal_moves:
        raise HTTPException(status_code=400, detail="Illegal move")
    
    # Make the move
    board.apply(piece, target)
    
    return serialize_board(board)

@app.post("/api/game/{game_id}/skill_move")
def make_skill_move(game_id: str, move: SkillMoveRequest):
    """Make a skill-based move."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = games[game_id]
    
    # Find the piece
    piece = next((p for p in board.pieces if p.piece_id == move.piece_id), None)
    if not piece:
        raise HTTPException(status_code=400, detail="Piece not found")
    
    # Check if it's the right player's turn
    if piece.player != board.turn:
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # Get skill targets
    skill_targets = board.color_skills.get_legal_targets(board, piece)
    target = (move.target_x, move.target_y)
    
    # Check if target is valid (handle both simple coords and complex targets)
    valid_target = False
    actual_target = target
    
    for t in skill_targets:
        if isinstance(t, tuple) and len(t) == 2:
            if hasattr(t[0], 'piece_id'):
                # MoveOpponent: check if it matches (piece, coord)
                if t[1] == target:
                    valid_target = True
                    actual_target = t  # Use the (Piece, Coord) format
                    break
            elif t == target:
                valid_target = True
                break
        elif t == target:
            valid_target = True
            break
    
    if not valid_target:
        raise HTTPException(status_code=400, detail="Illegal skill target")
    
    # Apply skill
    board.color_skills.apply_skill(board, piece, actual_target)
    
    return serialize_board(board)

@app.get("/api/game/{game_id}/legal_moves/{piece_id}")
def get_legal_moves(game_id: str, piece_id: int):
    """Get legal moves for a piece."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = games[game_id]
    piece = next((p for p in board.pieces if p.piece_id == piece_id), None)
    if not piece:
        raise HTTPException(status_code=400, detail="Piece not found")
    
    legal_moves = board.get_legal_moves(piece)
    return {"moves": list(legal_moves)}

@app.get("/api/game/{game_id}/skill_targets/{piece_id}")
def get_skill_targets(game_id: str, piece_id: int):
    """Get skill targets for a piece."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = games[game_id]
    piece = next((p for p in board.pieces if p.piece_id == piece_id), None)
    if not piece:
        raise HTTPException(status_code=400, detail="Piece not found")
    
    skill_targets = board.color_skills.get_legal_targets(board, piece)
    
    # Convert to serializable format (handle complex targets like MoveOpponent)
    serializable_targets = []
    for target in skill_targets:
        if isinstance(target, tuple) and len(target) == 2:
            # Check if it's (Piece, Coord) format
            if hasattr(target[0], 'piece_id'):
                # MoveOpponent target: convert to (piece_id, coord)
                serializable_targets.append((target[0].piece_id, target[1]))
            else:
                # Regular coord tuple
                serializable_targets.append(target)
        else:
            serializable_targets.append(target)
    
    return {"targets": serializable_targets}

@app.delete("/api/game/{game_id}")
def delete_game(game_id: str):
    """Delete a game session."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    del games[game_id]
    return {"message": "Game deleted"}

# Serve static files
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

@app.get("/")
def serve_index():
    """Serve the main game page."""
    return FileResponse(str(Path(__file__).parent / "static" / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

