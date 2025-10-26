from dataclasses import dataclass
from typing import Tuple, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .skill_base import Skill

Coord = Tuple[int, int]

class Color(Enum):
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'
    YELLOW = 'yellow'
    PURPLE = 'purple'
    ORANGE = 'orange'
    PINK = 'pink'
    BROWN = 'brown'
    GRAY = 'gray'
    BLACK = 'black'
    WHITE = 'white'

class Piece:
    def __init__(self, piece_id: int, player: int, loc: Coord, start_loc: Coord, color: Color, skills: List["Skill"], dest: int = None, tile_color: Color = None):
        self.piece_id = piece_id
        self.player = player
        self._loc = loc
        self.start_loc = start_loc
        self.color = color
        self.skills = skills
        self.dest = dest
        self.tile_color = tile_color
    
    @property
    def loc(self) -> Coord:
        return self._loc
    
    @loc.setter
    def loc(self, value: Coord):
        self._loc = value
    
    def __repr__(self):
        return f"Piece(piece_id={self.piece_id}, player={self.player}, loc={self._loc}, start_loc={self.start_loc}, color={self.color}, skills={self.skills}, dest={self.dest}, tile_color={self.tile_color})"