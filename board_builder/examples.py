#!/usr/bin/env python3
"""
Board Configuration Examples
Shows various ways to configure custom boards.
"""
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from board_builder.builder import BoardBuilder
from game import Color


def example_1_basic():
    """Basic board configuration."""
    print("=== Example 1: Basic 10x10 Board ===")
    
    config = (BoardBuilder()
        .set_size(10, 10)
        .set_pieces(4)
        .build()
    )
    
    print(f"Size: {config['w']}x{config['h']}")
    print(f"Pieces: {config['num_of_pieces']}")
    print(f"Colors: {[c.name for c in config['color_pallete']]}")
    print()


def example_2_custom_colors():
    """Custom color palette."""
    print("=== Example 2: Custom 4-Color Palette ===")
    
    config = (BoardBuilder()
        .set_colors(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW)
        .build()
    )
    
    print(f"Colors: {[c.name for c in config['color_pallete']]}")
    print()


def example_3_color_proportions():
    """Custom color distribution."""
    print("=== Example 3: Custom Color Distribution ===")
    
    config = (BoardBuilder()
        .set_colors(Color.RED, Color.GREEN, Color.BLUE)
        .set_proportions(
            RED=0.4,      # 40% red tiles
            GREEN=0.3,    # 30% green tiles
            BLUE=0.2,     # 20% blue tiles
            NONE=0.1      # 10% gray tiles
        )
        .build()
    )
    
    props = config['color_proportions']
    print("Color distribution:")
    for color, prop in props.items():
        name = 'GRAY' if color is None else color.name
        print(f"  {name}: {prop*100}%")
    print()


def example_4_player_colors():
    """Custom player piece colors."""
    print("=== Example 4: Red vs Blue Players ===")
    
    config = (BoardBuilder()
        .set_player_colors(Color.RED, Color.BLUE)
        .build()
    )
    
    p0, p1 = config['player_colors']
    print(f"Player 0: {p0.name}")
    print(f"Player 1: {p1.name}")
    print()


def example_5_force_starting():
    """Force starting tile color."""
    print("=== Example 5: Always Start on Green ===")
    
    config = (BoardBuilder()
        .set_colors(Color.RED, Color.GREEN, Color.BLUE)
        .force_starting_color(Color.GREEN)
        .build()
    )
    
    print(f"Starting color: {config['force_starting_tiles'].name}")
    print()


def example_6_complete_custom():
    """Complete custom configuration."""
    print("=== Example 6: Complete Custom Board ===")
    
    config = (BoardBuilder()
        .set_size(12, 12)
        .set_pieces(5)
        .set_colors(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW, Color.PURPLE)
        .set_proportions(
            RED=0.2,
            GREEN=0.2,
            BLUE=0.2,
            YELLOW=0.15,
            PURPLE=0.15,
            NONE=0.1
        )
        .set_player_colors(Color.WHITE, Color.BLACK)
        .force_starting_color(Color.RED)
        .build()
    )
    
    print(f"Size: {config['w']}x{config['h']}")
    print(f"Pieces: {config['num_of_pieces']}")
    print(f"Colors: {[c.name for c in config['color_pallete']]}")
    print(f"Starting: {config['force_starting_tiles'].name}")
    print()


def example_7_save_load():
    """Save and load configurations."""
    print("=== Example 7: Save and Load ===")
    
    # Create config
    builder = (BoardBuilder()
        .set_size(10, 10)
        .set_pieces(4)
        .set_colors(Color.RED, Color.GREEN, Color.BLUE)
    )
    
    # Save to file
    filename = Path(__file__).parent / 'saved_configs' / 'example_board.json'
    builder.save(str(filename))
    print(f"Saved to: {filename}")
    
    # Load it back
    loaded = BoardBuilder.load(str(filename))
    config = loaded.build()
    print(f"Loaded: {config['w']}x{config['h']}, {config['num_of_pieces']} pieces")
    print()


def example_8_launch():
    """Launch game with custom config."""
    print("=== Example 8: Launch Game ===")
    
    config = (BoardBuilder()
        .set_size(10, 10)
        .set_pieces(4)
        .set_colors(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW)
        .force_starting_color(Color.RED)
        .build()
    )
    
    print("Configuration created. To launch:")
    print("\nfrom ui.kivy_app import ThreesomeApp")
    print("ThreesomeApp(config).run()")
    print()
    
    # Uncomment to actually launch:
    # os.environ['KIVY_NO_ARGS'] = '1'
    # from ui.kivy_app import ThreesomeApp
    # ThreesomeApp(config).run()


if __name__ == "__main__":
    example_1_basic()
    example_2_custom_colors()
    example_3_color_proportions()
    example_4_player_colors()
    example_5_force_starting()
    example_6_complete_custom()
    example_7_save_load()
    example_8_launch()
    
    print("=" * 50)
    print("All examples completed!")
    print("\nSee BOARD_BUILDER_GUIDE.md for more information.")

