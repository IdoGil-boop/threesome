
from typing import List, Tuple, Optional
import random
import copy
from .entities import Coord, Color, Piece
from .skills import ColorSkills

class Board:
    @staticmethod
    def create_pieces(w: int, h:int, num_pieces: int = 3) -> List[Piece]:
        pieces = []
        piece_id = 0
        
        # Calculate even spacing across the width
        spacing = w / (num_pieces + 1)
        
        for i in range(num_pieces * 2):
            x = int((i % num_pieces + 1) * spacing)
            if i < num_pieces:
                # Player 0 starts at y=0, destination row is h-1
                start_loc, dest = (x, 0), (h - 1)
            else:
                # Player 1 starts at y=h-1, destination row is 0
                start_loc, dest = (x, h - 1), 0
            pieces.append(Piece(piece_id=piece_id, player=i//num_pieces, loc=start_loc, start_loc=start_loc, dest=dest, color=None, skills=[]))
            piece_id += 1
        return pieces

    def __init__(self, w:int = 8, h:int = 8, color_pallete:List[Color] = None, num_of_pieces:int = 3, color_proportions:dict = None, player_colors:Tuple[Color, Color] = (Color.WHITE, Color.BLACK), force_starting_tiles:Optional[Color] = Color.RED):
        self.w, self.h = w, h
        self.rounds = 0
        self.move_history: List[Tuple[str, int, Tuple[int, int], Tuple[int, int]]] = []  # (kind, piece_id, from, to)
        self._suppress_logs = False  # Set True on simulation copies to avoid noisy logs
        if color_pallete is None:
            color_pallete = [Color.RED, Color.GREEN, Color.BLUE]
        self.color_pallete = list(color_pallete)
        self.player_colors = player_colors  # Fixed colors for each player's pieces
        
        # Initialize color-to-skill mapping
        self.color_skills = ColorSkills([c.value for c in self.color_pallete])
        
        # Setup color proportions (including None for gray tiles with no skill)
        if color_proportions is None:
            # Uniform distribution by default (including gray/None)
            all_colors = self.color_pallete + [None]
            color_proportions = {c: 1.0 / len(all_colors) for c in all_colors}
        
        # Create weighted color list for random selection
        weighted_colors = []
        for color, proportion in color_proportions.items():
            weighted_colors.extend([color] * int(proportion * 100))
        
        self.color_grid = [[random.choice(weighted_colors) for _ in range(w)] for _ in range(h)]
        self.original_color_grid = [[self.color_grid[j][i] for i in range(w)] for j in range(h)]  # Store original colors
        self.consumed_tiles = set()  # Track tiles that have been consumed by skills
        self.grid = [[None for _ in range(w)] for _ in range(h)]
        self.pieces = self.create_pieces(w,h,num_of_pieces)
        for piece in self.pieces:
            x, y = piece.loc
            # Piece visual color is based on player
            piece.color = self.player_colors[piece.player]
            if force_starting_tiles:
                if force_starting_tiles not in self.color_pallete:
                    raise ValueError(f"Force starting tiles color {force_starting_tiles} is not in color pallete")
                self.color_grid[y][x] = force_starting_tiles
                self.original_color_grid[y][x] = force_starting_tiles
                piece.tile_color = force_starting_tiles
            else:
                piece.tile_color = self.color_grid[y][x]
            self.grid[y][x] = piece.piece_id
        self.turn = 0
    
    def copy(self):
        """Create a deep copy of the board state."""
        board_copy = Board.__new__(Board)
        board_copy.w = self.w
        board_copy.h = self.h
        board_copy.rounds = self.rounds
        board_copy.turn = self.turn
        board_copy.move_history = self.move_history.copy()
        board_copy.color_pallete = self.color_pallete.copy()
        board_copy.player_colors = self.player_colors
        board_copy._suppress_logs = self._suppress_logs
        
        # Deep copy grids
        board_copy.color_grid = [row[:] for row in self.color_grid]
        board_copy.original_color_grid = [row[:] for row in self.original_color_grid]
        board_copy.grid = [row[:] for row in self.grid]
        board_copy.consumed_tiles = self.consumed_tiles.copy()
        
        # Deep copy pieces - create completely new Piece objects manually to avoid any shared references
        board_copy.pieces = []
        for piece in self.pieces:
            from .entities import Piece
            new_piece = Piece(
                piece_id=piece.piece_id,
                player=piece.player,
                loc=piece.loc,  # tuple is immutable, this is safe
                start_loc=piece.start_loc,
                color=piece.color,
                skills=piece.skills.copy(),  # shallow copy of list is fine
                dest=piece.dest,
                tile_color=piece.tile_color
            )
            board_copy.pieces.append(new_piece)
        
        # Copy color skills (need to create new instance)
        board_copy.color_skills = ColorSkills([c.value for c in self.color_pallete])
        
        return board_copy
    
    def in_bound(self, coord: Coord) -> bool:
        """Check if coordinates are within board bounds."""
        x, y = coord
        return 0 <= x < self.w and 0 <= y < self.h
    
    def piece_legal_moves(self, piece:Piece, distance:int = 1, check_turn:bool = True) -> List[Coord]:
        """Get list of destination coords for a piece."""
        moves = []
        if check_turn and piece.player != self.turn:
            return moves

        x, y = piece.loc
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            # Check all tiles along the path
            blocked = False
            for step in range(1, distance + 1):
                check_x, check_y = x + dx * step, y + dy * step
                if not self.in_bound((check_x, check_y)):
                    blocked = True
                    break
                
                cell_val = self.grid[check_y][check_x]
                # Blocked if there's a piece or a blocked tile
                if cell_val is not None:
                    blocked = True
                    break
            
            # Only add if not blocked and destination is valid
            if not blocked:
                nx, ny = x + dx * distance, y + dy * distance
                moves.append((nx, ny))
        return moves
    
    def get_legal_moves(self, piece: Piece, check_turn: bool = True) -> List[Coord]:
        """Alias for piece_legal_moves for AI compatibility."""
        return self.piece_legal_moves(piece, distance=1, check_turn=check_turn)

    def apply(self, piece: Piece, destination: Coord):
        """Move a piece to destination and update game state."""
        sx, sy = piece.loc
        dx, dy = destination

        # Restore the tile the piece is leaving if it was consumed
        if (sx, sy) in self.consumed_tiles:
            self.color_grid[sy][sx] = self.original_color_grid[sy][sx]
            self.consumed_tiles.remove((sx, sy))

        # Move piece in grid
        piece_id = self.grid[sy][sx]
        self.grid[dy][dx] = piece_id
        self.grid[sy][sx] = None
        
        # Update piece location and tile color (visual color stays the same - it's based on player)
        piece.loc = (dx, dy)
        piece.tile_color = self.color_grid[dy][dx]

        # Record move in history
        self.move_history.append(('move', piece.piece_id, (sx, sy), (dx, dy)))

        # Decrement blocked tiles (negative values move toward 0)
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] is not None and self.grid[y][x] < 0:
                    self.grid[y][x] += 1
                    if self.grid[y][x] == 0:
                        self.grid[y][x] = None

        # Switch turns (0 -> 1, 1 -> 0)
        self.turn = 1 - self.turn
        self.rounds += 1

    def board_state_str(self) -> str:
        """Return a human-readable snapshot of the current board state."""
        lines = []
        try:
            lines.append(f"Turn: {self.turn} | Rounds: {self.rounds} | Winner: {self.winner()}")
            lines.append("Pieces:")
            for p in self.pieces:
                dest_y = p.dest[1] if isinstance(p.dest, tuple) else p.dest
                tile = getattr(p.tile_color, 'value', None)
                lines.append(f"  P{p.player}#{p.piece_id} at {p.loc} dest={dest_y} tile={tile}")

            lines.append("Grid (P{player}{id} for pieces, Bn for blocked):")
            for y in range(self.h):
                row = []
                for x in range(self.w):
                    val = self.grid[y][x]
                    if val is None:
                        row.append("..")
                    elif val >= 0:
                        piece = self.pieces[val]
                        row.append(f"{piece.player}{val}")
                    else:
                        row.append(f"B{abs(val)}")
                lines.append(" ".join(row))

            lines.append("Colors (first letter, . for gray):")
            for y in range(self.h):
                row = []
                for x in range(self.w):
                    c = self.color_grid[y][x]
                    row.append('.' if c is None else c.value[0].upper())
                lines.append(" ".join(row))
        except Exception as e:
            lines.append(f"[board_state_str error: {e}]")
        return "\n".join(lines)

    def log_board_state(self, context: str = ""):
        """Print the board state to stdout, labeled by context."""
        if getattr(self, "_suppress_logs", False):
            return
        header = f"=== BOARD STATE ===" if not context else f"=== BOARD STATE - {context} ==="
        print(header)
        print(self.board_state_str())
        print("=== END BOARD STATE ===\n")

    def consume_tiles(self, color: Color, player: int):
        """Turn tiles gray that contributed to skill intensity."""
        for piece in self.pieces:
            if piece.tile_color == color and piece.player == player:
                x, y = piece.loc
                self.consumed_tiles.add((x, y))
                self.color_grid[y][x] = None  # Turn gray
                piece.tile_color = None  # Update piece's tile color to gray

    def winner(self, return_ids: bool = False) -> Optional[str]:
        # A player wins if one of their pieces reaches the opponent's starting row
        # Player 0 starts at y=0, so they win by reaching y=h-1
        # Player 1 starts at y=h-1, so they win by reaching y=0
        for piece in self.pieces:
            y = piece.loc[1]
            if piece.player == 0 and y == self.h - 1:
                return 0 if return_ids else self.player_colors[0].value.upper()
            elif piece.player == 1 and y == 0:
                return 1 if return_ids else self.player_colors[1].value.upper()
        return None

    def get_score(self) -> int:
        """Score from player 0's perspective: higher = better for player 0.
        Dominant term: estimated turns-to-goal advantage.
        """

        def _get_blocking_count_forward(piece: Piece) -> int:
            blocking_count = 0
            dest_y = piece.dest[1] if isinstance(piece.dest, tuple) else piece.dest
            if dest_y == piece.loc[1]:
                return 0
            step = 1 if dest_y > piece.loc[1] else -1
            x_col = piece.loc[0]
            for row in range(piece.loc[1] + step, dest_y, step):
                cell_val = self.grid[row][x_col]
                if cell_val is not None and cell_val >= 0:
                    blocking_count += 1
                elif cell_val is not None and cell_val < 0:
                    if abs(row - piece.loc[1]) <= abs(cell_val):
                        blocking_count += 1
            return blocking_count

        def _current_stride_first_turn(piece: Piece) -> int:
            """How many rows this piece can advance this turn (MoveExtended), else 1."""
            skill = self.color_skills.get_skill(piece.tile_color)
            if skill and type(skill).__name__ == 'MoveExtended':
                try:
                    intensity = self.color_skills.get_intensity(self, piece.tile_color, piece.player)
                except ValueError:
                    return 1
                value = skill.get_value(intensity)
                return max(1, int(value))
            return 1

        def _estimate_turns_to_goal(piece: Piece) -> int:
            """Estimate minimal turns to reach destination row using grid-aware BFS.
            - First turn can use MoveExtended stride in straight lines
            - Subsequent turns are 1-step orthogonal moves
            - Cells occupied by other pieces or blocked (<0) are impassable
            """
            from collections import deque

            dest_y = piece.dest[1] if isinstance(piece.dest, tuple) else piece.dest
            start_x, start_y = piece.loc
            if start_y == dest_y:
                return 0

            def cell_free(x: int, y: int) -> bool:
                val = self.grid[y][x]
                # treat this piece's own id as free (we conceptually move it)
                return val is None or val == piece.piece_id

            # Generate first-turn destinations using stride
            stride = _current_stride_first_turn(piece)
            first_moves = set()
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                blocked = False
                for step in range(1, stride + 1):
                    nx, ny = start_x + dx * step, start_y + dy * step
                    if not self.in_bound((nx, ny)):
                        break
                    if not cell_free(nx, ny):
                        blocked = True
                        break
                    first_moves.add((nx, ny))
                # if path blocked, stop extending further in this dir
                if blocked:
                    continue

            # BFS over board using 1-step moves after first move
            q = deque()
            visited = set()

            # Start positions and distance in turns
            for pos in (first_moves or {(start_x, start_y)}):
                q.append((pos[0], pos[1], 1 if pos != (start_x, start_y) else 0))
                visited.add((pos[0], pos[1]))

            while q:
                x, y, turns = q.popleft()
                if y == dest_y:
                    return turns
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if not self.in_bound((nx, ny)):
                        continue
                    if not cell_free(nx, ny):
                        continue
                    if (nx, ny) in visited:
                        continue
                    visited.add((nx, ny))
                    q.append((nx, ny, turns + 1))

            # If unreachable (shouldn't happen normally), return a large number
            return 10**6

        winner_id = self.winner(return_ids=True)
        if winner_id is not None:
            return float('inf') if winner_id == 0 else float('-inf')

        player_0_turns = [float('inf') for _ in range(len(self.pieces))]
        player_1_turns = [float('inf') for _ in range(len(self.pieces))]
        
        for piece in self.pieces:
            turns = _estimate_turns_to_goal(piece)
            
            if piece.player == 0:
                player_0_turns[piece.piece_id] = turns
            else:
                player_1_turns[piece.piece_id] = turns
        
        # Higher score means better for player 0 (fewer turns than opponent)
        us_min = min(player_0_turns)
        them_min = min(player_1_turns)
        return them_min - us_min

    def get_turns_minima(self) -> Tuple[int, int]:
        """Return (player0_min_turns, player1_min_turns) using the same BFS model as get_score."""

        def _current_stride_first_turn(piece: Piece) -> int:
            skill = self.color_skills.get_skill(piece.tile_color)
            if skill and type(skill).__name__ == 'MoveExtended':
                try:
                    intensity = self.color_skills.get_intensity(self, piece.tile_color, piece.player)
                except ValueError:
                    return 1
                value = skill.get_value(intensity)
                return max(1, int(value))
            return 1

        def _estimate_turns_to_goal(piece: Piece) -> int:
            from collections import deque
            dest_y = piece.dest[1] if isinstance(piece.dest, tuple) else piece.dest
            start_x, start_y = piece.loc
            if start_y == dest_y:
                return 0
            def cell_free(x: int, y: int) -> bool:
                val = self.grid[y][x]
                return val is None or val == piece.piece_id
            stride = _current_stride_first_turn(piece)
            first_moves = set()
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                blocked = False
                for step in range(1, stride + 1):
                    nx, ny = start_x + dx * step, start_y + dy * step
                    if not self.in_bound((nx, ny)):
                        break
                    if not cell_free(nx, ny):
                        blocked = True
                        break
                    first_moves.add((nx, ny))
                if blocked:
                    continue
            q = deque()
            visited = set()
            for pos in (first_moves or {(start_x, start_y)}):
                q.append((pos[0], pos[1], 1 if pos != (start_x, start_y) else 0))
                visited.add((pos[0], pos[1]))
            while q:
                x, y, turns = q.popleft()
                if y == dest_y:
                    return turns
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if not self.in_bound((nx, ny)):
                        continue
                    if not cell_free(nx, ny):
                        continue
                    if (nx, ny) in visited:
                        continue
                    visited.add((nx, ny))
                    q.append((nx, ny, turns + 1))
            return 10**6

        p0_turns = [float('inf') for _ in range(len(self.pieces))]
        p1_turns = [float('inf') for _ in range(len(self.pieces))]
        for piece in self.pieces:
            turns = _estimate_turns_to_goal(piece)
            if piece.player == 0:
                p0_turns[piece.piece_id] = turns
            else:
                p1_turns[piece.piece_id] = turns
        return (min(p0_turns), min(p1_turns))
        