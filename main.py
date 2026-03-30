"""
Core Defender: AI Evolution
Root entry point — delegates to src/main.py
"""
import os
import sys

# Ensure the project root is always in sys.path so imports work
# regardless of cwd (e.g. running `python main.py` from project root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.main import main  # noqa: E402

if __name__ == "__main__":
    main()