#!/usr/bin/env python3
"""
Threesome Game Launcher
A strategic board game where players race pieces across a colored grid.
"""
import os
os.environ['KIVY_NO_ARGS'] = '1'


import argparse
import json
from pathlib import Path
from game import Color

def parse_color_list(color_str):
    """Parse comma-separated color list."""
    colors = []
    for c in color_str.split(','):
        c = c.strip().upper()
        try:
            colors.append(Color[c])
        except KeyError:
            raise argparse.ArgumentTypeError(f"Invalid color: {c}. Available: {', '.join([e.name for e in Color])}")
    return colors

def parse_color_proportions(prop_str):
    """Parse color proportions in format: RED:0.3,GREEN:0.3,BLUE:0.2,NONE:0.2"""
    if not prop_str:
        return None
    
    proportions = {}
    for pair in prop_str.split(','):
        color_name, prop = pair.split(':')
        color_name = color_name.strip().upper()
        
        if color_name == 'NONE':
            proportions[None] = float(prop)
        else:
            try:
                proportions[Color[color_name]] = float(prop)
            except KeyError:
                raise argparse.ArgumentTypeError(f"Invalid color: {color_name}")
    
    return proportions

def parse_color(color_str):
    """Parse color in format: RED,GREEN,BLUE"""
    color_names = [c.strip().upper() for c in color_str.split(',')]
    if len(color_names) != 1:
        raise argparse.ArgumentTypeError("Must specify exactly 1 color")
    try:
        return Color[color_names[0]]
    except KeyError:
        raise argparse.ArgumentTypeError(f"Invalid color: {color_names[0]}")

def parse_player_colors(colors_str):
    """Parse player colors in format: WHITE,BLACK"""
    color_names = [c.strip().upper() for c in colors_str.split(',')]
    if len(color_names) != 2:
        raise argparse.ArgumentTypeError("Must specify exactly 2 player colors")
    
    try:
        return tuple(Color[c] for c in color_names)
    except KeyError as e:
        raise argparse.ArgumentTypeError(f"Invalid color: {e}")

def load_config_file(config_path):
    """Load configuration from JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = json.load(f)
    
    # Convert color strings to Color enums (preserve order)
    if 'color_pallete' in config:
        config['color_pallete'] = [Color[c.upper()] for c in config['color_pallete']]
    
    if 'color_proportions' in config:
        proportions = {}
        for color_name, prop in config['color_proportions'].items():
            if color_name.upper() == 'NONE':
                proportions[None] = prop
            else:
                proportions[Color[color_name.upper()]] = prop
        config['color_proportions'] = proportions
    
    if 'player_colors' in config:
        config['player_colors'] = tuple(Color[c.upper()] for c in config['player_colors'])
    
    if 'force_starting_tiles' in config and config['force_starting_tiles']:
        config['force_starting_tiles'] = Color[config['force_starting_tiles'].upper()]
    
    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Threesome - A strategic board game')
    parser.add_argument('-W', '--width', type=int, default=8, help='Board width (default: 8)')
    parser.add_argument('-H', '--height', type=int, default=8, help='Board height (default: 8)')
    parser.add_argument('-p', '--pieces', type=int, default=3, help='Number of pieces per player (default: 3)')
    parser.add_argument('-c', '--colors', type=parse_color_list, default='RED,GREEN,BLUE',
                        help='Color palette (comma-separated, default: RED,GREEN,BLUE)')
    parser.add_argument('-cp', '--color-proportions', type=parse_color_proportions, default=None,
                        help='Color proportions (e.g., RED:0.3,GREEN:0.3,BLUE:0.2,NONE:0.2)')
    parser.add_argument('-pc', '--player-colors', type=parse_player_colors, default='WHITE,BLACK',
                        help='Player piece colors (default: WHITE,BLACK)')
    parser.add_argument('-f', '--config', type=str, default=None,
                        help='JSON config file (overrides other arguments)')
    parser.add_argument('-fs', '--force-starting-tiles', type=parse_color, default=None,
                        help='Force starting tiles to be a specific color (default: None)')
    parser.add_argument('--ai', action='store_true', help='Enable AI opponent')
    parser.add_argument('--ai-method', type=str, choices=['minimax'], default='minimax',
                        help='AI method to use (default: minimax)')
    parser.add_argument('--ai-player', type=int, choices=[0, 1], default=1,
                        help='Which player is AI: 0 or 1 (default: 1)')
    parser.add_argument('--ai-depth', type=int, default=3,
                        help='AI search depth (default: 3, higher = stronger but slower)')
    args = parser.parse_args()
    
    # Load from config file if provided, otherwise use CLI args
    if args.config:
        board_config = load_config_file(args.config)
    else:
        board_config = {
            'w': args.width,
            'h': args.height,
            'num_of_pieces': args.pieces,
            'color_pallete': args.colors,
            'color_proportions': args.color_proportions,
            'player_colors': args.player_colors,
            'force_starting_tiles': args.force_starting_tiles
        }
    
    from ui.kivy_app import ThreesomeApp
    ThreesomeApp(
        board_config=board_config,
        ai_enabled=args.ai,
        ai_method=args.ai_method,
        ai_player=args.ai_player,
        ai_depth=args.ai_depth
    ).run()

