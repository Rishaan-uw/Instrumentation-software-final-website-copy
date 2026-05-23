"""Chem instrument data sources.

The UI is built against this abstract interface so the chem panel works
today against `MockChemSource` and a real instrument can drop in later
without touching frontend code.
"""

from __future__ import annotations

import csv
import math
import os
import random
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from typing import Deque, Dict, List, Optional


@dataclass
class ChemReading:
    timestamp: float
    ph: float
    conductivity_us_cm: float
    temperature_c: float
    moisture_pct: float
    organic_index: float


class ChemSource:
    """Base class. Subclasses push readings via `_push` from any thread."""

    def __init__(self, history_seconds: int = 600) -> None:
        self._history: Deque[ChemReading] = deque()
        self._history_seconds = history_seconds
        self._lock = threading.Lock()

    def _push(self, reading: ChemReading) -> None:
        with self._lock:
            self._history.append(reading)
            cutoff = reading.timestamp - self._history_seconds
            while self._history and self._history[0].timestamp < cutoff:
                self._history.popleft()

    def latest(self) -> Optional[Dict]:
        with self._lock:
            if not self._history:
                return None
            return asdict(self._history[-1])

    def history(self, minutes: int = 5) -> List[Dict]:
        cutoff = time.time() - minutes * 60
        with self._lock:
            return [asdict(r) for r in self._history if r.timestamp >= cutoff]

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class MockChemSource(ChemSource):
    """Generates plausible drifting readings on a background thread."""

    def __init__(self, hz: float = 1.0) -> None:
        super().__init__()
        self._period = 1.0 / hz
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="MockChem")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        t0 = time.time()
        while not self._stop.is_set():
            t = time.time() - t0
            self._push(
                ChemReading(
                    timestamp=time.time(),
                    ph=7.0 + 0.5 * math.sin(t / 30) + random.gauss(0, 0.05),
                    conductivity_us_cm=350 + 40 * math.sin(t / 45) + random.gauss(0, 5),
                    temperature_c=18 + 3 * math.sin(t / 120) + random.gauss(0, 0.1),
                    moisture_pct=22 + 4 * math.sin(t / 90) + random.gauss(0, 0.3),
                    organic_index=0.4 + 0.2 * math.sin(t / 60) + random.gauss(0, 0.02),
                )
            )
            self._stop.wait(self._period)


class CsvChemSource(ChemSource):
    """Tails a CSV the chem instrument writes.

    Expected columns (header required):
      timestamp,ph,conductivity_us_cm,temperature_c,moisture_pct,organic_index
    """

    def __init__(self, path: str, poll_seconds: float = 0.5) -> None:
        super().__init__()
        self._path = path
        self._poll = poll_seconds
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._offset = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="CsvChem")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                if os.path.exists(self._path):
                    with open(self._path, "r", newline="") as f:
                        f.seek(self._offset)
                        reader = csv.DictReader(f) if self._offset == 0 else csv.reader(f)
                        for row in reader:
                            if isinstance(row, dict):
                                self._push_dict(row)
                            else:
                                # Header was already consumed; skip plain rows for safety.
                                continue
                        self._offset = f.tell()
            except Exception:
                # Don't kill the thread on a single bad read.
                pass
            self._stop.wait(self._poll)

    def _push_dict(self, row: Dict[str, str]) -> None:
        try:
            self._push(
                ChemReading(
                    timestamp=float(row.get("timestamp", time.time())),
                    ph=float(row["ph"]),
                    conductivity_us_cm=float(row["conductivity_us_cm"]),
                    temperature_c=float(row["temperature_c"]),
                    moisture_pct=float(row["moisture_pct"]),
                    organic_index=float(row["organic_index"]),
                )
            )
        except (KeyError, ValueError):
            return


def build_chem_source(spec: str) -> ChemSource:
    """Factory used by main.py based on HUSKY_CHEM_SOURCE."""
    if spec.startswith("csv:"):
        return CsvChemSource(spec[len("csv:") :])
    return MockChemSource()
