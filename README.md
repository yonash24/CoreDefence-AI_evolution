# Core Defender: Adaptive AI

A strategy/puzzle game where an "AI Director" observes player patterns and adapts enemy waves using A* pathfinding and weighted parameter mutation.

## Overview
- **Architecture**: Clean-slate high-level software engineering.
- **Engine**: Python Arcade.
- **Key Modules**:
  - `src/engine/`: Core game physics, map, and state.
  - `src/ai/`: Director pattern and pathfinding.
  - `src/entities/`: Tower and enemy archetypes.
  - `src/ui/`: Game HUD and menus.

## Setup
1. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the game:
   ```bash
   python main.py
   ```

## Key Technologies
- **Arcade**: 2D Game Engine.
- **Numpy**: Vector and grid calculations.
- **Pathfinding**: Efficient A* implementation.
- **Pydantic**: Data validation for balance and state.
