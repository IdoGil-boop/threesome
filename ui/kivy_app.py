# ui/kivy_app.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel
from game import Board, Color as GameColor
from game.skill_base import Skill
import random
TILE = 64

COLOR_MAP = {
    GameColor.RED: (1.0, 0.7, 0.75),      # Soft rose pink
    GameColor.GREEN: (0.7, 0.95, 0.8),    # Soft mint green
    GameColor.BLUE: (0.7, 0.85, 1.0),     # Soft sky blue
    GameColor.YELLOW: (1.0, 0.98, 0.7),   # Soft cream yellow
    GameColor.PURPLE: (0.85, 0.75, 1.0),  # Soft lavender
    GameColor.ORANGE: (1.0, 0.85, 0.7),   # Soft peach
    GameColor.PINK: (1.0, 0.8, 0.9),      # Soft baby pink
    GameColor.BROWN: (0.9, 0.8, 0.7),     # Soft tan/beige
    GameColor.GRAY: (0.8, 0.8, 0.8),      # Light gray
    GameColor.BLACK: (0, 0, 0),    # Soft charcoal
    GameColor.WHITE: (0.98, 0.98, 1.0),   # Soft white
    None: (0.85, 0.85, 0.85),             # Light gray for tiles with no skill
}

# Brighter colors for text markup
TEXT_COLOR_MAP = {
    GameColor.RED: "ff3333",
    GameColor.GREEN: "33ff66",
    GameColor.BLUE: "3399ff",
    GameColor.YELLOW: "ffff33",
    GameColor.PURPLE: "cc66ff",
    GameColor.ORANGE: "ff9933",
    GameColor.PINK: "ff66cc",
    GameColor.BROWN: "cc9966",
    GameColor.GRAY: "999999",
    GameColor.BLACK: "000000",
    GameColor.WHITE: "ffffff",
}

def get_color_markup(color: GameColor) -> str:
    """Get Kivy markup color string for a game color."""
    hex_color = TEXT_COLOR_MAP.get(color, "ffffff")
    return f"[color={hex_color}]"

class BoardWidget(Widget):
    def __init__(self, status_label, skill_info_label, w_tile = 8, h_tile = 8, num_of_pieces = 3, board_config=None, **kw):
        super().__init__(**kw)
        board_config = board_config or {}
        self.w_tile = w_tile
        self.h_tile = h_tile
        self.num_of_pieces = num_of_pieces
        
        # Create board with all config options
        self.board = Board(
            w=w_tile,
            h=h_tile,
            num_of_pieces=num_of_pieces,
            color_pallete=board_config.get('color_pallete', [GameColor.RED, GameColor.GREEN, GameColor.BLUE]),
            color_proportions=board_config.get('color_proportions', None),
            player_colors=board_config.get('player_colors', (GameColor.WHITE, GameColor.BLACK)),
            force_starting_tiles=board_config.get('force_starting_tiles', GameColor.RED)
        )
        self.selected_piece = None
        self.legal_targets = []
        self.selected_opponent_piece = None  # For move_opponent skill
        self.status_label = status_label
        self.skill_info_label = skill_info_label
        self.use_skill = False
        self.showing_full_map = True
        self.preview_tiles = []  # For hover preview
        
        # Swapping skill state
        self.swapping_first_target = None
        self.swapping_awaiting_second = False
        self.swapping_awaiting_color = False
        self.swapping_color_picker_buttons = []
        self.game_screen = None  # Will be set by GameScreen
        self.bind(size=self.redraw, pos=self.redraw)
        Window.bind(mouse_pos=self.on_mouse_move)
        self.update_status()
        if self.skill_info_label:
            self.update_skill_info()
        self.redraw()

    def make_ai_move(self):
        """Make an AI move using the configured method."""
        from game import create_ai_opponent
        from kivy.clock import Clock
        
        # Don't make AI move if game is over
        if self.board.winner() is not None:
            return
        
        # Show AI thinking status
        player_color = self.board.player_colors[self.board.turn].value.upper()
        self.status_label.text = f"{player_color} AI is thinking..."
        
        # Small delay so human can see the board state
        def delayed_ai_move(dt):
            try:
                # Create AI opponent using factory function
                # Pass the board directly - AI will copy it internally during search
                ai = create_ai_opponent(
                    self.board,
                    method=self.game_screen.ai_method,
                    depth=self.game_screen.ai_depth
                )
            except Exception as e:
                print(f"Error creating AI opponent: {e}")
                import traceback
                traceback.print_exc()
                return
            
            try:
                move_result = ai.find_best_move()
            except Exception as e:
                print(f"Error finding best move: {e}")
                import traceback
                traceback.print_exc()
                return
            
            if move_result is None:
                # choose random piece of AI
                ai_pieces = [p for p in self.board.pieces if p.player == self.game_screen.ai_player]
                random.shuffle(ai_pieces)
                for ai_piece in ai_pieces:
                    legal_moves = self.board.get_legal_moves(ai_piece)
                    if legal_moves:
                        move_result = (ai_piece.piece_id, random.choice(legal_moves))
                        break
                if move_result is None:
                    self.board.turn = 1 - self.game_screen.ai_player
                    print('pass the turn')
                    return
                print("AI couldn't find a move, making random move!")
            
            try:
                print(f"\n=== AI MOVE ===")
                print(f"Current turn: {self.board.turn} (AI should be player {self.game_screen.ai_player})")
                print(f"AI move result: {move_result}")
                
                # Handle different move types
                if len(move_result) == 3:
                    # Skill move: (piece_id, target, 'skill')
                    piece_id, target, _ = move_result
                    piece = self.board.pieces[piece_id]
                    print(f"AI skill move: piece {piece_id} (player={piece.player}) -> {target}")
                    
                    # If target is (opponent_piece_id, coord), convert it to (opponent_piece, coord)
                    if isinstance(target, tuple) and len(target) == 2 and isinstance(target[0], int) and isinstance(target[1], tuple):
                        # MoveOpponent skill: target is (opponent_piece_id, (x, y))
                        opponent_piece_id, coord = target
                        opponent_piece = self.board.pieces[opponent_piece_id]
                        target = (opponent_piece, coord)
                        print(f"Converted MoveOpponent target to: ({opponent_piece.piece_id}, {coord})")
                    
                    self.board.color_skills.apply_skill(self.board, piece, target)
                elif len(move_result) == 2:
                    # Regular move: (piece_id, coord)
                    piece_id, coord = move_result
                    piece = self.board.pieces[piece_id]
                    print(f"AI regular move: piece {piece_id} (player={piece.player}) from {piece.loc} -> {coord}")
                    self.board.apply(piece, coord)
                
                print(f"Turn after AI move: {self.board.turn}\n")
                try:
                    self.board.log_board_state("after AI move")
                except Exception:
                    pass
                
                self.update_status()
                self.update_skill_info()
                self.redraw()
            except Exception as e:
                print(f"Error applying AI move: {e}")
                import traceback
                traceback.print_exc()
        
        # Schedule AI move after short delay
        Clock.schedule_once(delayed_ai_move, 0.3)
    
    def toggle_skill(self):
        self.use_skill = not self.use_skill
        if self.selected_piece:
            self.update_legal_targets()
        self.clear_swapping_state()
        self.redraw()
    
    def clear_swapping_state(self):
        """Clear swapping skill state."""
        self.swapping_first_target = None
        self.swapping_awaiting_second = False
        self.swapping_awaiting_color = False
        self.remove_swapping_color_picker()
    
    def remove_swapping_color_picker(self):
        """Remove color picker buttons if they exist."""
        if self.game_screen:
            for widget in self.swapping_color_picker_buttons:
                if widget.parent:
                    widget.parent.remove_widget(widget)
        self.swapping_color_picker_buttons = []
    
    def show_swapping_color_picker(self, target):
        """Show color picker popup for swapping skill intensity 2."""
        if not self.game_screen:
            print("Warning: game_screen not set, cannot show color picker")
            return
            
        self.remove_swapping_color_picker()
        self.swapping_awaiting_color = True
        self.swapping_first_target = target  # Store for highlighting
        
        # Calculate dynamic tile size
        if self.width > 0 and self.height > 0:
            tile_size = min(self.width / self.board.w, self.height / self.board.h)
        else:
            tile_size = TILE
        
        # Calculate position relative to board widget - place menu away from target tile
        target_x, target_y = target
        target_pixel_x = target_x * tile_size
        target_pixel_y = target_y * tile_size
        
        # Decide placement: if target is on left half, place menu on right; otherwise left
        menu_width = 120
        menu_height = len(self.board.color_pallete) * 50 + 20
        
        if target_pixel_x < self.width / 2:
            # Target on left, place menu on right
            menu_x = target_pixel_x + tile_size + 10
        else:
            # Target on right, place menu on left
            menu_x = target_pixel_x - menu_width - 10
        
        # Clamp to board widget bounds
        menu_x = max(5, min(menu_x, self.width - menu_width - 5))
        menu_y = max(5, min(target_pixel_y, self.height - menu_height - 5))
        
        # Use absolute screen coordinates
        popup_x = self.x + menu_x
        popup_y = self.y + menu_y
        
        # Create container to hold background and buttons
        popup_layout = BoxLayout(
            orientation='vertical',
            size_hint=(None, None), 
            size=(menu_width, menu_height), 
            pos=(popup_x, popup_y),
            padding=10,
            spacing=5
        )
        
        # Draw background rectangle
        with popup_layout.canvas.before:
            Color(0.2, 0.2, 0.2, 0.95)
            popup_bg = Rectangle(pos=popup_layout.pos, size=popup_layout.size)
        
        # Update background position/size when layout changes
        def update_bg(instance, value):
            popup_bg.pos = instance.pos
            popup_bg.size = instance.size
        popup_layout.bind(pos=update_bg, size=update_bg)
        
        # Create buttons for each color in palette
        for i, game_color in enumerate(self.board.color_pallete):
            btn = Button(
                text=game_color.value.capitalize(),
                size_hint=(1, None),
                height=40
            )
            btn.bind(on_press=lambda instance, gc=game_color, tgt=target: self.apply_swapping_with_color(gc, tgt))
            popup_layout.add_widget(btn)
        
        # Add to the root GameScreen widget as an overlay
        self.game_screen.add_widget(popup_layout)
        self.swapping_color_picker_buttons.append(popup_layout)
        
        self.update_status()
        self.redraw()
    
    def apply_swapping_with_color(self, chosen_color, target):
        """Apply swapping skill with chosen color (intensity 2)."""
        try:
            skill = self.board.color_skills.get_skill(self.selected_piece.tile_color)
            intensity = Skill.get_intensity(self.board, self.selected_piece.tile_color, self.selected_piece.player)
            
            # Consume tiles that contributed to the skill
            self.board.consume_tiles(self.selected_piece.tile_color, self.selected_piece.player)
            
            # Apply with color parameter
            skill.apply(self.board, self.selected_piece, target, intensity, color=chosen_color)
            
            self.selected_piece = None
            self.selected_opponent_piece = None
            self.legal_targets = []
            self.preview_tiles = []
            self.clear_swapping_state()
            self.update_status()
            self.update_skill_info()
            self.redraw()
        except (ValueError, AttributeError) as e:
            print(f"Error applying swapping skill: {e}")
            self.clear_swapping_state()

    def update_status(self):
        winner = self.board.winner()
        if winner is not None:
            self.status_label.text = f"{winner} player WINS! 🎉"
        elif self.swapping_awaiting_second:
            self.status_label.text = "Select second tile to swap"
        elif self.swapping_awaiting_color:
            self.status_label.text = "Choose a color from the buttons"
        else:
            skill_text = " [SKILL MODE]" if self.use_skill else ""
            player_color = self.board.player_colors[self.board.turn].value.upper()
            self.status_label.text = f"{player_color}'s turn{skill_text}"
    
    def update_skill_info(self):
        """Update the skill info label with current piece info."""
        if not self.skill_info_label:
            return
            
        # If showing full map, refresh it with new piece info
        if self.showing_full_map:
            self.refresh_full_map()
            return
        
        if not self.selected_piece:
            self.skill_info_label.text = "Select a piece to see its skill info"
            return
        
        piece = self.selected_piece
        if piece.tile_color is None:
            self.skill_info_label.text = "GRAY - No skill available"
            return
        
        # Calculate intensity
        try:
            intensity = Skill.get_intensity(self.board, piece.tile_color, piece.player)
            skill_info = self.board.color_skills.get_skill_info(piece.tile_color, intensity)
            
            color_markup = get_color_markup(piece.tile_color)
            color_name = piece.tile_color.value.upper()
            self.skill_info_label.text = (
                f"{color_markup}{color_name}[/color] - {skill_info['name']} (Intensity {intensity}): {color_markup}{skill_info['description']}[/color]"
            )
        except ValueError:
            color_markup = get_color_markup(piece.tile_color)
            color_name = piece.tile_color.value.upper()
            self.skill_info_label.text = f"{color_markup}{color_name}[/color] - No pieces with this color"
    
    def refresh_full_map(self):
        """Refresh the full skill map display with updated piece info."""
        if not self.skill_info_label:
            return
            
        skill_map = self.board.color_skills.get_color_skill_map()
        lines = []
        
        # Show current piece info first if there's a selected piece
        if self.selected_piece and self.selected_piece.tile_color is not None:
            piece = self.selected_piece
            try:
                intensity = Skill.get_intensity(self.board, piece.tile_color, piece.player)
                skill_info = self.board.color_skills.get_skill_info(piece.tile_color, intensity)
                color_markup = get_color_markup(piece.tile_color)
                color_name = piece.tile_color.value.upper()
                lines.append(f"[b]>>> CURRENT: {color_markup}{color_name}[/color] - {skill_info['name']} (Intensity {intensity}): {skill_info['description']} <<<[/b]")
                lines.append("")
            except ValueError:
                pass
        
        lines.append("[b]=== All Color Skills ===[/b]")
        
        for color, skill_name in skill_map.items():
            color_markup = get_color_markup(color)
            color_name = color.value.upper()
            lines.append(f"\n[b]{color_markup}{color_name}[/color] - {skill_name}:[/b]")
            for intensity in [1, 2, 3]:
                info = self.board.color_skills.get_skill_info(color, intensity)
                lines.append(f"  {color_markup}{intensity}x: {info['description']}[/color]")
        
        self.skill_info_label.text = "\n".join(lines)

    def get_piece_at(self, x, y):
        """Get piece at grid coordinates."""
        if not self.board.in_bound((x, y)):
            return None
        piece_id = self.board.grid[y][x]
        if piece_id is not None and piece_id >= 0:
            return self.board.pieces[piece_id]
        return None

    def update_legal_targets(self):
        """Update legal targets for selected piece."""
        if not self.selected_piece:
            self.legal_targets = []
            return
        
        if self.use_skill:
            try:
                self.legal_targets = self.board.color_skills.get_legal_targets(self.board, self.selected_piece)
            except ValueError as e:
                # Invalid intensity (0 or >3 pieces with same color)
                self.legal_targets = []
        else:
            self.legal_targets = self.board.piece_legal_moves(self.selected_piece)

    def on_mouse_move(self, window, pos):
        """Handle hover preview for skills."""
        mouse_x, mouse_y = pos
        
        if not self.collide_point(mouse_x, mouse_y):
            if self.preview_tiles:
                self.preview_tiles = []
                self.redraw()
            return
        
        # Only show preview if in skill mode with a piece selected
        if not self.use_skill or not self.selected_piece:
            if self.preview_tiles:
                self.preview_tiles = []
                self.redraw()
            return
        
        # Calculate hovered tile
        if self.width > 0 and self.height > 0:
            tile_size = min(self.width / self.board.w, self.height / self.board.h)
        else:
            tile_size = TILE
        
        x = int((mouse_x - self.x) // tile_size)
        y = int((mouse_y - self.y) // tile_size)
        
        if not self.board.in_bound((x, y)):
            if self.preview_tiles:
                self.preview_tiles = []
                self.redraw()
            return
        
        # Get preview tiles if this is BlockingWall skill
        target = (x, y)
        if target in self.legal_targets:
            try:
                skill = self.board.color_skills.get_skill(self.selected_piece.tile_color)
                if hasattr(skill, 'get_affected_tiles'):
                    intensity = Skill.get_intensity(self.board, self.selected_piece.tile_color, self.selected_piece.player)
                    new_preview = skill.get_affected_tiles(self.board, target, intensity)
                    if new_preview != self.preview_tiles:
                        self.preview_tiles = new_preview
                        self.redraw()
                else:
                    if self.preview_tiles:
                        self.preview_tiles = []
                        self.redraw()
            except (ValueError, AttributeError):
                if self.preview_tiles:
                    self.preview_tiles = []
                    self.redraw()
        else:
            if self.preview_tiles:
                self.preview_tiles = []
                self.redraw()
    
    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        
        winner = self.board.winner()
        if winner is not None:
            return True
        
        # Calculate dynamic tile size for click detection
        if self.width > 0 and self.height > 0:
            tile_size = min(self.width / self.board.w, self.height / self.board.h)
        else:
            tile_size = TILE
        
        x = int((touch.x - self.x) // tile_size)
        y = int((touch.y - self.y) // tile_size)
        
        if not self.board.in_bound((x, y)):
            return True

        # If no piece selected, try to select one
        if self.selected_piece is None:
            piece = self.get_piece_at(x, y)
            if piece and piece.player == self.board.turn:
                self.selected_piece = piece
                self.update_legal_targets()
                self.update_skill_info()
                self.redraw()
        else:
            # Try to move to clicked position
            target = (x, y)
            moved = False
            
            # Check if clicking same piece (deselect)
            if self.selected_piece.loc == target:
                self.selected_piece = None
                self.selected_opponent_piece = None
                self.legal_targets = []
                self.preview_tiles = []
                self.clear_swapping_state()
                self.update_skill_info()
                self.redraw()
                return True
            
            # Check if clicking on another owned piece (switch selection)
            clicked_piece = self.get_piece_at(x, y)
            if clicked_piece and clicked_piece.player == self.board.turn:
                self.selected_piece = clicked_piece
                self.selected_opponent_piece = None
                self.clear_swapping_state()
                self.update_legal_targets()
                self.update_skill_info()
                self.redraw()
                return True
            
            # Check if clicking on opponent piece for move_opponent skill
            if self.use_skill and clicked_piece and clicked_piece.player != self.board.turn:
                # Check if this is a move_opponent skill
                if isinstance(self.legal_targets, list) and len(self.legal_targets) > 0:
                    if isinstance(self.legal_targets[0], tuple) and len(self.legal_targets[0]) == 2:
                        if hasattr(self.legal_targets[0][0], 'piece_id'):
                            # This is move_opponent skill
                            valid_pieces = [p for p, _ in self.legal_targets]
                            if clicked_piece in valid_pieces:
                                self.selected_opponent_piece = clicked_piece
                                self.redraw()
                                return True
            
            # Handle swapping skill second target selection (intensity 3)
            if self.swapping_awaiting_second and target in self.legal_targets:
                try:
                    skill = self.board.color_skills.get_skill(self.selected_piece.tile_color)
                    intensity = Skill.get_intensity(self.board, self.selected_piece.tile_color, self.selected_piece.player)
                    
                    # Consume tiles
                    self.board.consume_tiles(self.selected_piece.tile_color, self.selected_piece.player)
                    
                    # Apply with both targets
                    skill.apply(self.board, self.selected_piece, self.swapping_first_target, intensity, target_b=target)
                    
                    moved = True
                    self.selected_piece = None
                    self.selected_opponent_piece = None
                    self.legal_targets = []
                    self.preview_tiles = []
                    self.clear_swapping_state()
                    self.update_status()
                    self.update_skill_info()
                    self.redraw()
                    return True
                except (ValueError, AttributeError) as e:
                    print(f"Error applying swapping skill intensity 3: {e}")
                    self.clear_swapping_state()
            
            # Check if target is legal
            if self.use_skill:
                # Handle different skill return types
                if isinstance(self.legal_targets, list) and len(self.legal_targets) > 0:
                    if isinstance(self.legal_targets[0], tuple) and len(self.legal_targets[0]) == 2:
                        # Could be (Piece, Coord) or just Coord
                        if hasattr(self.legal_targets[0][0], 'piece_id'):
                            # move_opponent skill: List[Tuple[Piece, Coord]]
                            # We have an opponent piece selected, now pick destination
                            if self.selected_opponent_piece:
                                for opp_piece, dest in self.legal_targets:
                                    if opp_piece == self.selected_opponent_piece and dest == target:
                                        try:
                                            self.board.color_skills.apply_skill(self.board, self.selected_piece, (opp_piece, dest))
                                            moved = True
                                        except ValueError:
                                            pass
                                        break
                        else:
                            # Regular coord tuple
                            if target in self.legal_targets:
                                try:
                                    # Check for swapping skill special handling
                                    skill = self.board.color_skills.get_skill(self.selected_piece.tile_color)
                                    intensity = Skill.get_intensity(self.board, self.selected_piece.tile_color, self.selected_piece.player)
                                    if skill and skill.skill_type == 'swapping':
                                        if intensity == 1:
                                            # Random color, just apply normally
                                            self.board.color_skills.apply_skill(self.board, self.selected_piece, target)
                                            moved = True
                                        elif intensity == 2:
                                            # Show color picker
                                            self.show_swapping_color_picker(target)
                                            return True
                                        elif intensity == 3:
                                            # Save first target, wait for second
                                            self.swapping_first_target = target
                                            self.swapping_awaiting_second = True
                                            self.update_status()
                                            return True
                                    else:
                                        self.board.color_skills.apply_skill(self.board, self.selected_piece, target)
                                        moved = True
                                except ValueError:
                                    pass
                    else:
                        # Simple Coord list
                        if target in self.legal_targets:
                            try:
                                # Check for swapping skill special handling
                                skill = self.board.color_skills.get_skill(self.selected_piece.tile_color)
                                intensity = Skill.get_intensity(self.board, self.selected_piece.tile_color, self.selected_piece.player)
                                if skill and skill.skill_type == 'swapping':
                                    if intensity == 1:
                                        # Random color, just apply normally
                                        self.board.color_skills.apply_skill(self.board, self.selected_piece, target)
                                        moved = True
                                    elif intensity == 2:
                                        # Show color picker
                                        self.show_swapping_color_picker(target)
                                        return True
                                    elif intensity == 3:
                                        # Save first target, wait for second
                                        self.swapping_first_target = target
                                        self.swapping_awaiting_second = True
                                        self.update_status()
                                        return True
                                else:
                                    self.board.color_skills.apply_skill(self.board, self.selected_piece, target)
                                    moved = True
                            except ValueError:
                                pass
            else:
                # Normal move
                if target in self.legal_targets:
                    self.board.apply(self.selected_piece, target)
                    moved = True
            
            if moved:
                # Log user's move
                try:
                    last = self.board.move_history[-1] if self.board.move_history else None
                    print("=== USER MOVE ===")
                    if last and last[0] == 'move':
                        kind, pid, frm, to = last
                        piece = self.board.pieces[pid]
                        print(f"User moved piece {pid} (player={piece.player}) from {frm} -> {to}")
                    else:
                        print("User used a skill or non-move action")
                    self.board.log_board_state("after user move")
                except Exception:
                    pass
                # self.showing_full_map = False  # Reset after move
                self.selected_piece = None
                self.selected_opponent_piece = None
                self.legal_targets = []
                self.preview_tiles = []
                # Auto-disable skill mode on turn switch
                if self.use_skill:
                    self.use_skill = False
                    if self.game_screen:
                        self.game_screen.skill_btn.background_color = (1, 1, 1, 1)
                self.update_status()
                self.update_skill_info()
                
                # Check if AI should move next
                if self.game_screen and self.game_screen.ai_enabled:
                    if self.board.turn == self.game_screen.ai_player and self.board.winner() is None:
                        self.make_ai_move()
            
            self.redraw()
        
        return True

    def redraw(self, *args):
        self.canvas.clear()
        
        # Calculate dynamic tile size based on available widget space
        if self.width > 0 and self.height > 0:
            tile_size = min(self.width / self.board.w, self.height / self.board.h)
        else:
            tile_size = TILE
        
        with self.canvas:
            # Draw color grid
            for j in range(self.board.h):
                for i in range(self.board.w):
                    grid_color = self.board.color_grid[j][i]
                    rgb = COLOR_MAP.get(grid_color, (0.5, 0.5, 0.5))
                    Color(*rgb, 0.4)
                    Rectangle(pos=(self.x + i*tile_size, self.y + j*tile_size), size=(tile_size, tile_size))
                    
                    # Draw grid lines
                    Color(0.7, 0.7, 0.75, 0.3)
                    Line(rectangle=(self.x + i*tile_size, self.y + j*tile_size, tile_size, tile_size), width=1)
                    
                    # Draw blocked tiles
                    cell_val = self.board.grid[j][i]
                    if cell_val is not None and cell_val < 0:
                        Color(0.5, 0.5, 0.55, 0.6)
                        Rectangle(pos=(self.x + i*tile_size, self.y + j*tile_size), size=(tile_size, tile_size))
                        Color(1.0, 0.6, 0.65, 0.9)
                        Line(rectangle=(self.x + i*tile_size + 5, self.y + j*tile_size + 5, tile_size - 10, tile_size - 10), width=3)
                        
                        # Draw countdown number
                        rounds_remaining = abs(cell_val) // 2
                        label = CoreLabel(text=str(rounds_remaining), font_size=int(tile_size * 0.5))
                        label.refresh()
                        text_texture = label.texture
                        Color(1.0, 0.2, 0.3, 1.0)  # Bright red text
                        Rectangle(
                            pos=(self.x + i*tile_size + (tile_size - text_texture.size[0]) / 2, 
                                 self.y + j*tile_size + (tile_size - text_texture.size[1]) / 2),
                            size=text_texture.size,
                            texture=text_texture
                        )
            
            # Draw preview tiles (for skills with affected area)
            for px, py in self.preview_tiles:
                Color(1.0, 0.85, 0.6, 0.5)
                Rectangle(pos=(self.x + px*tile_size, self.y + py*tile_size), size=(tile_size, tile_size))
                Color(1.0, 0.8, 0.5, 0.8)
                Line(rectangle=(self.x + px*tile_size + 2, self.y + py*tile_size + 2, tile_size - 4, tile_size - 4), width=2)
            
            # Highlight legal targets (skip for blocking and swapping skills - they only show on hover)
            should_show_frames = True
            if self.use_skill and self.selected_piece and self.selected_piece.tile_color:
                skill = self.board.color_skills.get_skill(self.selected_piece.tile_color)
                if skill and (skill.skill_type == 'blocking' or skill.skill_type == 'swapping'):
                    should_show_frames = False
            
            if should_show_frames:
                for target in self.legal_targets:
                    if isinstance(target, tuple):
                        if hasattr(target[0], 'piece_id'):
                            # move_opponent: (Piece, Coord)
                            opp_piece, dest = target
                            # If no opponent piece selected, highlight all selectable opponent pieces
                            if self.selected_opponent_piece is None:
                                # Highlight the opponent piece location in soft cyan
                                ox, oy = opp_piece.loc
                                Color(0.7, 0.95, 0.95, 0.9)
                                Line(rectangle=(self.x + ox*tile_size + 2, self.y + oy*tile_size + 2, tile_size - 4, tile_size - 4), width=3)
                            # If opponent piece is selected, only show destinations for that piece
                            elif opp_piece == self.selected_opponent_piece:
                                tx, ty = dest
                                Color(0.7, 1.0, 0.8, 0.9)
                                Line(rectangle=(self.x + tx*tile_size + 2, self.y + ty*tile_size + 2, tile_size - 4, tile_size - 4), width=3)
                        else:
                            # Regular coord
                            tx, ty = target
                            Color(0.7, 1.0, 0.8, 0.9)
                            Line(rectangle=(self.x + tx*tile_size + 2, self.y + ty*tile_size + 2, tile_size - 4, tile_size - 4), width=3)
                    else:
                        # Simple coord
                        tx, ty = target
                        Color(0.7, 1.0, 0.8, 0.9)
                        Line(rectangle=(self.x + tx*tile_size + 2, self.y + ty*tile_size + 2, tile_size - 4, tile_size - 4), width=3)
            
            # Highlight selected opponent piece (if any)
            if self.selected_opponent_piece:
                ox, oy = self.selected_opponent_piece.loc
                Color(1.0, 0.75, 0.95, 0.7)
                Line(rectangle=(self.x + ox*tile_size + 2, self.y + oy*tile_size + 2, tile_size - 4, tile_size - 4), width=4)
            
            # Highlight selected piece
            if self.selected_piece:
                sx, sy = self.selected_piece.loc
                Color(1.0, 0.95, 0.6, 0.7)
                Line(rectangle=(self.x + sx*tile_size + 2, self.y + sy*tile_size + 2, tile_size - 4, tile_size - 4), width=4)
            
            # Highlight first swapping target when awaiting second OR color choice
            if (self.swapping_awaiting_second or self.swapping_awaiting_color) and self.swapping_first_target:
                fx, fy = self.swapping_first_target
                Color(0.5, 1.0, 0.5, 0.8)  # Bright green
                Line(rectangle=(self.x + fx*tile_size + 4, self.y + fy*tile_size + 4, tile_size - 8, tile_size - 8), width=3)
            
            # Draw pieces (color indicates player now)
            for piece in self.board.pieces:
                px, py = piece.loc
                piece_rgb = COLOR_MAP.get(piece.color, (0.7, 0.7, 0.7))
                
                # Draw piece circle
                Color(*piece_rgb, 1.0)
                Ellipse(pos=(self.x + px*tile_size + tile_size*0.125, self.y + py*tile_size + tile_size*0.125), 
                       size=(tile_size*0.75, tile_size*0.75))
                
                # In skill mode, add gold frame for pieces participating in the skill
                if self.use_skill and self.selected_piece and piece.player == self.board.turn:
                    if piece.tile_color and self.selected_piece.tile_color == piece.tile_color:
                        Color(1.0, 0.84, 0.0, 1.0)  # Gold frame
                        Line(circle=(self.x + px*tile_size + tile_size*0.5, self.y + py*tile_size + tile_size*0.5, tile_size*0.375), width=2.5)


class GameScreen(BoxLayout):
    def __init__(self, board_config=None, ai_enabled=False, ai_method='minimax', ai_player=1, ai_depth=3, **kwargs):
        board_config = board_config or {}
        self.board_config = board_config  # Store for reset
        self.ai_enabled = ai_enabled
        self.ai_method = ai_method
        self.ai_player = ai_player
        self.ai_depth = ai_depth
        super().__init__(orientation='vertical', **kwargs)
        
        # Status label at top
        self.status_label = Label(text="", size_hint=(1, 0.08), font_size='20sp')
        self.add_widget(self.status_label)
        
        # Horizontal layout for board and skill info
        main_area = BoxLayout(orientation='horizontal', size_hint=(1, 0.80))
        
        # Board on the left
        self.board_widget = BoardWidget(
            self.status_label, 
            None, 
            size_hint=(0.65, 1), 
            w_tile=board_config.get('w', 8),
            h_tile=board_config.get('h', 8),
            num_of_pieces=board_config.get('num_of_pieces', 3),
            board_config=board_config
        )
        main_area.add_widget(self.board_widget)
        
        # Skill info label in scrollview on the right
        scroll_view = ScrollView(size_hint=(0.35, 1), do_scroll_x=False, do_scroll_y=True)
        self.skill_info_label = Label(
            text="", 
            size_hint_y=None, 
            font_size='16sp', 
            halign='left', 
            valign='top',
            markup=True,
            padding=(10, 10)
        )
        self.skill_info_label.bind(texture_size=self.skill_info_label.setter('size'))
        self.skill_info_label.bind(width=lambda *x: self.skill_info_label.setter('text_size')(self.skill_info_label, (self.skill_info_label.width - 20, None)))
        scroll_view.add_widget(self.skill_info_label)
        main_area.add_widget(scroll_view)
        
        self.add_widget(main_area)
        
        # Now set the skill_info_label reference in board_widget and update it
        self.board_widget.skill_info_label = self.skill_info_label
        # Set reference to main window for popups
        self.board_widget.game_screen = self
        self.board_widget.update_skill_info()
        
        # Controls at bottom
        controls = BoxLayout(size_hint=(1, 0.12), spacing=10, padding=10)
        
        self.skill_btn = Button(text="Toggle Skill Mode", on_press=lambda x: self.toggle_skill())
        controls.add_widget(self.skill_btn)
        
        reset_btn = Button(text="New Game", on_press=lambda x: self.reset_game())
        controls.add_widget(reset_btn)
        
        self.ai_btn = Button(text=f"AI: {'ON' if self.ai_enabled else 'OFF'}", on_press=lambda x: self.toggle_ai())
        self.ai_btn.background_color = (0.95, 0.7, 0.7, 1) if self.ai_enabled else (1, 1, 1, 1)
        controls.add_widget(self.ai_btn)
        
        self.info_btn = Button(text="Show Color Skills", disabled=False if self.board_widget.showing_full_map else True, on_press=lambda x: self.show_skill_map())
        self.info_btn.background_color = (0.7, 0.95, 0.8, 1) if self.board_widget.showing_full_map else (1, 1, 1, 1)
        controls.add_widget(self.info_btn)
        
        self.add_widget(controls)
        
        # Start with AI move if AI goes first
        if self.ai_enabled and self.board_widget.board.turn == self.ai_player:
            self.board_widget.make_ai_move()
    
    def toggle_skill(self):
        self.board_widget.toggle_skill()
        self.board_widget.update_status()
        self.skill_btn.background_color = (0.7, 0.95, 0.8, 1) if self.board_widget.use_skill else (1, 1, 1, 1)
    
    def toggle_ai(self):
        """Toggle AI opponent on/off."""
        self.ai_enabled = not self.ai_enabled
        self.ai_btn.text = f"AI: {'ON' if self.ai_enabled else 'OFF'}"
        self.ai_btn.background_color = (0.95, 0.7, 0.7, 1) if self.ai_enabled else (1, 1, 1, 1)
        
        # If we just enabled AI and it's AI's turn, make a move
        if self.ai_enabled and self.board_widget.board.turn == self.ai_player:
            if self.board_widget.board.winner() is None:
                self.board_widget.make_ai_move()
    
    def show_skill_map(self):
        """Toggle the complete color-to-skill mapping display."""
        self.board_widget.showing_full_map = not self.board_widget.showing_full_map
        # Update the button's background color
        self.info_btn.background_color = (0.7, 0.95, 0.8, 1) if self.board_widget.showing_full_map else (1, 1, 1, 1)
        if self.board_widget.showing_full_map:
            self.board_widget.refresh_full_map()
        else:
            self.board_widget.update_skill_info()
    
    def reset_game(self):
        # Create new board with same config
        self.board_widget.board = Board(
            w=self.board_config.get('w', 8),
            h=self.board_config.get('h', 8),
            num_of_pieces=self.board_config.get('num_of_pieces', 3),
            color_pallete=self.board_config.get('color_pallete', [GameColor.RED, GameColor.GREEN, GameColor.BLUE]),
            color_proportions=self.board_config.get('color_proportions', None),
            player_colors=self.board_config.get('player_colors', (GameColor.WHITE, GameColor.BLACK)),
            force_starting_tiles=self.board_config.get('force_starting_tiles', GameColor.RED)
        )
        self.board_widget.selected_piece = None
        self.board_widget.selected_opponent_piece = None
        self.board_widget.legal_targets = []
        self.board_widget.preview_tiles = []
        self.board_widget.use_skill = False
        self.board_widget.showing_full_map = True
        self.board_widget.clear_swapping_state()
        self.skill_btn.background_color = (1, 1, 1, 1)
        self.info_btn.background_color = (1, 1, 1, 1)
        self.board_widget.update_status()
        self.board_widget.update_skill_info()
        self.board_widget.redraw()
        
        # If AI enabled and it's AI's turn, make first move
        if self.ai_enabled and self.board_widget.board.turn == self.ai_player:
            self.board_widget.make_ai_move()


class ThreesomeApp(App):
    def __init__(self, board_config=None, ai_enabled=False, ai_method='minimax', ai_player=1, ai_depth=3, **kwargs):
        super().__init__(**kwargs)
        self.board_config = board_config or {}
        self.ai_enabled = ai_enabled
        self.ai_method = ai_method
        self.ai_player = ai_player
        self.ai_depth = ai_depth
    
    def build(self):
        # Width: board area + info panel, Height: board + status + controls
        Window.size = (900, 700)
        return GameScreen(
            board_config=self.board_config,
            ai_enabled=self.ai_enabled,
            ai_method=self.ai_method,
            ai_player=self.ai_player,
            ai_depth=self.ai_depth
        )


if __name__ == "__main__":
    ThreesomeApp().run()
