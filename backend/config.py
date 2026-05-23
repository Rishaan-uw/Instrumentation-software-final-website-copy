"""Runtime configuration loaded from environment variables.

Defaults are picked so the backend boots usefully on a laptop with no
hardware attached (mock chem source, no cameras). At competition the
environment file overrides these to point at real devices.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root (parent of ``backend/``) so ``camera.env`` loads even if cwd is elsewhere.
_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILES = tuple(str(_ROOT / name) for name in (".env", "camera.env"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HUSKY_",
        env_file=_ENV_FILES,
        extra="ignore",
    )

    # Single shared bearer token. Empty string disables auth (dev only).
    token: str = ""

    # Comma-separated camera device specs. Each entry can be a numeric
    # index ("0"), a /dev path ("/dev/video2"), or "name:index" / "name:/dev/...".
    # Examples:
    #   HUSKY_CAMERAS="microscope:0,overview:1"
    #   HUSKY_CAMERAS="0"
    cameras: str = ""

    # Selects the chem data source.
    #   "mock"            - synthetic plausible readings (default)
    #   "csv:/path/file"  - tail a CSV that an instrument writes
    chem_source: str = "mock"

    # Where SpectroscopyLogger writes sessions.
    log_dir: str = "spectroscopy_logs"

    # Path the SampleRunner reads raw 2D frames from in mock/dev mode.
    # In production this is replaced by a real sensor driver.
    test_image_path: str = "test_spectrum.npy"

    # Streaming knobs - tune for the rover radio.
    camera_fps: int = 5
    camera_jpeg_quality: int = 70

    # Where the built React app lives. Served at "/".
    frontend_dist: str = "frontend/dist"

    # URL of the robot-side camera switching service (camera_service.py).
    # Example: "http://100.80.12.52:9000"
    # Leave empty to disable camera switching.
    cam_svc_url: str = ""

    # Shared token sent as X-Camera-Token header to the camera service.
    # Must match CAMERA_SVC_TOKEN on the rover.  Leave empty to disable.
    cam_svc_token: str = ""

    # Spectrometer source.
    #   "mock"  – uses test_spectrum.npy (default, works without hardware)
    #   "csv"   – reads color-band CSV from the Pi (production)
    spectrometer_source: str = "mock"

    # Path to the color spectrometer CSV on the Pi.
    # Columns: Red,Orange,Yellow,Green,Cyan,Blue
    color_csv_path: str = "/home/robot/HR-pi/output_data/peaks_colors.csv"

    # Path to the organic percentage CSV on the Pi.
    # Must contain a column named "organic_pct" or "organic_percent".
    # Leave empty to disable organic_pct reading.
    organic_pct_csv_path: str = ""

    # If set, /api/spectrum/latest proxies this URL instead of reading local state.
    # Example: "http://100.80.12.52:9001/spectrum"
    spectrum_api_url: str = ""

    @property
    def camera_specs(self) -> List[str]:
        return [s.strip() for s in self.cameras.split(",") if s.strip()]

    @property
    def auth_enabled(self) -> bool:
        return bool(self.token)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
