from abc import ABC, abstractmethod
from typing import List, Tuple, Union
from .entities import Coord, Color, Piece

class Skill(ABC):
    """Abstract base class for all skills."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable skill name."""
        pass
    
    @property
    @abstractmethod
    def skill_type(self) -> str:
        """Type of skill: 'moving' or 'blocking'."""
        pass
    
    @abstractmethod
    def get_description(self, intensity: int) -> str:
        """Get description of what skill does at given intensity."""
        pass
    
    @abstractmethod
    def get_value(self, intensity: int) -> int:
        """Get numeric effect value (range, duration, etc) at given intensity."""
        pass
    
    @abstractmethod
    def get_legal_targets(self, board, piece: Piece, intensity: int):
        """
        Get legal targets for this skill.
        Return type depends on skill:
        - Moving skills: List[Coord] or List[Tuple[Piece, Coord]]
        - Blocking skills: List[Coord]
        """
        pass
    
    @abstractmethod
    def apply(self, board, piece: Piece, target, intensity: int):
        """Apply the skill effect."""
        pass
    
    def get_info(self, intensity: int) -> dict:
        """Get complete skill information as a dictionary."""
        return {
            'name': self.name,
            'type': self.skill_type,
            'description': self.get_description(intensity),
            'value': self.get_value(intensity)
        }
    
    @staticmethod
    def get_intensity(board, color: Color, player: int) -> int:
        """Helper to calculate intensity for a color/player combination."""
        intensity = 0
        for piece in board.pieces:
            if piece.tile_color == color and piece.player == player:
                intensity += 1
        if 1 <= intensity <= 3:
            return intensity
        else:
            raise ValueError(f"Invalid intensity: {intensity}")

