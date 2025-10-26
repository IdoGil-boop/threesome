#!/usr/bin/env python3
"""
Visual Board Builder - GUI for creating custom board configurations
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ['KIVY_NO_ARGS'] = '1'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from game import Color
from board_builder.builder import BoardBuilder
from ui.kivy_app import ThreesomeApp


class BoardBuilderGUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)
        
        self.builder = BoardBuilder()
        self.color_values = ['RED', 'GREEN', 'BLUE', 'YELLOW', 'PURPLE', 'ORANGE', 'PINK', 'BROWN', 'GRAY']
        
        # Title
        title = Label(text="Board Builder", size_hint=(1, 0.1), font_size='24sp')
        self.add_widget(title)
        
        # Form
        form = GridLayout(cols=2, spacing=10, size_hint=(1, 0.7))
        
        # Width
        form.add_widget(Label(text="Width:", size_hint_x=0.3))
        self.width_input = TextInput(text='8', multiline=False, size_hint_x=0.7)
        form.add_widget(self.width_input)
        
        # Height
        form.add_widget(Label(text="Height:", size_hint_x=0.3))
        self.height_input = TextInput(text='8', multiline=False, size_hint_x=0.7)
        form.add_widget(self.height_input)
        
        # Pieces
        form.add_widget(Label(text="Pieces per player:", size_hint_x=0.3))
        self.pieces_input = TextInput(text='3', multiline=False, size_hint_x=0.7)
        form.add_widget(self.pieces_input)
        
        # Number of colors (with auto-update on change)
        form.add_widget(Label(text="Number of colors:", size_hint_x=0.3))
        self.num_colors_spinner = Spinner(
            text='3',
            values=[str(i) for i in range(1, 10)],
            size_hint_x=0.7
        )
        self.num_colors_spinner.bind(text=self.update_color_fields)
        form.add_widget(self.num_colors_spinner)
        
        # Color palette (dynamically shown/hidden)
        form.add_widget(Label(text="Color Palette:", size_hint_x=0.3))
        colors_scroll = ScrollView(size_hint_x=0.7, size_hint_y=None, height=200, do_scroll_x=False)
        self.colors_container = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.colors_container.bind(minimum_height=self.colors_container.setter('height'))
        colors_scroll.add_widget(self.colors_container)
        form.add_widget(colors_scroll)
        
        # Create all 9 spinners (will show/hide based on num_colors)
        self.color_spinners = []
        for i in range(9):
            default = self.color_values[i] if i < len(self.color_values) else 'RED'
            spinner = Spinner(
                text=default,
                values=self.color_values,
                size_hint_y=None,
                height=35
            )
            # Bind color changes to update force spinner options
            spinner.bind(text=lambda instance, value: self.update_force_spinner_options())
            self.color_spinners.append(spinner)
            self.colors_container.add_widget(spinner)
        
        # Color proportions (dynamic inputs based on selected colors)
        form.add_widget(Label(text="Color Proportions:", size_hint_x=0.3))
        props_scroll = ScrollView(size_hint_x=0.7, size_hint_y=None, height=150, do_scroll_x=False)
        self.proportions_container = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.proportions_container.bind(minimum_height=self.proportions_container.setter('height'))
        props_scroll.add_widget(self.proportions_container)
        form.add_widget(props_scroll)
        
        # Create proportion inputs (will be updated dynamically)
        self.proportion_inputs = {}
        
        # Player colors are always WHITE and BLACK (no configuration needed)
        
        # Force starting tiles
        form.add_widget(Label(text="Force starting color:", size_hint_x=0.3))
        self.force_spinner = Spinner(
            text='Random',
            values=['Random', 'RED', 'GREEN', 'BLUE', 'YELLOW', 'PURPLE', 'ORANGE'],
            size_hint_x=0.7
        )
        form.add_widget(self.force_spinner)
        
        # Now initialize color fields and proportions (after ALL containers are created)
        self.update_color_fields(None)
        
        self.add_widget(form)
        
        # Buttons
        buttons = BoxLayout(size_hint=(1, 0.2), spacing=10)
        
        save_btn = Button(text="Save Config")
        save_btn.bind(on_press=self.save_config)
        buttons.add_widget(save_btn)
        
        load_btn = Button(text="Load Config")
        load_btn.bind(on_press=self.load_config)
        buttons.add_widget(load_btn)
        
        launch_btn = Button(text="Launch Game", background_color=(0.7, 0.95, 0.8, 1))
        launch_btn.bind(on_press=self.launch_game)
        buttons.add_widget(launch_btn)
        
        self.add_widget(buttons)
    
    def update_color_fields(self, instance, value=None):
        """Show/hide color spinners based on num_colors_spinner."""
        try:
            num_colors = int(self.num_colors_spinner.text)
            num_colors = min(max(1, num_colors), 9)
        except (ValueError, AttributeError):
            num_colors = 3
        
        # Show/hide spinners based on count
        for i, spinner in enumerate(self.color_spinners):
            if i < num_colors:
                spinner.opacity = 1
                spinner.disabled = False
                spinner.size_hint_y = None
                spinner.height = 35
            else:
                spinner.opacity = 0
                spinner.disabled = True
                spinner.size_hint_y = None
                spinner.height = 0
        
        # Update proportion fields to match selected colors
        self.update_proportion_fields(None)
        
        # Update force starting color options
        self.update_force_spinner_options()
    
    def update_proportion_fields(self, instance):
        """Update proportion input fields based on selected colors."""
        try:
            num_colors = int(self.num_colors_spinner.text)
        except (ValueError, AttributeError):
            num_colors = 3
        
        # Clear existing proportion inputs
        self.proportions_container.clear_widgets()
        self.proportion_inputs = {}
        
        # Create proportion input for each visible color
        for i in range(min(num_colors, len(self.color_spinners))):
            color_name = self.color_spinners[i].text
            
            # Label for color
            label = Label(
                text=f"{color_name}:",
                size_hint_y=None,
                height=40,
                halign='right',
                valign='middle'
            )
            label.bind(size=label.setter('text_size'))
            self.proportions_container.add_widget(label)
            
            # Input for proportion
            prop_input = TextInput(
                text=f'{1.0/num_colors:.2f}',  # Equal distribution by default
                multiline=False,
                size_hint_y=None,
                height=40
            )
            self.proportion_inputs[color_name] = prop_input
            self.proportions_container.add_widget(prop_input)
        
        # Add gray (NONE) info label
        gray_label = Label(
            text="Gray (NONE):",
            size_hint_y=None,
            height=40,
            halign='right',
            valign='middle'
        )
        gray_label.bind(size=gray_label.setter('text_size'))
        self.proportions_container.add_widget(gray_label)
        
        gray_info = Label(
            text="(auto-calculated)",
            size_hint_y=None,
            height=40,
            italic=True,
            halign='left',
            valign='middle'
        )
        gray_info.bind(size=gray_info.setter('text_size'))
        self.proportions_container.add_widget(gray_info)
    
    def update_force_spinner_options(self):
        """Update force starting color dropdown based on selected colors."""
        # Safety check - make sure force_spinner exists
        if not hasattr(self, 'force_spinner'):
            return
        
        try:
            num_colors = int(self.num_colors_spinner.text)
        except (ValueError, AttributeError):
            num_colors = 3
        
        # Get currently selected colors
        selected_colors = ['Random']
        for i in range(min(num_colors, len(self.color_spinners))):
            selected_colors.append(self.color_spinners[i].text)
        
        # Update force spinner values
        current_value = self.force_spinner.text
        self.force_spinner.values = selected_colors
        
        # Reset to Random if current value is not in the new list
        if current_value not in selected_colors:
            self.force_spinner.text = 'Random'
    
    def build_config(self):
        """Build configuration from form inputs with validation."""
        builder = BoardBuilder()
        
        # Board size validation
        try:
            width = int(self.width_input.text or 8)
            height = int(self.height_input.text or 8)
            if width < 3 or height < 3:
                raise ValueError("Board dimensions must be at least 3x3")
            if width > 20 or height > 20:
                raise ValueError("Board dimensions cannot exceed 20x20")
        except ValueError as e:
            raise ValueError(f"Invalid board size: {e}")
        
        builder.set_size(width, height)
        
        # Pieces validation
        try:
            pieces = int(self.pieces_input.text or 3)
            if pieces < 1:
                raise ValueError("Must have at least 1 piece per player")
            if pieces > 10:
                raise ValueError("Cannot have more than 10 pieces per player")
            # Check if pieces fit on board
            if pieces > width * 0.8:
                raise ValueError(f"Too many pieces ({pieces}) for board width ({width}). Maximum recommended: {int(width * 0.8)}")
        except ValueError as e:
            raise ValueError(f"Invalid number of pieces: {e}")
        
        builder.set_pieces(pieces)
        
        # Colors validation (check for duplicates)
        colors = []
        num_colors = int(self.num_colors_spinner.text)
        for i in range(min(num_colors, len(self.color_spinners))):
            color = Color[self.color_spinners[i].text]
            if color in colors:
                raise ValueError(f"Duplicate color detected: {color.name}")
            colors.append(color)
        
        if not colors:
            raise ValueError("Must select at least one color")
        
        builder.set_colors(*colors)
        
        # Proportions validation
        proportions = {}
        total = 0.0
        for color_name, prop_input in self.proportion_inputs.items():
            try:
                value = float(prop_input.text)
                if value < 0 or value > 1:
                    raise ValueError(f"{color_name} proportion must be between 0 and 1 (got {value})")
                proportions[color_name] = value
                total += value
            except ValueError as e:
                raise ValueError(f"Invalid proportion for {color_name}: {e}")
        
        if total > 1.0:
            raise ValueError(f"Color proportions sum to {total:.2f}, which exceeds 1.0")
        
        if proportions:
            builder.set_proportions(**proportions)
        
        # Player colors are always WHITE and BLACK (no configuration needed)
        
        # Force starting color validation
        if self.force_spinner.text != 'Random':
            force_color = Color[self.force_spinner.text]
            # Check if force color is in the palette
            if force_color not in colors:
                raise ValueError(f"Force starting color {force_color.name} is not in the color palette: {[c.name for c in colors]}")
            builder.force_starting_color(force_color)
        else:
            builder.force_starting_color(None)
        
        return builder
    
    def save_config(self, instance):
        """Save configuration to file."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        filename_input = TextInput(text='saved_configs/my_board.json', multiline=False)
        content.add_widget(Label(text="Enter filename:"))
        content.add_widget(filename_input)
        
        popup = Popup(title='Save Configuration', content=content, size_hint=(0.6, 0.3))
        
        def do_save(btn):
            try:
                builder = self.build_config()
                filename = filename_input.text
                # Ensure it's saved in saved_configs directory
                if not filename.startswith('saved_configs/'):
                    filename = f'saved_configs/{filename}'
                builder.save(filename)
                popup.dismiss()
                self.show_message(f"Saved to {filename}")
            except Exception as e:
                self.show_message(f"Error: {str(e)}")
        
        save_button = Button(text='Save', size_hint=(1, 0.3))
        save_button.bind(on_press=do_save)
        content.add_widget(save_button)
        
        popup.open()
    
    def load_config(self, instance):
        """Load configuration from file."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        filename_input = TextInput(text='saved_configs/my_board.json', multiline=False)
        content.add_widget(Label(text="Enter filename:"))
        content.add_widget(filename_input)
        
        popup = Popup(title='Load Configuration', content=content, size_hint=(0.6, 0.3))
        
        def do_load(btn):
            try:
                builder = BoardBuilder.load(filename_input.text)
                config = builder.config
                
                # Update form
                self.width_input.text = str(config['w'])
                self.height_input.text = str(config['h'])
                self.pieces_input.text = str(config['num_of_pieces'])
                
                # Update number of colors and show/hide spinners
                num_colors = len(config['color_pallete'])
                self.num_colors_spinner.text = str(num_colors)
                self.update_color_fields(None)
                
                # Update color spinners
                for i, spinner in enumerate(self.color_spinners):
                    if i < len(config['color_pallete']):
                        spinner.text = config['color_pallete'][i].name
                
                # Update proportions in input fields
                if config['color_proportions']:
                    for color, value in config['color_proportions'].items():
                        if color is not None:  # Exclude NONE (gray)
                            color_name = color.name
                            if color_name in self.proportion_inputs:
                                self.proportion_inputs[color_name].text = str(value)
                
                # Player colors are always WHITE and BLACK (no configuration needed)
                
                self.force_spinner.text = config['force_starting_tiles'].name if config['force_starting_tiles'] else 'Random'
                
                popup.dismiss()
                self.show_message(f"Loaded from {filename_input.text}")
            except Exception as e:
                self.show_message(f"Error: {str(e)}")
        
        load_button = Button(text='Load', size_hint=(1, 0.3))
        load_button.bind(on_press=do_load)
        content.add_widget(load_button)
        
        popup.open()
    
    def launch_game(self, instance):
        """Launch game with current configuration."""
        try:
            builder = self.build_config()
            config = builder.build()
            
            # Close builder and launch game
            App.get_running_app().stop()
            ThreesomeApp(config).run()
        except Exception as e:
            self.show_message(f"Error launching game: {str(e)}")
    
    def show_message(self, message):
        """Show a popup message."""
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        close_btn = Button(text='Close', size_hint=(1, 0.3))
        content.add_widget(close_btn)
        
        popup = Popup(title='Message', content=content, size_hint=(0.5, 0.3))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class VisualBoardBuilderApp(App):
    def build(self):
        Window.size = (700, 550)
        return BoardBuilderGUI()


if __name__ == "__main__":
    VisualBoardBuilderApp().run()

