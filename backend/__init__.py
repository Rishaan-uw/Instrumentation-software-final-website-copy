"""Husky Robotics rover science backend.

FastAPI service that exposes the spectroscopy pipeline, microscope cameras,
and chem instrument over a single HTTP API for the React control panel.
"""

import os

# processor.py imports matplotlib at module top. Force the headless backend
# before anything else loads it so the Pi never tries to open a GUI window.
os.environ.setdefault("MPLBACKEND", "Agg")

__version__ = "0.1.0"
