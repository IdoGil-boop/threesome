from typing import List, TYPE_CHECKING
from .entities import Color, Coord, Piece
from .skill_base import Skill
from .skill_types import ALL_SKILLS

if TYPE_CHECKING:
    from .board import Board

class ColorSkills:
    """Manages the mapping of colors to skills and provides skill operations."""
    
    # All available skill classes
    AVAILABLE_SKILLS = ALL_SKILLS
    
    def __init__(self, color_pallete: List[str] = ['red', 'green', 'blue']):
        # Convert string colors to Color enums
        self.color_pallete = [Color(c) for c in color_pallete]
        
        # Assign skills to colors (Color enum -> Skill instance)
        self.skills = {
            color: self.AVAILABLE_SKILLS[i % len(self.AVAILABLE_SKILLS)]
            for i, color in enumerate(self.color_pallete)
        }
    
    def get_skill(self, color: Color) -> Skill:
        """Get the skill associated with a color."""
        return self.skills.get(color)
    
    def get_intensity(self, board: "Board", color: Color, player: int) -> int:
        """Get intensity for a color/player combination. Returns 0 if invalid."""
        try:
            return Skill.get_intensity(board, color, player)
        except ValueError:
            # Invalid intensity (0 or >3), return 0
            return 0
    
    def get_skill_info(self, color: Color, intensity: int) -> dict:
        """
        Returns a dictionary with skill information for a given color and intensity.
        Returns:
        {
            'name': str,        # Skill name
            'type': str,        # Skill type
            'description': str, # What the skill does at this intensity
            'value': int        # Numeric effect (range, duration, etc)
        }
        """
        skill = self.get_skill(color)
        if not skill:
            return {
                'name': 'Basic Move',
                'type': 'moving',
                'description': 'Move 1 square',
                'value': 1
            }
        return skill.get_info(intensity)
    
    def get_color_skill_map(self) -> dict:
        """Returns mapping of colors to their skill names."""
        return {color: skill.name for color, skill in self.skills.items()}
    
    def get_legal_targets(self, board: "Board", piece: Piece) -> List[Coord]:
        """
        Get legal targets for a piece based on its tile color skill.
        Returns:
        - For moving skills: List[Coord] or List[Tuple[Piece, Coord]]
        - For blocking skills: List[Coord]
        """
        skill = self.get_skill(piece.tile_color)
        if skill:
            intensity = Skill.get_intensity(board, piece.tile_color, piece.player)
            return skill.get_legal_targets(board, piece, intensity)
        else:
            # Default behavior if color not in palette
            return board.piece_legal_moves(piece, 1)
    
    def apply_skill(self, board: "Board", piece: Piece, target: Coord):
        """
        Apply skill effect based on the piece's tile color.
        - For MoveExtended: target is a Coord destination for the piece
        - For MoveOpponent: target is a Tuple[Piece, Coord] - which opponent piece to move where
        - For BlockTile: target is a Coord to block
        """
        skill = self.get_skill(piece.tile_color)
        if skill is None:
            # No skill for this color, just do basic move
            board.apply(piece, target)
            try:
                board.log_board_state("after basic move (no skill)")
            except Exception:
                pass
            return
        
        intensity = Skill.get_intensity(board, piece.tile_color, piece.player)
        
        # Verbose skill usage log (covers both user and AI) unless suppressed on simulation copies
        if not getattr(board, '_suppress_logs', False):
            try:
                if isinstance(target, tuple) and len(target) == 2 and hasattr(target[0], 'piece_id'):
                    tgt_desc = f"(opp#{target[0].piece_id}, {target[1]})"
                else:
                    tgt_desc = str(target)
                print(f"Applying skill: {skill.name} by piece {piece.piece_id} (player={piece.player}) target={tgt_desc} intensity={intensity}")
            except Exception:
                pass
        
        # Consume tiles that contributed to the skill
        board.consume_tiles(piece.tile_color, piece.player)
        
        skill.apply(board, piece, target, intensity)

        # Do not auto-log board state here; UI/consumers handle post-action logging

