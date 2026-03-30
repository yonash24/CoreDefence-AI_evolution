import arcade
import os
import sys
import json

# Ensure project root is in sys.path for internal imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.resources import load_balance, resolve

from src.engine.map import GridManager
from src.ai.pathing import Pathfinder
from src.entities.enemies import BaseEnemy
from src.entities.towers import BaseTower, Projectile
from src.engine.state import GameState
from src.ai.director import AIDirector
from src.ui.hud import HUD, MainMenu, GameOverMenu
import numpy as np
import random

class FadeParticle(arcade.Sprite):
    """Simple particle that fades out and moves."""
    def __init__(self, x, y, color):
        super().__init__()
        self.texture = arcade.make_soft_circle_texture(10, color)
        self.center_x = x
        self.center_y = y
        self.change_x = random.uniform(-3, 3)
        self.change_y = random.uniform(-3, 3)
        self.alpha = 255
        
    def update(self):
        self.alpha = max(0, self.alpha - 15)
        self.center_x += self.change_x
        self.center_y += self.change_y
        if self.alpha == 0:
            self.remove_from_sprite_lists()

class CoreDefender(arcade.View):
    """
    Main Application View for Core Defender.
    Handles orchestration between map, entities, and UI.
    """
    def __init__(self):
        super().__init__()
        
        # Data-driven components
        self.grid_manager: GridManager = None
        self.pathfinder: Pathfinder = None
        self.enemy_list: arcade.SpriteList = None
        self.tower_list: arcade.SpriteList = None
        self.projectile_list: arcade.SpriteList = None
        
        # Game State
        self.game_state: GameState = None
        self.balance_data = {}
        self.hud = None
        
        # Configuration Path (kept for GridManager; resource loader used elsewhere)
        self.config_path = resolve("data/balance.json")
        
        # Visual Polish
        self.show_ai_weights = False
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        """Initialize game state and components."""
        # Load balance data via centralised resource loader
        self.balance_data = load_balance()

        # 1. Initialize Game State
        self.game_state = GameState(starting_gold=500, starting_lives=20)

        # 2. Initialize the GridManager (Loads logic/visuals from JSON)
        self.grid_manager = GridManager(self.config_path)

        # 3. Synchronize Window Size with Grid Data
        new_width = self.grid_manager.cols * self.grid_manager.tile_stride
        new_height = self.grid_manager.rows * self.grid_manager.tile_stride
        
        # Audio Juice
        self.shoot_sound = arcade.load_sound(":resources:sounds/laser2.wav")
        self.hit_sound = arcade.load_sound(":resources:sounds/explosion2.wav")
        self.build_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.fail_sound = arcade.load_sound(":resources:sounds/error4.wav")
        
        # Visual Juice
        self.camera = arcade.Camera(self.window.width, self.window.height)
        self.shake_timer = 0.0
        self.particle_list = arcade.SpriteList()
        
        self.hud = HUD(new_width, new_height, self.balance_data)
        
        # 4. Navigation and AI Setup
        self.enemy_list = arcade.SpriteList()
        self.tower_list = arcade.SpriteList()
        self.projectile_list = arcade.SpriteList()
        
        self.director = AIDirector(self.balance_data, self.grid_manager)

    def on_draw(self):
        """Render the application."""
        self.clear()
        
        self.camera.use()
        
        if self.grid_manager:
            self.grid_manager.draw(show_heatmap=self.show_ai_weights)

        self.tower_list.draw()
        self.enemy_list.draw()
        self.projectile_list.draw()
        self.particle_list.draw()
        
        # Reset camera for HUD
        arcade.Camera(self.window.width, self.window.height).use()
        
        arcade.draw_text(f"Gold: {self.game_state.gold}", 20, self.window.height - 40, arcade.color.GOLD, 18, font_name="Kenney Future")
        arcade.draw_text(f"Lives: {self.game_state.lives}", 20, self.window.height - 70, arcade.color.RED_DEVIL, 18, font_name="Kenney Future")
        arcade.draw_text(f"Wave: {self.game_state.wave_number}", 20, self.window.height - 100, arcade.color.ELECTRIC_CYAN, 18, font_name="Kenney Future")
        
        # Advanced HUD
        if self.hud:
            adapter_heat = np.max(self.grid_manager.death_heatmap) if len(self.grid_manager.death_heatmap) > 0 else 0
            self.hud.draw(self.game_state.gold, self.game_state.lives, self.game_state.wave_number, adapter_heat)
        
        if self.game_state.game_over:
            arcade.draw_text("MISSION FAILURE", self.window.width//2, self.window.height//2, arcade.color.RED, 50, anchor_x="center", anchor_y="center", font_name="Kenney Future")

    def on_update(self, delta_time: float):
        """Update game logic and animations."""
        if self.game_state.game_over:
            # Transition to GameOverView
            game_over_view = GameOverMenu(success=False, restart_callback=reset_and_start_game)
            self.window.show_view(game_over_view)
            return

        # 1. Update sprites and juice
        self.enemy_list.update()
        self.projectile_list.update()
        self.particle_list.update()
        
        if self.shake_timer > 0:
            shake_x = random.uniform(-10, 10) * self.shake_timer
            shake_y = random.uniform(-10, 10) * self.shake_timer
            self.camera.move_to((shake_x, shake_y))
            self.shake_timer -= delta_time * 2
        else:
            self.camera.move_to((0, 0))
        
        # 2. Update AI Director
        self.director.update(delta_time, self.enemy_list, self.tower_list)
        self.game_state.wave_number = self.director.current_wave
        
        # 2. Update Tower targeting and projectile spawning
        for tower in self.tower_list:
            tower.update(delta_time, self.enemy_list)
            while tower.projectiles_to_spawn:
                p = tower.projectiles_to_spawn.pop(0)
                self.projectile_list.append(p)
                arcade.play_sound(self.shoot_sound, volume=0.2)

        # 3. Collision and Combat Logic
        for projectile in self.projectile_list:
            hit_list = arcade.check_for_collision_with_list(projectile, self.enemy_list)
            if hit_list:
                for enemy in hit_list:
                    enemy.take_damage(projectile.damage)
                    # Spawn impact juice
                    for _ in range(5):
                        self.particle_list.append(FadeParticle(enemy.center_x, enemy.center_y, arcade.color.ELECTRIC_CYAN))
                arcade.play_sound(self.hit_sound, volume=0.3)
                projectile.remove_from_sprite_lists()

        # 4. Handle Enemy Death and Goal Reach
        for enemy in self.enemy_list:
            # Reached Core?
            row, col = self.grid_manager.get_cell_from_mouse_coords(enemy.center_x, enemy.center_y)
            if self.grid_manager.grid[row, col] == 3: # 3 is TILE_CORE
                self.game_state.remove_lives(1)
                self.shake_timer = 1.0 # Screen shake
                arcade.play_sound(self.fail_sound, volume=0.5)
                enemy.remove_from_sprite_lists()
            
            # Dead?
            elif enemy.health <= 0:
                self.game_state.add_gold(enemy.reward)
                self.grid_manager.record_death(row, col)
                # Death explosion
                for _ in range(15):
                    self.particle_list.append(FadeParticle(enemy.center_x, enemy.center_y, arcade.color.MAGENTA))
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
                tower_cfg = self.hud.get_selected_tower() if self.hud else self.balance_data["towers"][0]
                if tower_cfg and self.game_state.subtract_gold(tower_cfg.get("cost", 100)):
                    world_pos = self.grid_manager._get_world_pos(row, col)
                    new_tower = BaseTower(world_pos[0], world_pos[1], tower_cfg)
                    self.tower_list.append(new_tower)
                    arcade.play_sound(self.build_sound)
                    
                    # Spawn build particles
                    for _ in range(10):
                        self.particle_list.append(FadeParticle(world_pos[0], world_pos[1], arcade.color.WHITE))
                else:
                    arcade.play_sound(self.fail_sound, volume=0.5)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Responsive feedback: 'Juice' the UI by updating hover highlights."""
        if self.grid_manager:
            prev_alpha = self.grid_manager.hover_highlight.alpha
            self.grid_manager.update_hover_feedback(x, y)
            
            # Play tiny click sound on new valid tile hover
            if prev_alpha == 0 and self.grid_manager.hover_highlight.alpha > 0:
                # Built-in subtle tick if we had one, but we can reuse a very quiet UI sound or skip
                pass

    def on_key_press(self, key, modifiers):
        """Handle keyboard inputs."""
        if key == arcade.key.H:
            self.show_ai_weights = not self.show_ai_weights
            print(f"AI Weight Visualization: {'ENABLED' if self.show_ai_weights else 'DISABLED'}")
            
        # Tower Selection
        if key >= arcade.key.KEY_1 and key <= arcade.key.KEY_9:
            idx = key - arcade.key.KEY_1
            if self.hud:
                self.hud.update_selected_tower(idx)

def start_game():
    window = arcade.get_window()
    game_view = CoreDefender()
    game_view.setup()
    window.show_view(game_view)

def reset_and_start_game():
    start_game()

def main():
    """Application Entry Point."""
    window = arcade.Window(1280, 768, "Core Defender: AI Evolution", resizable=False)
    
    # Pre-configure window size based on typical tile matrix so Menu is centered
    window.set_size(1300, 780)
    
    menu = MainMenu(start_callback=start_game)
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()
