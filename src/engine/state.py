"""
Core Defender: Game State and Economy
Handles gold, lives, and overall system status.
"""

class GameState:
    """
    Manages the global game variables and economic logic.
    """
    def __init__(self, starting_gold: int = 500, starting_lives: int = 20):
        self.gold = starting_gold
        self.lives = starting_lives
        self.game_over = False
        self.wave_number = 0

    def add_gold(self, amount: int):
        """Adds gold to the player's treasury."""
        if amount > 0:
            self.gold += amount

    def subtract_gold(self, amount: int) -> bool:
        """Removes gold if sufficient funds exist. Returns True if successful."""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def remove_lives(self, amount: int):
        """Reduces player lives. Triggers game over if lives reach zero."""
        self.lives -= amount
        if self.lives <= 0:
            self.lives = 0
            self.game_over = True
