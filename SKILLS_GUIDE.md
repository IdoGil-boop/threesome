# Skills Guide

## Color Skill System

Each game randomly assigns one of three skills to each color on the board. The skill's power scales with **intensity** (how many of your pieces share that color).

### Three Skills Available

#### 1. Move Extended
- **Effect**: Move up to (intensity + 1) squares in one cardinal direction
- **Intensity Scale**:
  - 1 piece: Move 2 squares
  - 2 pieces: Move 3 squares
  - 3 pieces: Move 4 squares
- **Best for**: Quick advancement across the board

#### 2. Move Opponent
- **Effect**: Force an opponent's piece to move (intensity + 1) / 2 squares
- **Intensity Scale**:
  - 1 piece: Move opponent 1 square
  - 2 pieces: Move opponent 1 square
  - 3 pieces: Move opponent 2 squares
- **Best for**: Tactical disruption and blocking opponent's path

#### 3. Block Tile
- **Effect**: Place a blocking marker on any empty tile for X turns
- **Intensity Scale**:
  - 1 piece: Block for 1 turn
  - 2 pieces: Block for 2 turns
  - 3 pieces: Block for 3 turns
- **Best for**: Area denial and controlling opponent movement

## How to Use Skills in Game

1. **Check Color Assignment**: Click "Show Color Skills" to see which color has which skill
2. **Build Intensity**: Move your pieces onto tiles of the same color to increase intensity
3. **Activate Skill Mode**: Click "Toggle Skill Mode" (button turns green)
4. **Select Piece**: Click one of your pieces
5. **View Available Options**: The info bar shows your piece's current skill and intensity
6. **Execute**: Click a green highlighted square to use the skill

## Strategy Tips

### Building Intensity
- Early game: Focus on getting 2-3 pieces the same color for maximum power
- Color management: Plan your moves to land on strategically useful colors
- Balance: Sometimes a weak skill at high intensity beats a strong skill at low intensity

### Skill Combos
- **Move Extended + Block**: Rush forward then block the path behind you
- **Move Opponent + Block**: Push opponent piece into a corner, then block their escape
- **Multiple Extended Moves**: Chain several extended moves to reach the goal quickly

### When to Use Skills vs Normal Moves
- **Normal moves** don't advance your turn counter (faster)
- **Skills** are more powerful but cost a turn
- Use skills when:
  - You need the extra range
  - You can disrupt opponent significantly
  - You need to control key board positions

## API for Developers

```python
from game import Board, ColorSkills

# Create board and skill system
board = Board(8, 8, num_of_pieces=3)
color_skills = ColorSkills([c.value for c in board.color_pallete])

# Get skill mapping
skill_map = color_skills.get_color_skill_map()
# Returns: {Color.RED: 'Move Extended', Color.BLUE: 'Block Tile', ...}

# Get skill info for a specific color and intensity
info = color_skills.get_skill_info(Color.RED, intensity=2)
# Returns: {
#     'name': 'Move Extended',
#     'type': 'moving',
#     'description': 'Move up to 3 squares in one direction',
#     'value': 3
# }

# Get legal targets for a piece using its skill
targets = color_skills.get_legal_targets(board, piece)
# Returns: List[Coord] or List[Tuple[Piece, Coord]] depending on skill

# Apply a skill
color_skills.apply_skill(board, piece, target)
```

## UI Elements

- **Status Bar**: Shows current player and mode (normal/skill)
- **Info Bar**: Shows selected piece's color, skill, intensity, and description
- **Yellow Border**: Your selected piece
- **Green Highlights**: Legal moves/targets
- **Red X on Dark Square**: Blocked tile (shows countdown)
- **Piece Borders**: White = Player 0, Black = Player 1
- **Piece Fill**: Current color of the piece

## Troubleshooting

**Q: Skill mode crashed the game**
A: Fixed! The game now handles all color-skill mappings correctly.

**Q: How do I know what intensity I have?**
A: Select a piece - the info bar shows your current intensity.

**Q: Can I see all skills at once?**
A: Click "Show Color Skills" to see the mapping and an example intensity scale.

**Q: The skill didn't work**
A: Make sure:
  - Skill mode is ON (green button)
  - You selected one of YOUR pieces
  - You clicked a green highlighted square
  - Your piece has a color (pieces start with no color until they move)

