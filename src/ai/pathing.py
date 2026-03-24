"""
Core Defence Navigation System
Implements A* pathfinding using the `pathfinding` library.
Handles grid weight conversion and path caching.
"""

import numpy as np
from typing import List, Tuple, Optional
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Pathfinder:
    """
    Handles pathfinding logic over the game grid.
    Features: Cost-informed traversal (A*), grid weight mapping, and caching.
    """
    def __init__(self):
        # Local cache: (grid_hash, start, end) -> path
        self._cache = {}

    def get_path(self, grid_matrix: np.ndarray, start_node: Tuple[int, int], end_node: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Calculates the optimal path from start to end using weighted grid costs.
        
        Weight Mapping:
        - TILE_PATH (1) -> cost=1
        - TILE_BUILD_SPOT (2) -> cost=0 (impassable)
        - TILE_EMPTY (0) -> cost=5
        - TILE_CORE (3) -> cost=1
        
        Args:
            grid_matrix: Numpy matrix of cell types.
            start_node: (col, row) grid coordinates.
            end_node: (col, row) grid coordinates.
            
        Returns:
            List of (x, y) grid coordinates.
        """
        # 1. Check Cache
        grid_id = hash(grid_matrix.tobytes())
        cache_key = (grid_id, start_node, end_node)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 2. Convert Numpy matrix to weighted pathfinding grid
        # pathfinding library uses (col, row) internally
        # grid_matrix is typically [row, col]
        rows, cols = grid_matrix.shape
        weight_matrix = np.ones((rows, cols), dtype=int)
        
        # Apply weights based on user specifications
        # Paths (1) = 1
        # BuildSpots (2) = 0 (infinite cost/impassable)
        # Empty (0) = 5
        # Core (3) = 1
        
        weight_matrix[grid_matrix == 1] = 1 # Paths
        weight_matrix[grid_matrix == 2] = 0 # BuildSpots (Impassable)
        weight_matrix[grid_matrix == 0] = 5 # Empty (Walkable but discouraged)
        weight_matrix[grid_matrix == 3] = 1 # Core
        
        # Create the grid
        # Note: pathfinding.core.grid.Grid expects [row][col] mapping
        grid = Grid(matrix=weight_matrix.tolist())
        
        # pathfinding.core.grid.Grid.node(x, y) takes (col, row)
        start = grid.node(start_node[0], start_node[1])
        end = grid.node(end_node[0], end_node[1])
        
        # 3. Find path
        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        path, runs = finder.find_path(start, end, grid)
        
        # Convert path objects to simple (x, y) tuples
        result = [(node.x, node.y) for node in path]
        
        # Cache Result
        self._cache[cache_key] = result
        return result

    def clear_cache(self):
        """Invoke this when the map layout is significantly changed."""
        self._cache.clear()
