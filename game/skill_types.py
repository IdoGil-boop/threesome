from typing import List, Tuple
from .skill_base import Skill
from .entities import Coord, Piece, Color
import random

class MoveExtended(Skill):
    """Skill that allows moving multiple squares in one direction."""
    
    @property
    def name(self) -> str:
        return 'Move Extended'
    
    @property
    def skill_type(self) -> str:
        return 'moving'
    
    def get_description(self, intensity: int) -> str:
        value = self.get_value(intensity)
        return f'Move up to {value} squares in one direction'
    
    def get_value(self, intensity: int) -> int:
        return 2 * intensity
    
    def get_legal_targets(self, board, piece: Piece, intensity: int) -> List[Coord]:
        """Returns list of coords this piece can move to with extended range."""
        distance = self.get_value(intensity)
        legal_moves = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            for step in range(1, distance + 1):
                check_x, check_y = piece.loc[0] + dx * step, piece.loc[1] + dy * step
                if not board.in_bound((check_x, check_y)):
                    break
                if board.grid[check_y][check_x] is not None:
                    break
                legal_moves.append((check_x, check_y))
        return legal_moves
    
    def apply(self, board, piece: Piece, target: Coord, intensity: int):
        """Move the piece to target location."""
        board.apply(piece, target)


class MoveOpponent(Skill):
    """Skill that forces opponent pieces to move."""
    
    @property
    def name(self) -> str:
        return 'Move Opponent'
    
    @property
    def skill_type(self) -> str:
        return 'moving'
    
    def get_description(self, intensity: int) -> str:
        value = self.get_value(intensity)
        plural = 's' if value != 1 else ''
        return f'Force opponent piece to move {value} square{plural}'
    
    def get_value(self, intensity: int) -> int:
        return (intensity + 1) // 2
    
    def get_legal_targets(self, board, piece: Piece, intensity: int) -> List[Tuple[Piece, Coord]]:
        """Returns list of (opponent_piece, destination) tuples."""
        distance = self.get_value(intensity)
        legal_moves = []
        for p in board.pieces:
            if p.player != piece.player:
                destinations = board.piece_legal_moves(p, distance, check_turn=False)
                for dest in destinations:
                    legal_moves.append((p, dest))
        return legal_moves
    
    def apply(self, board, piece: Piece, target: Tuple[Piece, Coord], intensity: int):
        """Move the opponent piece to target location."""
        opponent_piece, destination = target
        board.apply(opponent_piece, destination)


class BlockTile(Skill):
    """Skill that blocks tiles for multiple turns."""
    
    @property
    def name(self) -> str:
        return 'Block Tile'
    
    @property
    def skill_type(self) -> str:
        return 'blocking'
    
    def get_description(self, intensity: int) -> str:
        value = self.get_value(intensity)
        plural = 's' if intensity != 1 else ''
        return f'Block a tile for {value} turn{plural}'
    
    def get_value(self, intensity: int) -> int:
        return intensity
    
    def get_legal_targets(self, board, piece: Piece, intensity: int) -> List[Coord]:
        """Returns list of coords that can be blocked."""
        legal_coords = []
        for y in range(board.h):
            for x in range(board.w):
                if board.grid[y][x] is None:
                    legal_coords.append((x, y))
        return legal_coords
    
    def get_affected_tiles(self, board, target: Coord, intensity: int) -> List[Coord]:
        """Returns list of tiles that would be blocked (just the single target)."""
        x, y = target
        if board.in_bound((x, y)) and board.grid[y][x] is None:
            return [(x, y)]
        return []
    
    def apply(self, board, piece: Piece, target: Coord, intensity: int):
        """Block the target tile with negative intensity."""
        x, y = target
        board.grid[y][x] = -intensity * 2
        board.turn = 1 - board.turn
        board.rounds += 1

class BlockingWall(Skill):
    """Skill that blocks a wall of tiles for one turn."""
    
    @property
    def name(self) -> str:
        return 'Blocking Wall'
    
    @property
    def skill_type(self) -> str:
        return 'blocking'
    
    def get_description(self, intensity: int) -> str:
        value = self.get_value(intensity)
        return f'Block up to {value} consecutive tiles for one turn'
    
    def get_value(self, intensity: int) -> int:
        return 2 * intensity + 1
    
    def get_legal_targets(self, board, piece: Piece, intensity: int) -> List[Coord]:
        """Returns list of coords that can be blocked."""
        legal_coords = []
        for y in range(board.h):
            for x in range(board.w):
                legal_coords.append((x, y))
        return legal_coords
    
    def get_affected_tiles(self, board, target: Coord, intensity: int) -> List[Coord]:
        """Returns list of tiles that would be blocked."""
        x, y = target
        affected = []
        
        # Center tile
        if board.in_bound((x, y)) and board.grid[y][x] is None:
            affected.append((x, y))
        
        # Expand left
        for dx in range(1, intensity + 1):
            check_x = x - dx
            if not board.in_bound((check_x, y)) or board.grid[y][check_x] is not None:
                break
            affected.append((check_x, y))
        
        # Expand right
        for dx in range(1, intensity + 1):
            check_x = x + dx
            if not board.in_bound((check_x, y)) or board.grid[y][check_x] is not None:
                break
            affected.append((check_x, y))
        
        return affected
    
    def apply(self, board, piece: Piece, target: Coord, intensity: int):
        """Block the target tile with negative intensity."""
        affected = self.get_affected_tiles(board, target, intensity)
        for coord in affected:
            x, y = coord
            board.grid[y][x] = -2
        
        board.turn = 1 - board.turn
        board.rounds += 1

class ColorSwap(Skill):
    """Skill that swaps the color of two tiles, random for intensity 1, chosen for intensity 2, swaps two tiles at intensity 3"""
    @property
    def name(self) -> str:
        return 'Color Swap'
    
    @property
    def skill_type(self) -> str:
        return 'swapping'
    
    def get_description(self, intensity: int) -> str:
        if intensity == 1:
            return f'Swap the color of a tile at random'
        elif intensity == 2:
            return f'Swap the color of a tile, to a color of your choice'
        elif intensity == 3:
            return f'Swap the color of two tiles you choose'
    
    def get_value(self, intensity: int) -> int:
       pass
    
    def get_legal_targets(self, board, piece: Piece, intensity: int) -> List[Coord]:
        """Returns list of coords that can be swapped."""
        legal_coords = []
        for y in range(board.h):
            for x in range(board.w):
                legal_coords.append((x, y))
        return legal_coords
    
    def get_affected_tiles(self, board, target: Coord, intensity: int) -> List[Coord]:
        """Returns list of tiles that would be swapped."""
        x, y = target
        return [(x, y)]

    def apply(self, board, piece: Piece, target: Coord, intensity: int, target_b: Coord = None, color: Color = None):
        """Swap the color of the two tiles."""
        x, y = target
        if intensity == 1:
            color = board.color_grid[y][x]
            while color == board.color_grid[y][x]:
                color = random.choice(board.color_pallete)
            board.color_grid[y][x] = color
        elif intensity == 2:
            board.color_grid[y][x] = color
        elif intensity == 3:
            temp = board.color_grid[y][x]
            swap_tile_x, swap_tile_y = target_b

            board.color_grid[y][x] = board.color_grid[swap_tile_y][swap_tile_x]
            board.color_grid[swap_tile_y][swap_tile_x] = temp

        board.turn = 1 - board.turn
        board.rounds += 1

# Interface: All available skills
ALL_SKILLS = [
    MoveExtended(),
    MoveOpponent(),
    BlockTile(),
    BlockingWall(),
    ColorSwap(),
]
