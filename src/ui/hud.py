import arcade
import arcade.gui
from typing import Callable, List, Optional
import numpy as np

class MainMenu(arcade.View):
    """The Main Entry screen for the game."""
    def __init__(self, start_callback: Callable):
        super().__init__()
        self.start_callback = start_callback
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Create a layout
        self.v_box = arcade.gui.UIBoxLayout(space_between=20)
        
        title_label = arcade.gui.UILabel(
            text="CORE DEFENDER",
            font_size=48,
            font_name="Kenney Future",
            text_color=arcade.color.ELECTRIC_CYAN
        )
        subtitle_label = arcade.gui.UILabel(
            text="AI EVOLUTION",
            font_size=24,
            font_name="Kenney Future",
            text_color=arcade.color.MAGENTA
        )

        start_button = arcade.gui.UIFlatButton(text="INITIATE PROTOCOL", width=300, style={
            "normal": {
                "bg_color": (20, 20, 30),
                "font_color": arcade.color.ELECTRIC_CYAN,
                "border_width": 2,
                "border_color": arcade.color.ELECTRIC_CYAN,
                "font_name": "Kenney Future"
            }
        })
        start_button.on_click = self.on_start_click

        self.v_box.add(title_label)
        self.v_box.add(subtitle_label)
        self.v_box.add(start_button)
        
        # Center the UI
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def on_show_view(self):
        arcade.set_background_color((10, 10, 15))

    def on_draw(self):
        self.clear()
        self.manager.draw()
        
    def on_start_click(self, event):
        self.start_callback()
    
    def on_hide_view(self):
        self.manager.disable()


class GameOverMenu(arcade.View):
    """Mission Failure / Success Screen"""
    def __init__(self, success: bool, restart_callback: Callable):
        super().__init__()
        self.success = success
        self.restart_callback = restart_callback
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.v_box = arcade.gui.UIBoxLayout(space_between=20)
        
        title = "MISSION SUCCESS" if success else "MISSION FAILURE"
        color = arcade.color.GREEN if success else arcade.color.RED_DEVIL

        title_label = arcade.gui.UILabel(
            text=title,
            font_size=40,
            font_name="Kenney Future",
            text_color=color
        )
        
        restart_button = arcade.gui.UIFlatButton(text="REBOOT SYSTEM", width=300, style={
            "normal": {
                "bg_color": (20, 20, 30),
                "font_color": color,
                "border_width": 2,
                "border_color": color,
                "font_name": "Kenney Future"
            }
        })
        restart_button.on_click = self.on_restart_click

        self.v_box.add(title_label)
        self.v_box.add(restart_button)
        
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def on_show_view(self):
        arcade.set_background_color((15, 5, 5) if not self.success else (5, 15, 5))

    def on_draw(self):
        self.clear()
        self.manager.draw()
        
    def on_restart_click(self, event):
        self.restart_callback()

    def on_hide_view(self):
        self.manager.disable()


class HUD:
    """
    On-screen Display for the main game.
    Displays Economy, Waves, AI Adaptation Meter, and Tower Selection.
    """
    def __init__(self, width: int, height: int, balance_data: dict):
        self.width = width
        self.height = height
        self.towers_info = balance_data.get("towers", [])
        
        # Selected tower index for building
        self.selected_tower_idx = 0
        
        self.meter_bg_color = (30, 30, 40)
        self.meter_fill_color = arcade.color.MAGENTA

    def draw(self, gold: int, lives: int, wave: int, adapter_max_heat: float):
        """Draws top HUD and side/bottom elements."""
        # Top panel background
        arcade.draw_rectangle_filled(self.width / 2, self.height - 25, self.width, 50, (10, 15, 20, 230))
        arcade.draw_line(0, self.height - 50, self.width, self.height - 50, arcade.color.ELECTRIC_CYAN, 2)
        
        # Economy & Life Stats
        arcade.draw_text(f"GOLD: {gold}", 20, self.height - 32, arcade.color.GOLD, 16, font_name="Kenney Future", bold=True)
        arcade.draw_text(f"LIVES: {lives}", 150, self.height - 32, arcade.color.RED_DEVIL, 16, font_name="Kenney Future", bold=True)
        arcade.draw_text(f"WAVE: {wave}", 280, self.height - 32, arcade.color.ELECTRIC_CYAN, 16, font_name="Kenney Future", bold=True)
        
        # AI Adaptation Meter
        meter_x = self.width - 150
        meter_y = self.height - 25
        meter_w = 200
        meter_h = 16
        arcade.draw_text("AI HEAT:", meter_x - 140, meter_y - 8, arcade.color.WHITE, 12, font_name="Kenney Future")
        
        # Draw background meter
        arcade.draw_rectangle_filled(meter_x, meter_y, meter_w, meter_h, self.meter_bg_color)
        
        # Heat value can exceed 100, normalize it for aesthetic
        heat_ratio = min(1.0, adapter_max_heat / 50.0)
        fill_w = meter_w * heat_ratio
        if fill_w > 0:
            arcade.draw_rectangle_filled(meter_x - (meter_w/2) + (fill_w/2), meter_y, fill_w, meter_h, self.meter_fill_color)
            
        arcade.draw_rectangle_outline(meter_x, meter_y, meter_w, meter_h, arcade.color.CYAN, border_width=1)

        # Tower Selection Menu (Bottom Left)
        self._draw_tower_selection()

    def _draw_tower_selection(self):
        """Draws a horizontal dock of available towers."""
        panel_y = 50
        start_x = 70
        
        arcade.draw_rectangle_filled(start_x + 50, panel_y, 240, 80, (10, 15, 20, 200))
        arcade.draw_rectangle_outline(start_x + 50, panel_y, 240, 80, arcade.color.ELECTRIC_CYAN, 2)
        
        arcade.draw_text("TOWER ARCHIVES // [1-9] TO SELECT", start_x - 40, panel_y + 25, arcade.color.LIGHT_GRAY, 10, font_name="Kenney Future")
        
        for idx, tower in enumerate(self.towers_info):
            x = start_x + (idx * 80)
            y = panel_y - 10
            
            # Selection Highlight
            is_selected = (idx == self.selected_tower_idx)
            color = arcade.color.ELECTRIC_CYAN if is_selected else arcade.color.DARK_GRAY
            
            # Draw box
            arcade.draw_rectangle_outline(x, y, 64, 64, color, 2 if is_selected else 1)
            
            # Draw name and cost
            name = tower.get("type", "UNK")
            cost = str(tower.get("cost", 0))
            
            arcade.draw_text(f"{name[:4]}", x, y + 5, color, 10, anchor_x="center")
            arcade.draw_text(f"${cost}", x, y - 15, arcade.color.GOLD, 10, anchor_x="center")
            
    def update_selected_tower(self, index: int):
        if 0 <= index < len(self.towers_info):
            self.selected_tower_idx = index
            
    def get_selected_tower(self):
        if 0 <= self.selected_tower_idx < len(self.towers_info):
            return self.towers_info[self.selected_tower_idx]
        return None
