"""Background worker that drives the spectroscopy pipeline.

Replaces the orchestration that lived in `run_with_dashboard.py` and
`spectrometer_app.py`. Operators control it through the REST API:

  POST /api/start    -> begin a session, take samples in a loop
  POST /api/stop     -> end the session
  POST /api/sample   -> take exactly one sample now

Samples are read from `Settings.test_image_path` in dev. To run on real
hardware swap the `_acquire_frame` implementation (or pass a callback).
"""

from __future__ import annotations

import os
import threading
import time
from typing import Callable, Optional

import numpy as np

from datalogger import SpectroscopyLogger

from ..config import Settings
from ..state import SystemState
from ..sources.spectrometer import SpectrometerService

FrameAcquirer = Callable[[], np.ndarray]


class SampleRunner:
    def __init__(
        self,
        settings: Settings,
        state: SystemState,
        spectrometer: SpectrometerService,
        acquirer: Optional[FrameAcquirer] = None,
        sample_period_seconds: float = 3.0,
    ) -> None:
        self._settings = settings
        self._state = state
        self._spectrometer = spectrometer
        self._acquirer = acquirer or self._default_acquirer
        self._sample_period = sample_period_seconds
        self._logger: Optional[SpectroscopyLogger] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> str:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return self._state.session_id or ""
            self._logger = SpectroscopyLogger(log_dir=self._settings.log_dir)
            session_id = self._logger.session_id
            self._state.set_running(session_id)
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True, name="SampleRunner")
            self._thread.start()
            return session_id

    def stop(self) -> None:
        with self._lock:
            self._stop.set()
            thread = self._thread
        if thread:
            thread.join(timeout=5)
        with self._lock:
            if self._logger:
                self._logger.end_session()
                self._logger = None
            self._thread = None
            self._state.set_idle()

    def take_one(self) -> str:
        """Synchronously acquire and process a single sample."""
        ephemeral_logger = self._logger or SpectroscopyLogger(log_dir=self._settings.log_dir)
        try:
            return self._acquire_and_log(ephemeral_logger)
        finally:
            if self._logger is None:
                ephemeral_logger.end_session()

    def _loop(self) -> None:
        try:
            assert self._logger is not None
            while not self._stop.is_set():
                self._acquire_and_log(self._logger)
                self._stop.wait(self._sample_period)
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self._state.set_error(f"runner crashed: {exc!r}")

    def _acquire_and_log(self, logger: SpectroscopyLogger) -> str:
        # Pick up any calibration changes the operator made via the UI.
        cal = [(p.pixel, p.wavelength_nm) for p in self._state.calibration]
        self._spectrometer.set_calibration(cal)

        frame = self._acquirer()
        result = self._spectrometer.analyze(frame)

        sample_id = f"sample_{int(time.time())}"
        ts = time.time()

        spectrum_payload = {
            "sample_id": sample_id,
            "timestamp": ts,
            **result,
        }

        logger.log_measurement(
            {
                "wavelengths": np.array(result["wavelengths"]),
                "spectrum": np.array(result["intensities"]),
                "peak_wavelengths": result["peak_wavelengths"],
                "peaks_detected": len(result["peak_wavelengths"]),
                "biosignature_analysis": result["biosignatures"],
                "raw_image": frame,
            },
            sample_id=sample_id,
        )

        self._state.record_sample(sample_id, spectrum_payload, ts)
        return sample_id

    def _default_acquirer(self) -> np.ndarray:
        """Dev acquirer: load test_spectrum.npy and add light noise.

        Replace this in production with a real sensor read.
        """
        path = self._settings.test_image_path
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"No frame source at {path!r}. Run `python3 testdata.py` first or wire a real sensor."
            )
        base = np.load(path)
        noise = np.random.normal(0, 50, base.shape)
        return np.clip(base + noise, 0, 4095).astype(base.dtype)
