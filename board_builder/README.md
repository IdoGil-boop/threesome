# Board Builder Guide

Create custom board configurations for Threesome using simple Python code, CLI, or a visual GUI.

## Quick Start

### Method 1: Visual GUI Builder (Easiest)

```bash
cd board_builder
python3 visual_builder.py
```

Use the GUI to:
- Set board dimensions
- Choose number of pieces
- Select number of colors (dropdown: 1-9, auto-updates fields)
- Pick each color from dropdowns
- Set proportions for each color with dedicated input fields
- Gray (NONE) proportion is auto-calculated
- Force starting tile color (optional)
- Save/load configurations
- Launch game directly

**Note:** Player colors are always WHITE vs BLACK.

### Method 2: CLI Interactive Mode

```bash
cd board_builder
python3 builder.py -i
```

Follow prompts to configure your board, then optionally launch:

```bash
python3 builder.py -i --launch
```

The interactive CLI will guide you through:
1. Board dimensions
2. Number of pieces
3. How many colors to use (1-9)
4. Selecting each color individually
5. Setting proportions for each color (gray auto-calculated)
6. Forcing starting tile color (optional)
7. Saving the configuration

**Note:** Player colors are always WHITE vs BLACK.

### Method 3: Python Code

```python
from board_builder import BoardBuilder
from game import Color

config = (BoardBuilder()
    .set_size(10, 10)                    # 10x10 board
    .set_pieces(4)                        # 4 pieces per player
    .set_colors(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW)
    .set_proportions(
        RED=0.25,
        GREEN=0.25, 
        BLUE=0.25,
        YELLOW=0.15,
        NONE=0.1                          # 10% gray tiles
    )
    .set_player_colors(Color.WHITE, Color.BLACK)
    .force_starting_color(Color.RED)      # Start on red tiles
    .build()
)

# Save for later
BoardBuilder().set_size(10, 10).save('saved_configs/my_board.json')

# Load and launch
from ui.kivy_app import ThreesomeApp
ThreesomeApp(config).run()
```

## Configuration Options

All options available in `main.py` are supported:

| Option | Description | Default |
|--------|-------------|---------|
| **Size** | Board width x height | 8x8 |
| **Pieces** | Number of pieces per player | 3 |
| **Color Palette** | Colors available on board (1-9 colors) | RED, GREEN, BLUE |
| **Color Proportions** | Distribution of tile colors | Equal split + gray remainder |
| **Player Colors** | Visual colors for pieces | WHITE, BLACK (fixed) |
| **Force Starting Color** | Color of starting tiles | None (random) |

### Available Colors

You can use up to 9 colors in your game (WHITE and BLACK are reserved for player pieces):

```
RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, PINK, BROWN, GRAY
```

**Note:** Gray tiles (NONE) are automatically calculated as `1.0 - sum(all color proportions)`

## Examples

### Large Board with Many Pieces

```python
config = (BoardBuilder()
    .set_size(12, 12)
    .set_pieces(5)
    .build()
)
```

### Mostly Red Tiles

```python
config = (BoardBuilder()
    .set_colors(Color.RED, Color.GREEN, Color.BLUE)
    .set_proportions(
        RED=0.6,      # 60% red
        GREEN=0.2,    # 20% green
        BLUE=0.15     # 15% blue
        # NONE (gray) = 0.05 (auto-calculated: 1.0 - 0.95 = 0.05)
    )
    .build()
)
```

### Force Starting on Green

```python
config = (BoardBuilder()
    .force_starting_color(Color.GREEN)
    .build()
)
```

### Many Colors (Rainbow Board!)

```python
config = (BoardBuilder()
    .set_size(12, 12)
    .set_colors(
        Color.RED, Color.ORANGE, Color.YELLOW, 
        Color.GREEN, Color.BLUE, Color.PURPLE, Color.PINK
    )
    .set_proportions(
        RED=0.15, ORANGE=0.15, YELLOW=0.15,
        GREEN=0.15, BLUE=0.15, PURPLE=0.15, PINK=0.05
        # NONE (gray) = 0.05 (auto-calculated)
    )
    .build()
)
```

## Save and Load Configurations

### Save

```python
builder = BoardBuilder()
builder.set_size(10, 10).set_pieces(4)
builder.save('saved_configs/my_board.json')
```

### Load

```python
builder = BoardBuilder.load('saved_configs/my_board.json')
config = builder.build()
```

### Load and Launch from CLI

```bash
cd board_builder
python3 builder.py -l saved_configs/my_board.json --launch
```

## Tips

1. **Larger boards** work better with more pieces (4-5)
2. **More colors** = more strategic variety (try 5-7 colors on large boards!)
3. **Color proportions** are automatically completed with gray tiles (NONE)
   - Just specify the colors you want, gray fills the rest
   - Gray tiles have no skills - use them to reduce randomness
4. **Force starting color** helps ensure balanced starts
5. **Save configs** you like for reuse
6. **Interactive mode** shows remaining proportions as you go

## Validation & Error Handling

Both builders now include comprehensive validation to catch common errors:

### Automatic Checks

✅ **Board Size**
- Minimum: 3x3
- Maximum: 20x20
- Prevents invalid dimensions

✅ **Number of Pieces**
- Minimum: 1 per player
- Maximum: 10 per player
- Automatically validates against board width (max = width × 0.8)

✅ **Color Palette**
- Prevents duplicate colors
- Must have at least 1 color
- WHITE and BLACK are reserved for player pieces

✅ **Color Proportions**
- Each must be between 0.0 and 1.0
- Total cannot exceed 1.0
- Gray (NONE) is auto-calculated

✅ **Force Starting Color**
- Must be in your color palette
- Visual builder: dropdown automatically updates with only valid colors
- CLI: validates and prompts again if invalid

### Error Messages

The builders provide clear, specific error messages when validation fails:
- "Board dimensions must be at least 3x3"
- "Too many pieces (7) for board width (8). Maximum recommended: 6"
- "Duplicate color detected: RED"
- "Color proportions sum to 1.25, which exceeds 1.0"
- "Force starting color YELLOW is not in the color palette: [RED, GREEN, BLUE]"

## Troubleshooting

**Q: Color proportions error**
- The builder validates automatically - just ensure each proportion is 0.0-1.0
- Total cannot exceed 1.0 (gray fills the remainder)

**Q: Too many/few pieces**
- The builder prevents this - maximum is automatically calculated based on board width

**Q: Can I use WHITE or BLACK as board colors?**
- No, these are reserved for player pieces
- Use GRAY if you want a light neutral color

**Q: Config file won't load**
- Check JSON syntax is valid
- Verify all color names are uppercase

**Q: Visual builder crashes**
- Try CLI mode: `cd board_builder && python3 builder.py -i`
- Or use Python code directly

## Integration with main.py

All board builder configurations work directly with `main.py`:

```bash
# Create config
cd board_builder
python3 builder.py -i
# (saves to saved_configs/my_board.json)

# Launch with main.py (from project root)
cd ..
python3 main.py -f board_builder/saved_configs/my_board.json
```

Or programmatically:

```python
from board_builder import BoardBuilder
from ui.kivy_app import ThreesomeApp

config = BoardBuilder().set_size(10, 10).build()
ThreesomeApp(config).run()
```

