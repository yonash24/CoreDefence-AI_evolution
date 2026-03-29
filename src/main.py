import arcade
import os
import sys
import json

# Ensure project root is in sys.path for internal imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.engine.map import GridManager
from src.ai.pathing import Pathfinder
from src.entities.enemies import BaseEnemy
from src.entities.towers import BaseTower, Projectile
from src.engine.state import GameState
from src.ai.director import AIDirector

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
        self.tower_list: arcade.SpriteList = None
        self.projectile_list: arcade.SpriteList = None
        
        # Game State
        self.game_state: GameState = None
        self.balance_data = {}
        
        # Configuration Path
        self.config_path = os.path.join(PROJECT_ROOT, "data", "balance.json")
        
        # Visual Polish
        self.show_ai_weights = False
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        """Initialize game state and components."""
        # Load balance data
        with open(self.config_path, 'r') as f:
            self.balance_data = json.load(f)

        # 1. Initialize Game State
        self.game_state = GameState(starting_gold=500, starting_lives=20)

        # 2. Initialize the GridManager (Loads logic/visuals from JSON)
        self.grid_manager = GridManager(self.config_path)

        # 3. Synchronize Window Size with Grid Data
        new_width = self.grid_manager.cols * self.grid_manager.tile_stride
        new_height = self.grid_manager.rows * self.grid_manager.tile_stride
        self.set_size(new_width, new_height)
        
        # 4. Navigation and AI Setup
        self.enemy_list = arcade.SpriteList()
        self.tower_list = arcade.SpriteList()
        self.projectile_list = arcade.SpriteList()
        
        # 5. AI Director Setup (The Overmind)
        self.director = AIDirector(self.balance_data, self.grid_manager)
        
        self.set_update_rate(1/60)

    def on_draw(self):
        """Render the application."""
        self.clear()
        
        if self.grid_manager:
            self.grid_manager.draw(show_heatmap=self.show_ai_weights)

        self.tower_list.draw()
        self.enemy_list.draw()
        self.projectile_list.draw()
        
        arcade.draw_text(f"Gold: {self.game_state.gold}", 20, self.height - 40, arcade.color.GOLD, 18, font_name="Kenney Future")
        arcade.draw_text(f"Lives: {self.game_state.lives}", 20, self.height - 70, arcade.color.RED_DEVIL, 18, font_name="Kenney Future")
        arcade.draw_text(f"Wave: {self.game_state.wave_number}", 20, self.height - 100, arcade.color.ELECTRIC_CYAN, 18, font_name="Kenney Future")
        
        if self.game_state.game_over:
            arcade.draw_text("MISSION FAILURE", self.width//2, self.height//2, arcade.color.RED, 50, anchor_x="center", font_name="Kenney Future")

    def on_update(self, delta_time: float):
        """Update game logic and animations."""
        if self.game_state.game_over:
            return

        # 1. Update sprites
        self.enemy_list.update()
        self.projectile_list.update()
        
        # 2. Update AI Director
        self.director.update(delta_time, self.enemy_list, self.tower_list)
        self.game_state.wave_number = self.director.current_wave
        
        # 2. Update Tower targeting and projectile spawning
        for tower in self.tower_list:
            tower.update(delta_time, self.enemy_list)
            while tower.projectiles_to_spawn:
                p = tower.projectiles_to_spawn.pop(0)
                self.projectile_list.append(p)

        # 3. Collision and Combat Logic
        for projectile in self.projectile_list:
            hit_list = arcade.check_for_collision_with_list(projectile, self.enemy_list)
            if hit_list:
                for enemy in hit_list:
                    enemy.take_damage(projectile.damage)
                projectile.remove_from_sprite_lists()

        # 4. Handle Enemy Death and Goal Reach
        for enemy in self.enemy_list:
            # Reached Core?
            row, col = self.grid_manager.get_cell_from_mouse_coords(enemy.center_x, enemy.center_y)
            if self.grid_manager.grid[row, col] == 3: # 3 is TILE_CORE
                self.game_state.remove_lives(1)
                enemy.remove_from_sprite_lists()
            
            # Dead?
            elif enemy.health <= 0:
                self.game_state.add_gold(enemy.reward)
                self.grid_manager.record_death(row, col)
                enemy.remove_from_sprite_lists()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle tower building."""
        if self.game_state.game_over:
            return

        row, col = self.grid_manager.get_cell_from_mouse_coords(x, y)
        if self.grid_manager.is_valid_build_spot(row, col):
            # Check if spot is occupied
            occupied = False
            for tower in self.tower_list:
                t_row, t_col = self.grid_manager.get_cell_from_mouse_coords(tower.center_x, tower.center_y)
                if t_row == row and t_col == col:
                    occupied = True
                    break
            
            if not occupied:
                tower_cfg = self.balance_data["towers"][0]
                if self.game_state.subtract_gold(tower_cfg["cost"]):
                    world_pos = self.grid_manager._get_world_pos(row, col)
                    new_tower = BaseTower(world_pos[0], world_pos[1], tower_cfg)
                    self.tower_list.append(new_tower)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Responsive feedback: 'Juice' the UI by updating hover highlights."""
        if self.grid_manager:
            self.grid_manager.update_hover_feedback(x, y)

    def on_key_press(self, key, modifiers):
        """Handle keyboard inputs."""
        if key == arcade.key.H:
            self.show_ai_weights = not self.show_ai_weights
            print(f"AI Weight Visualization: {'ENABLED' if self.show_ai_weights else 'DISABLED'}")

def main():
    """Application Entry Point."""
    window = CoreDefender(100, 100, "Core Defender: AI Evolution")
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
