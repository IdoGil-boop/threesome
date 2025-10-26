# Threesome - Strategic Board Game

A two-player strategic board game where you race pieces across a colored grid, collecting colors to unlock powerful skills.

## How to Play

### Objective
Be the first player to get one of your pieces to the opponent's starting row:
- **Player 0** (white border): Start at bottom (y=0), win by reaching top (y=7)
- **Player 1** (black border): Start at top (y=7), win by reaching bottom (y=0)

### Basic Rules

1. **Turn-based**: Players alternate turns
2. **Movement**: Click a piece to select it, then click a highlighted square to move
3. **Legal Moves**: Pieces can move 1 square in any cardinal direction (up, down, left, right)
4. **Colors**: When a piece moves, it takes on the color of the tile it lands on

### Color Skills

Each color in the game grants a unique skill based on **intensity** (number of your pieces with that color):

**Three Skills Available:**
- **Move Extended (moveX)**: Move 2-4 squares instead of 1 (based on intensity+1)
- **Move Opponent**: Force an opponent's piece to move (intensity+1)/2 squares
- **Block**: Place a blocking tile on the board for X turns (X = intensity)

Skills are automatically assigned to colors at the start of each game.

### Skill Mode

- Click **"Toggle Skill Mode"** to activate skills
- When skill mode is ON:
  - Your piece's color determines which skill you can use
  - Green highlights show where you can apply the skill
  - The skill uses intensity based on how many of your pieces share that color
- When skill mode is OFF:
  - Normal 1-square movement only

### UI Elements

- **Color Grid**: Background shows the color of each tile
- **Pieces**: Circles with colored fill (current color) and border (player)
  - White border = Player 0
  - Black border = Player 1
- **Yellow Highlight**: Your selected piece
- **Green Highlight**: Legal moves/targets
- **Red X**: Blocked tiles (countdown shown as negative values)

## Running the Game

```bash
# Activate virtual environment
source venv/bin/activate

# Run the game
python3 main.py

# Or run directly
python3 ui/kivy_app.py
```

## Custom Board Builder

Create custom board configurations with different sizes, colors, and proportions!

### Quick Start

**Visual GUI Builder:**
```bash
cd board_builder
python3 visual_builder.py
```

**CLI Interactive Mode:**
```bash
cd board_builder
python3 builder.py -i
```

**Python Code:**
```python
from board_builder import BoardBuilder
from game import Color

config = (BoardBuilder()
    .set_size(10, 10)
    .set_pieces(4)
    .set_colors(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW)
    .set_proportions(RED=0.3, GREEN=0.3, BLUE=0.2, YELLOW=0.1)
    # Gray (NONE) = 0.1 automatically calculated
    .force_starting_color(Color.RED)
    .build()
)

# Launch custom game
from ui.kivy_app import ThreesomeApp
ThreesomeApp(config).run()
```

See **[board_builder/README.md](board_builder/README.md)** for complete documentation.

## Controls

- **Left Click**: Select piece / Make move
- **Toggle Skill Mode Button**: Switch between normal and skill moves
- **New Game Button**: Reset the board

## Strategy Tips

1. **Color Management**: Try to get multiple pieces the same color for stronger skills
2. **Block Opponent**: Use blocking skills to slow down opponent's pieces
3. **Race vs Control**: Balance between rushing to the goal and controlling the board
4. **Skill Timing**: Normal moves are faster, but skills can be game-changing

## Development

Run tests:
```bash
source venv/bin/activate
PYTHONPATH=/Users/idogil/threesome pytest tests/test_rules.py -v
```

## Project Structure

```
threesome/
├── game/             # Core game logic
│   ├── board.py
│   ├── entities.py
│   ├── skills.py
│   └── skill_types.py
├── ui/               # User interface
│   ├── kivy_app.py
│   └── widgets.kv
├── board_builder/    # Custom board configuration tools
│   ├── builder.py    # Programmatic & CLI builder
│   ├── visual_builder.py # GUI builder
│   ├── examples.py   # Usage examples
│   ├── saved_configs/ # Saved board configurations
│   └── README.md     # Full documentation
├── tests/
│   └── test_rules.py
└── main.py           # Game launcher
```

Enjoy playing Threesome! 🎮

