"""
Core Defence Enemy System
Handles enemy behavior, health, and path-based navigation.
"""

import arcade
import math
import os
from typing import List, Tuple, Optional
from src.utils.resources import resolve, asset_exists

class BaseEnemy(arcade.Sprite):
    """
    Base class for all enemy archetypes.
    Handles A* path traversal and vector-based movement.
    """
    def __init__(self, 
                 path: List[Tuple[int, int]], 
                 tile_stride: int,
                 health: int = 100, 
                 speed: float = 2.0,
                 **kwargs):
        # Initialize the sprite with a simple triangle shape if no image is available
        # For now, we'll try to find a texture or use a simple shape
        super().__init__(scale=1.0)
        
        self.reward = kwargs.get("reward", 10)
        self.health = health
        self.max_health = health
        self.speed = speed
        self.is_dead = False
        self.path = path  # List of (col, row)
        self.tile_stride = tile_stride
        self.current_path_index = 0
        
        # Movement State
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None
        
        # Set initial position to first waypoint if available
        if self.path:
            pos_x, pos_y = self._grid_to_world(self.path[0])
            self.center_x = pos_x
            self.center_y = pos_y
            self.current_path_index = 1 # Start moving to the second node
            self._set_next_waypoint()
            
        # Aesthetic: Load texture or use simple shapes based on type
        self.asset = kwargs.get("asset")
        self.enemy_type = kwargs.get("type", "Unknown")
        self._load_visuals()
        
    def take_damage(self, amount: int):
        """Reduces health and flags enemy as dead if HP <= 0."""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_dead = True

    def _load_visuals(self):
        """Loads specialized texture or creates visually distinct shapes if missing."""
        if self.asset and asset_exists(self.asset):
            self.texture = arcade.load_texture(resolve(self.asset))
        else:
            # Fallback based on enemy archetype/health/speed combination
            # Try to guess from the asset name roughly if we don't have a specific `enemy_type` arg
            if self.asset and "fast" in self.asset.lower() or self.speed > 3.0:
                self.texture = arcade.make_soft_circle_texture(24, arcade.color.ELECTRIC_CYAN)
            elif self.asset and "tank" in self.asset.lower() or self.health > 100:
                self.texture = arcade.make_soft_square_texture(48, arcade.color.RED_DEVIL, 255, 255)
            elif self.asset and "scout" in self.asset.lower():
                self.texture = arcade.make_soft_circle_texture(28, arcade.color.NEON_CARROT)
            else:
                self.texture = arcade.make_soft_circle_texture(32, arcade.color.MAGENTA)

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
