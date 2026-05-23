"""Color read test data source.

Reads colorReadTest.csv written by the Pi color-read sensor test.
Expected format:

    pct_diff
    10.48
"""

from __future__ import annotations

import csv
import math
import os
import threading
import time
from dataclasses import asdict, dataclass
from typing import Dict, Optional

ORGANIC_DETECTED_THRESHOLD = 50.0  # % — at or above this value organics are detected


@dataclass
class ColorReadReading:
    timestamp: float
    pct_diff: float


class ColorReadSource:
    """Polls colorReadTest.csv and exposes the latest pct_diff reading."""

    def __init__(self, poll_seconds: float = 0.5) -> None:
        self._poll = poll_seconds
        self._latest: Optional[ColorReadReading] = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ColorRead")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def latest(self) -> Optional[Dict]:
        with self._lock:
            if self._latest is None:
                return None
            reading = self._latest
        return {
            **asdict(reading),
            "organics_detected": reading.pct_diff >= ORGANIC_DETECTED_THRESHOLD,
            "interpretation": (
                "Organic signal detected"
                if reading.pct_diff >= ORGANIC_DETECTED_THRESHOLD
                else "No organic signal detected"
            ),
        }

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                reading = self._read()
                if reading is not None:
                    with self._lock:
                        self._latest = reading
            except Exception:
                pass
            self._stop.wait(self._poll)

    def _read(self) -> Optional[ColorReadReading]:
        raise NotImplementedError


class MockColorReadSource(ColorReadSource):
    """Dev source — returns a fixed sample pct_diff without hardware."""

    def _read(self) -> Optional[ColorReadReading]:
        return ColorReadReading(timestamp=time.time(), pct_diff=10.48)


class CsvColorReadSource(ColorReadSource):
    """Production source — reads the latest pct_diff row from colorReadTest.csv."""

    def __init__(self, path: str, poll_seconds: float = 0.5) -> None:
        super().__init__(poll_seconds=poll_seconds)
        self._path = path

    def _read(self) -> Optional[ColorReadReading]:
        if not os.path.exists(self._path):
            return None

        last_row: Optional[Dict[str, str]] = None
        with open(self._path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                last_row = row

        if last_row is None:
            return None

        raw = last_row.get("pct_diff", "").strip()
        if not raw:
            return None

        try:
            pct_diff = float(raw)
        except ValueError:
            return None
        if not math.isfinite(pct_diff):
            return None

        return ColorReadReading(timestamp=time.time(), pct_diff=pct_diff)


def build_chem_source(source: str, csv_path: str) -> ColorReadSource:
    """Factory used by main.py."""
    if source == "csv":
        return CsvColorReadSource(csv_path)
    return MockColorReadSource()
