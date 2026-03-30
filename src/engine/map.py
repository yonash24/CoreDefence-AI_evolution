"""
Core Defence Map System
Handles the DATA and VISUAL representation of the terrain.
Aesthetic: Clean, Dark Sci-Fi / Cyberpunk Outpost.
"""

import arcade
import numpy as np
import json
import os
import logging
from typing import Tuple, Dict, List, Optional
from src.utils.resources import resolve as _resolve, get_project_root

# Set up logging for professional debugging
logger = logging.getLogger(__name__)

# Grid Data Constants
TILE_EMPTY = 0
TILE_PATH = 1
TILE_BUILD_SPOT = 2
TILE_CORE = 3

class Tile(arcade.Sprite):
    """
    Highly performant Tile sprite.
    Minimal logic here; focus on data and presentation.
    """
    def __init__(self, filename: str, scale: float, row: int, col: int, tile_type: str):
        super().__init__(filename, scale)
        self.row = row
        self.col = col
        self.tile_type = tile_type

class GridManager:
    """
    Orchestrates the map grid.
    Interfaces between the game engine and the visual terrain.
    """
    def __init__(self, config_path: str = "data/balance.json"):
        self.config_path = config_path
        
        # Load data-driven configuration
        self._load_config()
        
        # Performance: Use Numpy for grid queries (AI, Pathfinding)
        self.grid = np.zeros((self.rows, self.cols), dtype=int)
        
        # Training Data: AI Director learns from where players kill enemies
        self.death_heatmap = np.zeros((self.rows, self.cols), dtype=float)
        
        # Batched Rendering Lists
        self.terrain_list = arcade.SpriteList(use_spatial_hash=True)
        self.ui_list = arcade.SpriteList()  # For highlights/juice
        
        # Hover effect sprite
        self.hover_highlight = arcade.Sprite(self.textures["highlight"], self.scale)
        self.hover_highlight.alpha = 0
        self.ui_list.append(self.hover_highlight)
        
        # Grid boundaries in pixels
        self.width_px = self.cols * self.tile_stride
        self.height_px = self.rows * self.tile_stride
        
        # Build initial map layout
        self._generate_static_map()
        self._initialize_sprites()

    def _load_config(self):
        """Loads grid dimensions and assets from JSON with robust path resolution."""
        try:
            # Use the centralised resource loader – always relative to project root
            full_config_path = _resolve(self.config_path)

            with open(full_config_path, 'r') as f:
                full_data = json.load(f)
                cfg = full_data.get("map_settings", {})

            self.rows = cfg.get("rows", 12)
            self.cols = cfg.get("cols", 20)
            self.tile_base_size = cfg.get("tile_size", 64)
            self.tile_spacing = cfg.get("tile_spacing", 1)
            self.tile_stride = self.tile_base_size + self.tile_spacing

            # Asset relative paths resolved to absolute
            raw_textures = cfg.get("tiles", {})
            self.textures = {
                k: _resolve(v) for k, v in raw_textures.items()
            }

            # Auto-calculate scale (Assets are 256x256)
            self.scale = self.tile_base_size / 256.0

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load map config: {e}")
            # Fallback defaults
            self.rows, self.cols = 10, 10
            self.tile_base_size = 64
            self.tile_stride = 65
            self.scale = 0.25
            self.textures = {}

    def _generate_static_map(self):
        """
        Creates the logical level layout in the Numpy matrix.
        In a full implementation, this could load from a .tmx or .json map file.
        """
        # Create a simple path for demonstration
        path_y = self.rows // 2
        self.grid[path_y, :] = TILE_PATH
        
        # Place the Core at the end
        self.grid[path_y, self.cols - 1] = TILE_CORE
        
        # Surround path with building spots for tactical depth
        for x in range(2, self.cols - 2):
            if self.grid[path_y - 1, x] == TILE_EMPTY:
                self.grid[path_y - 1, x] = TILE_BUILD_SPOT
            if self.grid[path_y + 1, x] == TILE_EMPTY:
                self.grid[path_y + 1, x] = TILE_BUILD_SPOT

    def _initialize_sprites(self):
        """Batch-creates sprites for the terrain list."""
        for row in range(self.rows):
            for col in range(self.cols):
                tile_id = self.grid[row, col]
                
                # Determine asset path and meta-type
                if tile_id == TILE_PATH:
                    tex_file = self.textures["path"]
                    t_type = "Path"
                elif tile_id == TILE_BUILD_SPOT:
                    tex_file = self.textures["build_spot"]
                    t_type = "BuildSpot"
                elif tile_id == TILE_CORE:
                    tex_file = self.textures["core_area"]
                    t_type = "CoreArea"
                else:
                    # Generic background fill
                    tex_file = self.textures["path"]
                    t_type = "Background"
                
                # Screen position calculation
                center_x = col * self.tile_stride + (self.tile_stride / 2)
                center_y = row * self.tile_stride + (self.tile_stride / 2)
                
                tile = Tile(tex_file, self.scale, row, col, t_type)
                tile.position = (center_x, center_y)
                
                # Aesthetic Polish: Background tiles are dimmed
                if t_type == "Background":
                    tile.color = (40, 45, 50)
                
                self.terrain_list.append(tile)

    def draw(self, show_heatmap: bool = False):
        """Premium batched rendering."""
        self.terrain_list.draw()
        if show_heatmap:
            self.draw_heatmap()
        self.ui_list.draw()

    def draw_heatmap(self):
        """Visualizes the AI's learning data (death heatmap)."""
        for row in range(self.rows):
            for col in range(self.cols):
                heat = self.death_heatmap[row, col]
                if heat > 0:
                    x, y = self._get_world_pos(row, col)
                    # Simple rectangle for heat visualization
                    # Fade intensity based on heat (capped at 150 alpha)
                    alpha = min(150, int(heat * 20))
                    arcade.draw_rectangle_filled(
                        x, y, self.tile_base_size, self.tile_base_size,
                        (255, 0, 0, alpha)
                    )

    def update_hover_feedback(self, mouse_x: float, mouse_y: float):
        """
        Implements 'Juice': Subtle glow when hovering valid spots.
        """
        row, col = self.get_cell_from_mouse_coords(mouse_x, mouse_y)
        
        if self.is_valid_build_spot(row, col):
            world_x, world_y = self._get_world_pos(row, col)
            self.hover_highlight.position = (world_x, world_y)
            self.hover_highlight.alpha = 200 # Semi-transparent glow
        else:
            self.hover_highlight.alpha = 0

    def get_cell_from_mouse_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Converts screen pixels to (row, col) grid coordinates."""
        col = int(x // self.tile_stride)
        row = int(y // self.tile_stride)
        
        # Clamp to avoid index errors
        return (
            max(0, min(row, self.rows - 1)),
            max(0, min(col, self.cols - 1))
        )

    def is_valid_build_spot(self, row: int, col: int) -> bool:
        """Consults the Numpy grid for high-performance validation."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row, col] == TILE_BUILD_SPOT
        return False

    def record_death(self, row: int, col: int):
        """Increments the heatmap value at specified grid location."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.death_heatmap[row, col] += 1.0
            logger.debug(f"Recorded death at ({row}, {col}). Current heat: {self.death_heatmap[row, col]}")

    def decay_heat(self, amount: float = 0.1):
        """Cool down the heatmap over time (waves)."""
        self.death_heatmap = np.maximum(0, self.death_heatmap - amount)

    def _get_world_pos(self, row: int, col: int) -> Tuple[float, float]:
        """Internal helper for pixel center of a cell."""
        x = col * self.tile_stride + (self.tile_stride / 2)
        y = row * self.tile_stride + (self.tile_stride / 2)
        return (x, y)
