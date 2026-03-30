"""
Core Defender Tower and Projectile Systems
Handles defensive deployment and combat logic.
"""

import arcade
import math
import time
from typing import Optional
import numpy as np
import os
from src.utils.resources import resolve, asset_exists

class Projectile(arcade.Sprite):
    """
    Neon-bright energy bolt that moves toward a target.
    """
    def __init__(self, start_x: float, start_y: float, target: arcade.Sprite, damage: int, speed: float = 8.0, scale: float = 0.5):
        # Using a simple soft circle texture for neon effect
        super().__init__(scale=scale)
        self.texture = arcade.make_soft_circle_texture(24, arcade.color.ELECTRIC_CYAN)
        
        self.center_x = start_x
        self.center_y = start_y
        self.target = target
        self.damage = damage
        self.speed = speed
        self.is_hit = False

    def update(self):
        """Move toward target or just fly straight if target is lost."""
        if not self.target or self.target.health <= 0:
            # Continue moving in the last known direction if target dies
            # For simplicity, we'll just flag it for removal if target is gone
            self.remove_from_sprite_lists()
            return

        # Calculate vector to target
        dx = self.target.center_x - self.center_x
        dy = self.target.center_y - self.center_y
        distance = math.sqrt(dx**2 + dy**2)

        if distance < self.speed:
            # Hit! Collision will be handled globally, but we flag it here
            self.is_hit = True
        else:
            # Normalize and move
            self.center_x += (dx / distance) * self.speed
            self.center_y += (dy / distance) * self.speed
            # Rotate to face movement
            self.angle = math.degrees(math.atan2(dy, dx))

class BaseTower(arcade.Sprite):
    """
    High-tech defensive pylon that shoots at enemies.
    """
    def __init__(self, x: float, y: float, stats: dict, scale: float = 0.5):
        # Stats: range, damage, fire_rate, cost
        super().__init__(scale=scale)
        
        # Try to load custom texture, else fallback
        asset_path = stats.get("asset")
        if asset_path and asset_exists(asset_path):
            self.texture = arcade.load_texture(resolve(asset_path))
            self.color = arcade.color.WHITE # Reset color if custom texture is used
        else:
            self.texture = arcade.make_soft_circle_texture(64, arcade.color.COOL_GREY)
            self.color = (0, 255, 255)  # Cyan glow
        
        self.center_x = x
        self.center_y = y
        
        self.range = stats.get("range", 200)
        self.damage = stats.get("damage", 10)
        self.fire_rate = stats.get("fire_rate", 1.0) # Seconds between shots
        self.cost = stats.get("cost", 100)
        
        self.last_shot_time = 0.0
        self.projectiles_to_spawn = []

    def update(self, delta_time: float, enemies: arcade.SpriteList):
        """Find closest enemy and shoot if cooldown ready."""
        # Find closest enemy within range
        closest_enemy = None
        min_distance = self.range

        for enemy in enemies:
            dx = enemy.center_x - self.center_x
            dy = enemy.center_y - self.center_y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < min_distance:
                min_distance = dist
                closest_enemy = enemy

        # Attack logic
        current_time = time.time()
        if closest_enemy and (current_time - self.last_shot_time) >= self.fire_rate:
            self.shoot(closest_enemy)
            self.last_shot_time = current_time

    def shoot(self, target: arcade.Sprite):
        """Creates a projectile toward the target."""
        projectile = Projectile(
            start_x=self.center_x,
            start_y=self.center_y,
            target=target,
            damage=self.damage
        )
        self.projectiles_to_spawn.append(projectile)
