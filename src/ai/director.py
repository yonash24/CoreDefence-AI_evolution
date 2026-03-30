import arcade
import random
import logging
from typing import List, Tuple, Dict, Any
from src.entities.enemies import BaseEnemy
from src.ai.pathing import Pathfinder
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
import numpy as np

logger = logging.getLogger(__name__)

class AIDirector:
    """
    The 'Overmind' of the game.
    Handles wave orchestration, difficulty scaling, and AI adaptation.
    
    Aesthetic: The 'AI' should feel like it's learning from the player's defense patterns.
    """
    def __init__(self, balance_data: Dict[str, Any], grid_manager: Any):
        self.balance_data = balance_data
        self.grid_manager = grid_manager
        self.pathfinder = Pathfinder()
        
        # Difficulty & Progression
        self.current_wave = 0
        self.difficulty_multiplier = 1.0
        self.adaptation_weight = balance_data.get("settings", {}).get("director_adaptation_weight", 0.5)
        
        # Wave State
        self.enemies_spawned = 0
        self.wave_in_progress = False
        self.spawn_timer = 0.0
        self.time_between_spawns = 1.5
        self.enemies_remaining_to_spawn = 0
        
        # Evolution Stats
        self.evolved_health_bonus = 0.0
        self.evolved_speed_bonus = 0.0
        
        # Pathfinding parameters
        self.start_pos = (0, self.grid_manager.rows // 2)
        self.end_pos = (self.grid_manager.cols - 1, self.grid_manager.rows // 2)
        
        # Threat assessment
        self.tower_threat_map = np.zeros((self.grid_manager.rows, self.grid_manager.cols), dtype=float)

    def start_next_wave(self, tower_list: arcade.SpriteList = None):
        """Prepare and start the next tactical wave."""
        self.current_wave += 1
        self.wave_in_progress = True
        
        # Calculate wave size (e.g., Wave 1: 5, Wave 2: 8, Wave 3: 12...)
        self.enemies_remaining_to_spawn = 5 + int(self.current_wave * 2.5)
        
        # Scale difficulty
        self.difficulty_multiplier = 1.0 + (self.current_wave - 1) * 0.15
        
        # Update intelligence
        self.grid_manager.decay_heat(0.5) # Forget old traps slightly
        if tower_list:
            self._update_tower_threat(tower_list)
        
        # Evolve enemies based on previous performance
        self.evolved_health_bonus = (self.current_wave - 1) * 5
        self.evolved_speed_bonus = (self.current_wave - 1) * 0.1
        
        logger.info(f"Starting Wave {self.current_wave} with {self.enemies_remaining_to_spawn} enemies.")
        logger.info(f"Difficulty Multiplier: {self.difficulty_multiplier:.2f}")

    def update(self, delta_time: float, enemy_list: arcade.SpriteList, tower_list: arcade.SpriteList = None):
        """Handle wave orchestration and spawning."""
        if not self.wave_in_progress:
            # Check if all enemies are dead to start countdown to next wave
            if len(enemy_list) == 0:
                self.start_next_wave(tower_list)
            return

        if self.enemies_remaining_to_spawn > 0:
            self.spawn_timer += delta_time
            if self.spawn_timer >= self.time_between_spawns:
                self.spawn_timer = 0
                self._spawn_enemy(enemy_list)
                self.enemies_remaining_to_spawn -= 1
        
        elif len(enemy_list) == 0:
            # All enemies in this wave are clear
            self.wave_in_progress = False
            logger.info(f"Wave {self.current_wave} Completed.")

    def _spawn_enemy(self, enemy_list: arcade.SpriteList):
        """Create a new enemy with evolved attributes and adaptive pathing."""
        # 1. Selection: Probabilistic selection of enemy types based on wave
        types = self.balance_data["enemies"]
        if self.current_wave < 3:
            # Only fast enemies at first
            enemy_cfg = types[0]
        else:
            # Mix in tanks and scouts
            enemy_cfg = random.choices(types, weights=[50, 25, 25])[0]
        
        # 2. Adaptive Pathfinding (AI Evolution)
        # We calculate a path that avoids the 'death heatmap'
        path = self._calculate_adaptive_path()
        
        if not path:
            logger.warning("No path found for enemy spawn!")
            return

        # 3. Attribute Evolution
        scaled_health = (enemy_cfg["health"] + self.evolved_health_bonus) * self.difficulty_multiplier
        scaled_speed = (enemy_cfg["speed"] + self.evolved_speed_bonus) * min(2.0, self.difficulty_multiplier)
        
        new_enemy = BaseEnemy(
            path=path,
            tile_stride=self.grid_manager.tile_stride,
            health=int(scaled_health),
            speed=scaled_speed,
            reward=enemy_cfg["reward"],
            asset=enemy_cfg.get("asset")
        )
        
        # Position at the start of the path
        new_enemy.center_x, new_enemy.center_y = self.grid_manager._get_world_pos(self.start_pos[1], self.start_pos[0])
        
        enemy_list.append(new_enemy)

    def _calculate_adaptive_path(self) -> List[Tuple[int, int]]:
        """
        Calculates a path that intelligently avoids areas where many enemies have died.
        This is the core of the 'AI Evolution' - the director learns and adapts.
        """
        # Create a fresh weight matrix from the grid
        rows, cols = self.grid_manager.rows, self.grid_manager.cols
        weight_matrix = np.ones((rows, cols), dtype=int)
        
        # Base weights from tile types
        # Path = 1, BuildSpot = 0 (impassable), Empty = 5, Core = 1
        for r in range(rows):
            for c in range(cols):
                tile_type = self.grid_manager.grid[r, c]
                if tile_type == 1: # PATH
                    weight_matrix[r, c] = 1
                elif tile_type == 2: # BUILD_SPOT
                    weight_matrix[r, c] = 0 # Impassable
                elif tile_type == 3: # CORE
                    weight_matrix[r, c] = 1
                else: # EMPTY
                    weight_matrix[r, c] = 5
        
        # AI Evolution: Add penalty from death heatmap
        # Higher weight = More costly to walk here
        # max_penalty = 50 (very strong discouragement)
        heatmap = self.grid_manager.death_heatmap
        max_heat = np.max(heatmap) if np.max(heatmap) > 0 else 1.0
        
        for r in range(rows):
            for c in range(cols):
                if weight_matrix[r, c] > 0: # If walkable
                    death_penalty = (heatmap[r, c] / (max_heat if max_heat > 0 else 1.0)) * 20
                    tower_penalty = self.tower_threat_map[r, c] * 15
                    
                    penalty = int((death_penalty + tower_penalty) * self.adaptation_weight)
                    weight_matrix[r, c] += penalty

        # Pathfinding
        grid = Grid(matrix=weight_matrix.tolist())
        start = grid.node(self.start_pos[0], self.start_pos[1])
        end = grid.node(self.end_pos[0], self.end_pos[1])
        
        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        path, runs = finder.find_path(start, end, grid)
        
        return [(node.x, node.y) for node in path]

    def _update_tower_threat(self, tower_list: arcade.SpriteList):
        """Map out areas covered by player towers to help the AI navigate better."""
        self.tower_threat_map.fill(0)
        rows, cols = self.grid_manager.rows, self.grid_manager.cols
        tile_stride = self.grid_manager.tile_stride
        
        for tower in tower_list:
            # Radius in tiles
            r_tiles = int(tower.range / tile_stride) + 1
            t_row, t_col = self.grid_manager.get_cell_from_mouse_coords(tower.center_x, tower.center_y)
            
            for r in range(max(0, t_row - r_tiles), min(rows, t_row + r_tiles + 1)):
                for c in range(max(0, t_col - r_tiles), min(cols, t_col + r_tiles + 1)):
                    # Circular fallout
                    dist = np.sqrt((r - t_row)**2 + (c - t_col)**2)
                    if dist <= r_tiles:
                        # Threat increases inversely to distance, normalized
                        self.tower_threat_map[r, c] += 1.0 - (dist / r_tiles)
