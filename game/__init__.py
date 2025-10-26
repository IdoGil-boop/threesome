# Re-export main classes for backward compatibility
from .entities import Color, Piece, Coord
from .board import Board
from .skills import ColorSkills
from .skill_base import Skill
from .skill_types import MoveExtended, MoveOpponent, BlockTile, BlockingWall, ColorSwap
from .ai_opponent_base import AIOpponentBase, methods

def create_ai_opponent(board: Board, method: str = 'minimax', depth: int = 3) -> AIOpponentBase:
    """
    Factory function to create an AI opponent.
    
    Args:
        board: The game board
        method: AI method name ('minimax', etc.)
        depth: Search depth for the AI
    
    Returns:
        An AIOpponent instance
    
    Raises:
        ValueError: If method is not recognized
    """
    if method == 'minimax':
        from .ai_opponent_minmax import AIOpponent
        return AIOpponent(board, methods.minimax, depth=depth)
    else:
        raise ValueError(f"Unknown AI method: {method}. Available methods: ['minimax']")

__all__ = [
    'Color', 'Piece', 'Coord', 'Board', 'ColorSkills', 'Skill', 
    'MoveExtended', 'MoveOpponent', 'BlockTile', 'BlockingWall', 'ColorSwap',
    'AIOpponentBase', 'methods', 'create_ai_opponent'
]

