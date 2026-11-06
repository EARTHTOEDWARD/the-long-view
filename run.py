#!/usr/bin/env python3
"""Run the local source checkout without installing a package."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from the_long_view.engine import main


if __name__ == "__main__":
    main()
