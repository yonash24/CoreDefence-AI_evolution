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
from src.ai.pathing import Pathfinder
from src.entities.enemies import BaseEnemy

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
        self.pathfinder: Pathfinder = None
        self.enemy_list: arcade.SpriteList = None
        
        # Configuration Path
        self.config_path = os.path.join(PROJECT_ROOT, "data", "balance.json")
        
        # Visual Polish
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        """Initialize game state and components."""
        # 1. Initialize the GridManager (Loads logic/visuals from JSON)
        self.grid_manager = GridManager(self.config_path)

        # 2. Synchronize Window Size with Grid Data
        new_width = self.grid_manager.cols * self.grid_manager.tile_stride
        new_height = self.grid_manager.rows * self.grid_manager.tile_stride
        self.set_size(new_width, new_height)
        
        # 3. Navigation and AI Setup
        self.pathfinder = Pathfinder()
        self.enemy_list = arcade.SpriteList()
        
        # 4. Spawn Test Enemy at start of the path
        path_y = self.grid_manager.rows // 2
        start_pos = (0, path_y)
        end_pos = (self.grid_manager.cols - 1, path_y)
        
        # Calculate A* path
        calculated_path = self.pathfinder.get_path(
            self.grid_manager.grid, 
            start_pos, 
            end_pos
        )
        
        # Spawn one drone at entry
        if calculated_path:
            test_enemy = BaseEnemy(
                path=calculated_path, 
                tile_stride=self.grid_manager.tile_stride,
                speed=2.5
            )
            self.enemy_list.append(test_enemy)
        
        # Center the window on screen (optional but nice)
        self.set_update_rate(1/60)

    def on_draw(self):
        """Render the application."""
        self.clear()
        
        # Render the map system (Batched for performance)
        if self.grid_manager:
            self.grid_manager.draw()

        # Render enemies
        self.enemy_list.draw()

    def on_update(self, delta_time: float):
        """Update game logic and animations."""
        # Update enemy movements based on their AI paths
        self.enemy_list.update()

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
