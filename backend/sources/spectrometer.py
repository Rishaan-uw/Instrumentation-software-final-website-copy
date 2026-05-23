"""Spectrometer sources.

Two implementations:
  SpectrometerService   – wraps processor.py; used in dev with a test .npy frame.
  CsvColorSpectrometer  – reads peaks_colors.csv from the Pi; production on the rover.

Both expose the same interface:
  .set_calibration(points)
  .analyze(frame_or_none) -> dict
"""

from __future__ import annotations

import csv
import math
import os
import threading
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from processor import SpectrometerProcessor


# ── Shared band definitions ────────────────────────────────────────────────────
# Sorted ascending by wavelength (Blue → Red).
# Each tuple: (csv_column_name, wl_min, wl_max, midpoint_nm)

COLOR_BANDS: List[Tuple[str, int, int, float]] = [
    ("Blue",   450, 495, 472.5),
    ("Cyan",   485, 500, 492.5),
    ("Green",  495, 570, 532.5),
    ("Yellow", 570, 590, 580.0),
    ("Orange", 590, 620, 605.0),
    ("Red",    620, 750, 685.0),
]

WL_STEP = 5  # nm per generated graph point


def _is_valid(v: float) -> bool:
    return math.isfinite(v)


def _parse_float_cell(raw: str) -> Optional[float]:
    raw = raw.strip()
    if raw.lower() in ("", "nan", "-nan", "inf", "-inf"):
        return None
    try:
        v = float(raw)
        return v if _is_valid(v) else None
    except ValueError:
        return None


def _read_last_csv_row(path: str) -> Optional[Dict[str, str]]:
    if not os.path.exists(path):
        return None
    last_row: Optional[Dict[str, str]] = None
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            last_row = row
    return last_row


def _build_spectrum(band_values: Dict[str, Optional[float]]) -> Dict[str, Any]:
    """
    Given a dict {color_name: intensity | None}, generate wavelength/intensity
    arrays (5 nm steps, ascending) and peak arrays (midpoint per valid band).
    Invalid or missing bands are skipped entirely.
    """
    wavelengths: List[float] = []
    intensities: List[float] = []
    peak_wl: List[float] = []
    peak_int: List[float] = []

    for col, wl_min, wl_max, midpoint in COLOR_BANDS:
        val = band_values.get(col)
        if val is None or not _is_valid(val):
            continue
        for wl in range(wl_min, wl_max + 1, WL_STEP):
            wavelengths.append(float(wl))
            intensities.append(val)
        peak_wl.append(midpoint)
        peak_int.append(val)

    return {
        "wavelengths": wavelengths,
        "intensities": intensities,
        "peak_wavelengths": peak_wl,
        "peak_intensities": peak_int,
    }


# ── Image-based service (dev / mock) ──────────────────────────────────────────

class SpectrometerService:
    def __init__(self, wavelength_range: Tuple[int, int] = (400, 700)) -> None:
        self.processor = SpectrometerProcessor(wavelength_range=wavelength_range)

    def set_calibration(self, points: List[Tuple[int, float]]) -> None:
        self.processor.wavelength_calibration(points)

    def analyze(self, image_2d: np.ndarray) -> Dict[str, Any]:
        spectrum_raw = self.processor.extract_spectrum(image_2d)
        wavelengths, spectrum = self.processor.apply_calibration(spectrum_raw)
        spectrum_corrected = self.processor.baseline_correction(spectrum)
        spectrum_smooth = self.processor.smooth_spectrum(spectrum_corrected)
        peak_wl, peak_int, _ = self.processor.find_peaks(wavelengths, spectrum_smooth)

        biosignatures = _detect_biosignatures(peak_wl)

        return {
            "wavelengths": wavelengths.tolist(),
            "intensities": spectrum_smooth.tolist(),
            "peak_wavelengths": peak_wl.tolist(),
            "peak_intensities": peak_int.tolist(),
            "biosignatures": biosignatures,
        }


# ── CSV-backed spectrometer (production / Pi) ────────────────────────────────

class CsvColorSpectrometer:
    """
    Polls peaks_colors.csv on the Pi for 6-band spectrometer graph data.

    CSV format (header on row 1):
        Red,Orange,Yellow,Green,Cyan,Blue
        2.26509,2.07029,1.88324,1.76782,-nan,-6.89396

    The latest row is used on each poll.
    """

    def __init__(self, color_csv: str, poll_seconds: float = 0.5) -> None:
        self._color_csv = color_csv
        self._poll = poll_seconds
        self._latest: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="CsvColorSpec")
        self._thread.start()

    def set_calibration(self, points: object) -> None:
        pass  # not applicable for CSV source

    def analyze(self, _frame: object = None) -> Dict[str, Any]:
        with self._lock:
            if self._latest is not None:
                return self._latest
        return _empty_spectrum()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                result = self._read_csv()
                if result is not None:
                    with self._lock:
                        self._latest = result
            except Exception:
                pass
            self._stop.wait(self._poll)

    def _read_csv(self) -> Optional[Dict[str, Any]]:
        last_row = _read_last_csv_row(self._color_csv)
        if last_row is None:
            return None

        band_values: Dict[str, Optional[float]] = {}
        for col, *_ in COLOR_BANDS:
            band_values[col] = _parse_float_cell(last_row.get(col, ""))

        if not any(v is not None for v in band_values.values()):
            return None

        return _build_spectrum(band_values)


def _empty_spectrum() -> Dict[str, Any]:
    return {
        "wavelengths": [],
        "intensities": [],
        "peak_wavelengths": [],
        "peak_intensities": [],
    }


# ── Biosignature helpers (mock / dev spectrometer only) ───────────────────────

def _detect_biosignatures(peak_wavelengths: Any) -> Dict[str, Any]:
    """Legacy heuristic for image-based spectrometer."""
    has_chlorophyll = any(425 < p < 435 for p in peak_wavelengths) or any(
        655 < p < 665 for p in peak_wavelengths
    )
    has_carotenoids = any(450 < p < 550 for p in peak_wavelengths)
    has_organics = any(400 < p < 450 for p in peak_wavelengths)

    indicators = sum([has_chlorophyll, has_carotenoids, has_organics])
    if indicators == 0:
        confidence, interpretation = "none", "No biosignatures detected"
    elif indicators == 1:
        confidence, interpretation = "low", "Weak biosignature detected"
    elif indicators == 2:
        confidence, interpretation = "medium", "Multiple biosignatures detected"
    else:
        confidence, interpretation = "high", "Strong biosignature pattern detected"

    return {
        "chlorophyll": has_chlorophyll,
        "carotenoids": has_carotenoids,
        "organics": has_organics,
        "confidence": confidence,
        "interpretation": interpretation,
    }
