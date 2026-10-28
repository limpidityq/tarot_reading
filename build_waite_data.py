"""Download a local Waite original-meaning snapshot before deployment.

Execute at the project root: python scripts/build_waite_data.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tarot_core import SNAPSHOT, load_cards  # noqa: E402

if __name__ == "__main__":
    if SNAPSHOT.exists():
        print(f"Snapshot already exists: {SNAPSHOT}")
    cards = load_cards()
    print(f"Validated {len(cards)} original Waite card meanings; snapshot: {SNAPSHOT}")
