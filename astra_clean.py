#!/usr/bin/env python3
"""Entry point script for astra-clean CLI tool."""

import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli import main

if __name__ == '__main__':
    sys.exit(main())
