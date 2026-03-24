"""
Core Defence Enemy System
Handles enemy behavior, health, and path-based navigation.
"""

import arcade
import math
from typing import List, Tuple, Optional

class BaseEnemy(arcade.Sprite):
    """
    Base class for all enemy archetypes.
    Handles A* path traversal and vector-based movement.
    """
    def __init__(self, 
                 path: List[Tuple[int, int]], 
                 tile_stride: int,
                 health: int = 100, 
                 speed: float = 2.0):
        # Initialize the sprite with a simple triangle shape if no image is available
        # For now, we'll try to find a texture or use a simple shape
        super().__init__(scale=1.0)
        
        self.health = health
        self.speed = speed
        self.path = path  # List of (col, row)
        self.tile_stride = tile_stride
        self.current_path_index = 0
        
        # Movement State
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None
        
        # Set initial position to first waypoint if available
        if self.path:
            self.center_x, self.center_y = self._grid_to_world(self.path[0])
            self._set_next_waypoint()
            
        # Aesthetic: Simple Drone/Triangle shape
        # In a real scenario, this would be a sprite from a sheet.
        # We'll create a simple texture here or assign a dummy one.
        self._create_simple_texture()

    def _create_simple_texture(self):
        """Creates a neon-colored triangle texture programmatically."""
        # This is a bit advanced for arcade.Sprite without a file, 
        # but we can create one using a DrawingContext or similar.
        # For simplicity and given the prompt, we'll assume a triangle is better.
        # If we can't find a file, arcade.make_soft_circle_texture or similar can work.
        # Let's use a simple color sprite for now.
        self.texture = arcade.make_soft_circle_texture(32, arcade.color.ELECTRIC_CYAN)
        # We can simulate a triangle by changing the drawing if needed, 
        # but the prompt implies we should have a sprite.
        # Let's stick with this for now.

    def _grid_to_world(self, grid_pos: Tuple[int, int]) -> Tuple[float, float]:
        """Converts (col, row) grid index to world coordinates (pixels)."""
        col, row = grid_pos
        x = col * self.tile_stride + (self.tile_stride / 2)
        y = row * self.tile_stride + (self.tile_stride / 2)
        return x, y

    def _set_next_waypoint(self):
        """Sets the next destination based on the path index."""
        if self.current_path_index < len(self.path):
            self.target_x, self.target_y = self._grid_to_world(self.path[self.current_path_index])
        else:
            self.target_x, self.target_y = None, None

    def update(self, delta_time: float = 1/60):
        """
        Calculates movement toward the next waypoint.
        Uses normalized vectors to ensure consistent speed.
        """
        if self.target_x is None or self.target_y is None:
            return

        # 1. Calculate direction vector
        dx = self.target_x - self.center_x
        dy = self.target_y - self.center_y
        distance = math.sqrt(dx**2 + dy**2)

        # 2. Check if we reached the waypoint (within a small threshold)
        if distance <= self.speed:
            self.center_x = self.target_x
            self.center_y = self.target_y
            self.current_path_index += 1
            self._set_next_waypoint()
        else:
            # 3. Normalize and move
            # Ensures speed is consistent (e.g., 2.0 pixels per frame)
            vx = (dx / distance) * self.speed
            vy = (dy / distance) * self.speed
            
            self.center_x += vx
            self.center_y += vy
            
            # Simple rotation towards movement
            self.angle = math.degrees(math.atan2(vy, vx)) - 90
