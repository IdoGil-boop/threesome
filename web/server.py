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
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import game modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.board import Board
from game.entities import Color
from game import create_ai_opponent

app = FastAPI(title="Threesome Game API")

# In-memory game sessions (use Redis/DB for production)
games: Dict[str, Board] = {}
# Track AI settings per game
game_ai_settings: Dict[str, Dict[str, Any]] = {}

# Leaderboard storage (file-based for simplicity, use proper DB in production)
LEADERBOARD_FILE = Path(__file__).parent / "leaderboard.json"

def load_leaderboard() -> List[Dict[str, Any]]:
    """Load leaderboard from file."""
    if LEADERBOARD_FILE.exists():
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_leaderboard(scores: List[Dict[str, Any]]):
    """Save leaderboard to file."""
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")

class NewGameRequest(BaseModel):
    width: int = 8
    height: int = 8
    num_pieces: int = 3
    colors: Optional[List[str]] = None
    proportions: Optional[Dict[str, float]] = None
    force_starting_color: Optional[str] = None
    ai_enabled: bool = True
    ai_player: int = 1  # Which player is AI (0 or 1)
    ai_depth: int = 3

class MoveRequest(BaseModel):
    piece_id: int
    target_x: int
    target_y: int

class SkillMoveRequest(BaseModel):
    piece_id: int
    target_x: int
    target_y: int

class LeaderboardEntry(BaseModel):
    name: str
    score: int
    rounds: int
    time_seconds: int

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
    
    # Get blocked tiles (stored as negative values in grid)
    blocked_tiles = {}
    for y in range(board.h):
        for x in range(board.w):
            cell_value = board.grid[y][x]
            if cell_value is not None and cell_value < 0:
                # Negative values indicate blocked tiles
                # Calculate rounds remaining: abs(value) // 2
                rounds_remaining = abs(cell_value) // 2
                blocked_tiles[f"{x},{y}"] = rounds_remaining
    
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
        try:
            colors = [Color[c.upper()] for c in req.colors]
        except (KeyError, AttributeError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid color in palette: {req.colors} - {str(e)}")
    
    # Parse proportions if provided
    color_proportions = None
    if req.proportions:
        color_proportions = {}
        for color_str, proportion in req.proportions.items():
            try:
                color_proportions[Color[color_str.upper()]] = proportion
            except (KeyError, AttributeError) as e:
                raise HTTPException(status_code=400, detail=f"Invalid color in proportions: {color_str} - {str(e)}")
    
    # Parse force starting color if provided
    # Explicitly check if it's None/null to override Board's default
    force_color = None
    force_color_provided = False
    if req.force_starting_color is not None and req.force_starting_color.lower() not in ['none', 'null']:
        try:
            force_color = Color[req.force_starting_color.upper()]
            force_color_provided = True
        except (KeyError, AttributeError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid force starting color: {req.force_starting_color} - {str(e)}")
    elif req.force_starting_color is not None:
        # Explicitly set to None (override Board default)
        force_color_provided = True
    
    try:
        # Build kwargs only with provided values
        board_kwargs = {
            "w": req.width,
            "h": req.height,
            "num_of_pieces": req.num_pieces,
        }
        
        if colors is not None:
            board_kwargs["color_pallete"] = colors
        
        if color_proportions is not None:
            board_kwargs["color_proportions"] = color_proportions
        
        # Always pass force_starting_tiles if it was explicitly provided (even if None)
        if force_color_provided:
            board_kwargs["force_starting_tiles"] = force_color
        
        board = Board(**board_kwargs)
        games[game_id] = board
        
        # Store AI settings
        game_ai_settings[game_id] = {
            "enabled": req.ai_enabled,
            "player": req.ai_player,
            "depth": req.ai_depth
        }
        
        return {
            "game_id": game_id,
            "state": serialize_board(board),
            "ai_settings": game_ai_settings[game_id]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error creating board: {str(e)}")

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
    
    # Check if AI should move next
    result = {"state": serialize_board(board)}
    ai_settings = game_ai_settings.get(game_id, {})
    if ai_settings.get("enabled") and board.turn == ai_settings.get("player") and board.winner(return_ids=True) is None:
        result["ai_should_move"] = True
    
    return result

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
    
    # Check if AI should move next
    result = {"state": serialize_board(board)}
    ai_settings = game_ai_settings.get(game_id, {})
    if ai_settings.get("enabled") and board.turn == ai_settings.get("player") and board.winner(return_ids=True) is None:
        result["ai_should_move"] = True
    
    return result

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

@app.post("/api/game/{game_id}/ai_move")
def make_ai_move(game_id: str):
    """Make an AI move for the current player."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = games[game_id]
    ai_settings = game_ai_settings.get(game_id, {})
    
    if not ai_settings.get("enabled"):
        raise HTTPException(status_code=400, detail="AI is not enabled for this game")
    
    if board.turn != ai_settings.get("player"):
        raise HTTPException(status_code=400, detail="Not AI's turn")
    
    if board.winner(return_ids=True) is not None:
        raise HTTPException(status_code=400, detail="Game is already over")
    
    try:
        # Create AI opponent
        ai = create_ai_opponent(
            board,
            method='minimax',
            depth=ai_settings.get("depth", 3)
        )
        
        # Get best move
        move_result = ai.find_best_move()
        
        if move_result is None:
            # No valid moves found, pass turn
            board.turn = 1 - board.turn
            return {"state": serialize_board(board), "move_type": "pass"}
        
        # Handle different move types
        if len(move_result) == 3:
            # Skill move: (piece_id, target, 'skill')
            piece_id, target, _ = move_result
            piece = board.pieces[piece_id]
            
            # If target is (opponent_piece_id, coord), convert it to (opponent_piece, coord)
            if isinstance(target, tuple) and len(target) == 2 and isinstance(target[0], int) and isinstance(target[1], tuple):
                # MoveOpponent skill: target is (opponent_piece_id, (x, y))
                opponent_piece_id, coord = target
                opponent_piece = board.pieces[opponent_piece_id]
                target = (opponent_piece, coord)
            
            board.color_skills.apply_skill(board, piece, target)
            move_type = "skill"
        elif len(move_result) == 2:
            # Regular move: (piece_id, coord)
            piece_id, coord = move_result
            piece = board.pieces[piece_id]
            board.apply(piece, coord)
            move_type = "normal"
        else:
            raise HTTPException(status_code=500, detail="Invalid move format from AI")
        
        return {
            "state": serialize_board(board),
            "move_type": move_type,
            "piece_id": piece_id
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

@app.delete("/api/game/{game_id}")
def delete_game(game_id: str):
    """Delete a game session."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    del games[game_id]
    if game_id in game_ai_settings:
        del game_ai_settings[game_id]
    return {"message": "Game deleted"}

@app.get("/api/leaderboard")
def get_leaderboard():
    """Get leaderboard scores sorted by streak."""
    try:
        scores = load_leaderboard()
        # Sort by streak (descending), then by timestamp
        scores.sort(key=lambda x: (x.get('streak', 0), x.get('timestamp', '')), reverse=True)
        # Return top 50
        return {"scores": scores[:50]}
    except Exception as e:
        print(f"Error loading leaderboard: {e}")
        return {"scores": []}

@app.post("/api/leaderboard")
def add_leaderboard_entry(entry: LeaderboardEntry):
    """Add or update leaderboard entry for win streak."""
    scores = load_leaderboard()
    
    # Find existing entry for this player
    existing_entry = None
    for i, score in enumerate(scores):
        if score.get('name') == entry.name[:20]:
            existing_entry = i
            break
    
    if existing_entry is not None:
        # Update existing entry's streak
        scores[existing_entry]['streak'] = entry.score  # score field contains streak
        scores[existing_entry]['rounds'] = entry.rounds
        scores[existing_entry]['time_seconds'] = entry.time_seconds
        scores[existing_entry]['timestamp'] = datetime.now().isoformat()
        updated_entry = scores[existing_entry]
    else:
        # Create new entry
        updated_entry = {
            "name": entry.name[:20],
            "streak": entry.score,  # score field contains streak
            "rounds": entry.rounds,
            "time_seconds": entry.time_seconds,
            "timestamp": datetime.now().isoformat()
        }
        scores.append(updated_entry)
    
    # Keep only top 100 scores
    scores.sort(key=lambda x: x.get('streak', 0), reverse=True)
    scores = scores[:100]
    
    save_leaderboard(scores)
    
    return {"message": "Streak updated", "entry": updated_entry}

# Serve static files
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

@app.get("/")
def serve_index():
    """Serve the main game page."""
    return FileResponse(str(Path(__file__).parent / "static" / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

