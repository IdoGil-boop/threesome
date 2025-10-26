#!/usr/bin/env python3
"""
Simple Board Builder - Create custom board configurations
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from game import Color

class BoardBuilder:
    """Build custom board configurations using existing parameters."""
    
    def __init__(self):
        self.config = {
            'w': 8,
            'h': 8,
            'num_of_pieces': 3,
            'color_pallete': [Color.RED, Color.GREEN, Color.BLUE],
            'color_proportions': None,
            'player_colors': (Color.WHITE, Color.BLACK),
            'force_starting_tiles': None
        }
    
    def set_size(self, width, height):
        """Set board dimensions."""
        self.config['w'] = width
        self.config['h'] = height
        return self
    
    def set_pieces(self, num_pieces):
        """Set number of pieces per player."""
        self.config['num_of_pieces'] = num_pieces
        return self
    
    def set_colors(self, *colors):
        """Set color palette. Example: .set_colors(Color.RED, Color.GREEN, Color.BLUE)"""
        self.config['color_pallete'] = list(colors)
        return self
    
    def set_proportions(self, **proportions):
        """
        Set color proportions. Example:
        .set_proportions(RED=0.3, GREEN=0.3, BLUE=0.2, NONE=0.2)
        """
        props = {}
        for color_name, value in proportions.items():
            if color_name.upper() == 'NONE':
                continue
            try:
                props[Color[color_name.upper()]] = value
            except KeyError:
                raise ValueError(f"Invalid color: {color_name}")
        if sum(props.values()) != 1.0:
            props[None] = 1.0 - sum(props.values())
        self.config['color_proportions'] = props
        return self
    
    def set_player_colors(self, player0_color, player1_color):
        """Set piece colors for each player."""
        self.config['player_colors'] = (player0_color, player1_color)
        return self
    
    def force_starting_color(self, color):
        """Force starting tiles to be a specific color (or None for random)."""
        self.config['force_starting_tiles'] = color
        return self
    
    def build(self):
        """Return the configuration dict."""
        return self.config.copy()
    
    def save(self, filename):
        """Save configuration to JSON file."""
        # Convert Color enums to strings for JSON
        json_config = {
            'w': self.config['w'],
            'h': self.config['h'],
            'num_of_pieces': self.config['num_of_pieces'],
            'color_pallete': [c.name for c in self.config['color_pallete']],
            'player_colors': [c.name for c in self.config['player_colors']],
            'force_starting_tiles': self.config['force_starting_tiles'].name if self.config['force_starting_tiles'] else None
        }
        
        if self.config['color_proportions']:
            json_config['color_proportions'] = {
                (c.name if c else 'NONE'): v 
                for c, v in self.config['color_proportions'].items()
            }
        
        path = Path(filename)
        with open(path, 'w') as f:
            json.dump(json_config, f, indent=2)
        
        return self
    
    @staticmethod
    def load(filename):
        """Load configuration from JSON file."""
        path = Path(filename)
        with open(path, 'r') as f:
            json_config = json.load(f)
        
        builder = BoardBuilder()
        builder.config['w'] = json_config.get('w', 8)
        builder.config['h'] = json_config.get('h', 8)
        builder.config['num_of_pieces'] = json_config.get('num_of_pieces', 3)
        builder.config['color_pallete'] = [Color[c] for c in json_config.get('color_pallete', ['RED', 'GREEN', 'BLUE'])]
        builder.config['player_colors'] = tuple(Color[c] for c in json_config.get('player_colors', ['WHITE', 'BLACK']))
        
        force = json_config.get('force_starting_tiles')
        builder.config['force_starting_tiles'] = Color[force] if force else None
        
        if 'color_proportions' in json_config:
            props = {}
            for color_name, value in json_config['color_proportions'].items():
                if color_name == 'NONE':
                    props[None] = value
                else:
                    props[Color[color_name]] = value
            builder.config['color_proportions'] = props
        
        return builder


def interactive_builder():
    """Interactive CLI board builder with validation."""
    print("=== Board Builder ===\n")
    
    # Board size with validation
    while True:
        try:
            width = int(input("Board width (default 8): ") or "8")
            if width < 3:
                print("  Error: Width must be at least 3")
                continue
            if width > 20:
                print("  Error: Width cannot exceed 20")
                continue
            break
        except ValueError:
            print("  Error: Please enter a valid number")
    
    while True:
        try:
            height = int(input("Board height (default 8): ") or "8")
            if height < 3:
                print("  Error: Height must be at least 3")
                continue
            if height > 20:
                print("  Error: Height cannot exceed 20")
                continue
            break
        except ValueError:
            print("  Error: Please enter a valid number")
    
    # Number of pieces with validation
    max_pieces = int(width * 0.8)
    while True:
        try:
            pieces = int(input(f"Pieces per player (default 3, max {max_pieces}): ") or "3")
            if pieces < 1:
                print("  Error: Must have at least 1 piece per player")
                continue
            if pieces > 10:
                print("  Error: Cannot have more than 10 pieces per player")
                continue
            if pieces > max_pieces:
                print(f"  Error: Too many pieces for board width. Maximum: {max_pieces}")
                continue
            break
        except ValueError:
            print("  Error: Please enter a valid number")
    
    # Colors
    print("\nAvailable colors:")
    available_colors = [c for c in Color if c not in [Color.WHITE, Color.BLACK]]  # Exclude player colors
    print(", ".join([c.name for c in available_colors]))
    
    num_colors = int(input(f"\nHow many colors? (1-{len(available_colors)}, default 3): ") or "3")
    num_colors = min(max(1, num_colors), len(available_colors))  # Clamp between 1 and max
    
    colors = []
    print(f"\nSelect {num_colors} colors:")
    for i in range(num_colors):
        while True:
            color_input = input(f"  Color {i+1} (default {['RED', 'GREEN', 'BLUE', 'YELLOW', 'PURPLE', 'ORANGE', 'PINK', 'BROWN', 'GRAY'][i] if i < 9 else 'RED'}): ").strip().upper()
            if not color_input:
                color_input = ['RED', 'GREEN', 'BLUE', 'YELLOW', 'PURPLE', 'ORANGE', 'PINK', 'BROWN', 'GRAY'][i] if i < 9 else 'RED'
            try:
                color = Color[color_input]
                if color in colors:
                    print(f"    {color.name} already selected, choose another")
                    continue
                if color in [Color.WHITE, Color.BLACK]:
                    print(f"    {color.name} is reserved for player pieces, choose another")
                    continue
                colors.append(color)
                break
            except KeyError:
                print(f"    Invalid color: {color_input}")
    
    # Color proportions
    use_proportions = input("\nSet color proportions? (y/n, default n): ").lower() == 'y'
    proportions = {}
    if use_proportions:
        print("Enter proportions (0.0-1.0):")
        total = 0.0
        for color in colors:
            while True:
                try:
                    prop = input(f"  {color.name} ({1.0 - total:.2f} remaining): ").strip()
                    if not prop:
                        prop = (1.0 - total) / (len(colors) - len(proportions))  # Equal split remaining
                    else:
                        prop = float(prop)
                    
                    if prop < 0 or prop > 1.0:
                        print("    Proportion must be between 0.0 and 1.0")
                        continue
                    if total + prop > 1.0:
                        print(f"    Too much! Maximum is {1.0 - total:.2f}")
                        continue
                    
                    proportions[color.name] = prop
                    total += prop
                    break
                except ValueError:
                    print("    Invalid number")
        
        # Automatically set NONE (gray) to remaining
        if total < 1.0:
            proportions['NONE'] = 1.0 - total
            print(f"  NONE (gray tiles): {1.0 - total:.2f} (auto-calculated)")
    
    # Player colors are always WHITE and BLACK
    print("\n(Player colors: WHITE vs BLACK)")
    
    # Force starting tiles with validation
    while True:
        force = input(f"\nForce starting tile color? (default None, available: {', '.join(c.name for c in colors)}): ").strip().upper()
        if not force:
            force_color = None
            break
        if force not in [c.name for c in colors]:
            print(f"  Error: {force} is not in your color palette. Choose from: {', '.join(c.name for c in colors)}")
            continue
        force_color = Color[force]
        break
    
    # Build configuration
    builder = BoardBuilder()
    builder.set_size(width, height)
    builder.set_pieces(pieces)
    builder.set_colors(*colors)
    
    if proportions:
        builder.set_proportions(**proportions)
    
    # Player colors are always WHITE and BLACK (default)
    builder.force_starting_color(force_color)
    
    # Save option
    save = input("\nSave configuration? (y/n): ").lower() == 'y'
    if save:
        filename = input("Filename (e.g., my_board.json): ")
        # Ensure it's saved in saved_configs directory
        if not filename.startswith('saved_configs/'):
            filename = f'saved_configs/{filename}'
        builder.save(filename)
        print(f"Saved to {filename}")
    
    return builder


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Board configuration builder')
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('-l', '--load', type=str, help='Load config from file')
    parser.add_argument('--launch', action='store_true', help='Launch game with config')
    
    args = parser.parse_args()
    
    if args.interactive:
        builder = interactive_builder()
        config = builder.build()
        
        if args.launch:
            print("\nLaunching game...")
            import os
            os.environ['KIVY_NO_ARGS'] = '1'
            from ui.kivy_app import ThreesomeApp
            ThreesomeApp(config).run()
    
    elif args.load:
        builder = BoardBuilder.load(args.load)
        config = builder.build()
        print(f"\nLoaded configuration from {args.load}:")
        print(f"  Size: {config['w']}x{config['h']}")
        print(f"  Pieces: {config['num_of_pieces']}")
        print(f"  Colors: {', '.join(c.name for c in config['color_pallete'])}")
        
        if args.launch:
            print("\nLaunching game...")
            import os
            os.environ['KIVY_NO_ARGS'] = '1'
            from ui.kivy_app import ThreesomeApp
            ThreesomeApp(config).run()
    
    else:
        # Example usage
        print("Example: Creating a custom board\n")
        
        config = (BoardBuilder()
            .set_size(10, 10)
            .set_pieces(4)
            .set_colors(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW)
            .set_proportions(RED=0.25, GREEN=0.25, BLUE=0.25, YELLOW=0.15, NONE=0.1)
            .set_player_colors(Color.WHITE, Color.BLACK)
            .force_starting_color(Color.RED)
            .build()
        )
        
        print("Created configuration:")
        print(f"  Size: {config['w']}x{config['h']}")
        print(f"  Pieces: {config['num_of_pieces']}")
        print(f"  Colors: {', '.join(c.name for c in config['color_pallete'])}")
        print(f"  Starting color: {config['force_starting_tiles'].name if config['force_starting_tiles'] else 'Random'}")
        
        print("\nUsage:")
        print("  Interactive: python3 builder.py -i")
        print("  Load file:   python3 builder.py -l saved_configs/myboard.json")
        print("  Launch:      python3 builder.py -l saved_configs/myboard.json --launch")

