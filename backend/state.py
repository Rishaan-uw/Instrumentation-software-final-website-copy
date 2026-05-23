"""Shared, in-memory system state.

A single `SystemState` instance is held by the FastAPI app and updated
by the `SampleRunner` worker. Routers read from it to answer requests
without touching the worker thread directly.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RunStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class CalibrationPoint:
    pixel: int
    wavelength_nm: float


@dataclass
class SystemState:
    status: RunStatus = RunStatus.IDLE
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    sample_count: int = 0
    last_sample_id: Optional[str] = None
    last_sample_time: Optional[float] = None
    calibration: List[CalibrationPoint] = field(
        default_factory=lambda: [
            CalibrationPoint(0, 400.0),
            CalibrationPoint(640, 550.0),
            CalibrationPoint(1279, 700.0),
        ]
    )
    latest_spectrum: Optional[Dict[str, Any]] = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self.status.value,
                "error_message": self.error_message,
                "session_id": self.session_id,
                "sample_count": self.sample_count,
                "last_sample_id": self.last_sample_id,
                "last_sample_time": self.last_sample_time,
                "calibration": [
                    {"pixel": p.pixel, "wavelength_nm": p.wavelength_nm}
                    for p in self.calibration
                ],
            }

    def set_running(self, session_id: str) -> None:
        with self._lock:
            self.status = RunStatus.RUNNING
            self.session_id = session_id
            self.error_message = None

    def set_idle(self) -> None:
        with self._lock:
            self.status = RunStatus.IDLE

    def set_error(self, message: str) -> None:
        with self._lock:
            self.status = RunStatus.ERROR
            self.error_message = message

    def record_sample(self, sample_id: str, spectrum_payload: Dict[str, Any], ts: float) -> None:
        with self._lock:
            self.sample_count += 1
            self.last_sample_id = sample_id
            self.last_sample_time = ts
            self.latest_spectrum = spectrum_payload

    def get_latest_spectrum(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.latest_spectrum

    def set_calibration(self, points: List[CalibrationPoint]) -> None:
        with self._lock:
            self.calibration = points


_state_singleton: Optional[SystemState] = None


def get_state() -> SystemState:
    global _state_singleton
    if _state_singleton is None:
        _state_singleton = SystemState()
    return _state_singleton
