"""Spectrometer sources.

Two implementations:
  SpectrometerService   – wraps processor.py; used in dev with a test .npy frame.
  CsvColorSpectrometer  – reads color-band intensities from a Pi CSV file;
                          used in production on the rover.

Both expose the same interface:
  .set_calibration(points)
  .analyze(frame_or_none) -> dict
"""

from __future__ import annotations

import csv
import math
import os
import threading
import time
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


# ── CSV-backed color spectrometer (production / Pi) ───────────────────────────

class CsvColorSpectrometer:
    """
    Polls /home/robot/HR-pi/output_data/peaks_colors.csv and
    (optionally) an organic_pct CSV.

    CSV format for peaks_colors.csv (header on row 1):
        Red,Orange,Yellow,Green,Cyan,Blue
        2.26509,2.07029,1.88324,1.76782,-nan,-6.89396

    The latest row is used each time analyze() is called.

    organic_pct_csv format — any CSV with a column named
    "organic_pct" or "organic_percent" (latest row wins).
    """

    def __init__(
        self,
        color_csv: str,
        organic_pct_csv: str = "",
        poll_seconds: float = 0.5,
    ) -> None:
        self._color_csv = color_csv
        self._organic_csv = organic_pct_csv
        self._poll = poll_seconds
        self._latest: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="CsvColorSpec")
        self._thread.start()

    # ── public interface (matches SpectrometerService) ─────────────────────

    def set_calibration(self, points: object) -> None:
        pass  # not applicable for CSV source

    def analyze(self, _frame: object = None) -> Dict[str, Any]:
        with self._lock:
            if self._latest is not None:
                return self._latest
        return self._empty_result()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3)

    # ── background polling ─────────────────────────────────────────────────

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
        if not os.path.exists(self._color_csv):
            return None

        band_values: Dict[str, Optional[float]] = {}
        last_row: Optional[Dict[str, str]] = None

        with open(self._color_csv, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                last_row = row

        if last_row is None:
            return None

        for col, *_ in COLOR_BANDS:
            raw = last_row.get(col, "").strip()
            if raw.lower() in ("", "nan", "-nan", "inf", "-inf"):
                band_values[col] = None
            else:
                try:
                    v = float(raw)
                    band_values[col] = v if _is_valid(v) else None
                except ValueError:
                    band_values[col] = None

        spectrum = _build_spectrum(band_values)
        organic_pct = self._read_organic_pct()
        biosignatures = _detect_biosignatures_csv(
            has_organics=any(v is not None for v in band_values.values()),
            organic_pct=organic_pct,
        )

        return {**spectrum, "biosignatures": biosignatures}

    def _read_organic_pct(self) -> Optional[float]:
        if not self._organic_csv or not os.path.exists(self._organic_csv):
            return None
        try:
            last_row: Optional[Dict[str, str]] = None
            with open(self._organic_csv, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    last_row = row
            if last_row is None:
                return None
            for key in ("organic_pct", "organic_percent", "organic"):
                raw = last_row.get(key, "").strip()
                if raw:
                    v = float(raw)
                    return v if _is_valid(v) else None
        except Exception:
            pass
        return None

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        return {
            "wavelengths": [],
            "intensities": [],
            "peak_wavelengths": [],
            "peak_intensities": [],
            "biosignatures": _detect_biosignatures_csv(False, None),
        }


# ── Biosignature helpers ───────────────────────────────────────────────────────

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
        "organic_pct": None,
        "confidence": confidence,
        "interpretation": interpretation,
    }


ORGANIC_DETECTED_THRESHOLD = 50.0  # % — at or above this value organics are detected


def _detect_biosignatures_csv(
    has_organics: bool,
    organic_pct: Optional[float],
) -> Dict[str, Any]:
    """Biosignature result for CSV color spectrometer."""
    if organic_pct is not None and organic_pct >= ORGANIC_DETECTED_THRESHOLD:
        has_organics = True
    elif organic_pct is not None:
        has_organics = False

    if has_organics:
        confidence, interpretation = "low", "Organic signal detected"
    else:
        confidence, interpretation = "none", "No organic signal detected"

    return {
        "chlorophyll": False,
        "carotenoids": False,
        "organics": has_organics,
        "organic_pct": organic_pct,
        "confidence": confidence,
        "interpretation": interpretation,
    }
