"""
Core Defender: AI Evolution
Main Orchestration Script - System Integration Layer.
"""

import arcade
import os
import sys

# Ensure project root is in sys.path for internal imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.engine.map import GridManager

class CoreDefender(arcade.Window):
    """
    Main Application class for Core Defender.
    Handles orchestration between map, entities, and UI.
    """
    def __init__(self, width: int, height: int, title: str):
        # Initial Window Setup
        super().__init__(width, height, title, resizable=False)
        
        # Data-driven components
        self.grid_manager: GridManager = None
        
        # Configuration Path
        self.config_path = os.path.join(PROJECT_ROOT, "data", "balance.json")
        
        # Visual Polish
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        """Initialize game state and components."""
        # 1. Initialize the GridManager (Loads logic/visuals from JSON)
        self.grid_manager = GridManager(self.config_path)
        
        # 2. Synchronize Window Size with Grid Data
        # GridManager calculates width_px/height_px from cols*stride
        new_width = self.grid_manager.cols * self.grid_manager.tile_stride
        new_height = self.grid_manager.rows * self.grid_manager.tile_stride
        self.set_size(new_width, new_height)
        
        # Center the window on screen (optional but nice)
        self.set_update_rate(1/60)

    def on_draw(self):
        """Render the application."""
        self.clear()
        
        # Render the map system (Batched for performance)
        if self.grid_manager:
            self.grid_manager.draw()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """
        Responsive feedback: 'Juice' the UI by updating hover highlights.
        """
        if self.grid_manager:
            self.grid_manager.update_hover_feedback(x, y)

def main():
    """Application Entry Point."""
    # Using small dummy values as setup() handles resizing to grid specs
    window = CoreDefender(100, 100, "Core Defender: AI Evolution")
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
