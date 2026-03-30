"""
Core Defender: Resource Loader
A single authoritative source for resolving asset and data paths
relative to the project root, regardless of cwd or how the app is launched.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

# The project root is two levels above this file (src/utils/resources.py → project root)
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


def get_project_root() -> Path:
    """Return the absolute project root Path object."""
    return _PROJECT_ROOT


def resolve(relative_path: str) -> str:
    """
    Resolve a path relative to the project root to an absolute string path.

    Usage:
        tex = arcade.load_texture(resolve("assets/tower_basic.png"))
    """
    return str(_PROJECT_ROOT / relative_path)


def load_balance(relative_path: str = "data/balance.json") -> Dict[str, Any]:
    """
    Load and return the balance JSON file.

    Args:
        relative_path: Path relative to project root. Defaults to data/balance.json.

    Returns:
        Parsed Python dict.

    Raises:
        FileNotFoundError: If the JSON file cannot be found.
        json.JSONDecodeError: If the file is malformed.
    """
    abs_path = resolve(relative_path)
    with open(abs_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_level(level_file: str) -> Dict[str, Any]:
    """
    Load a level definition from data/levels/<level_file>.

    Args:
        level_file: Filename (e.g. "level_1.json").

    Returns:
        Parsed Python dict.
    """
    rel = f"data/levels/{level_file}"
    return load_balance(rel)


def asset_exists(relative_path: str) -> bool:
    """Return True if an asset file exists relative to project root."""
    return (_PROJECT_ROOT / relative_path).is_file()
