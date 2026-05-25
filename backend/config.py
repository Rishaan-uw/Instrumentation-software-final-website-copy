"""Runtime configuration loaded from environment variables.

Defaults are picked so the backend boots usefully on a laptop with no
hardware attached. At competition the environment file overrides these
to point at real devices.
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
    cameras: str = ""

    # Pi robot service (actions + sensor sampling + CSV reads) on port 9001.
    robot_service_url: str = "http://127.0.0.1:9001"
    robot_service_token: str = ""
    robot_service_timeout: float = 10.0

    # Where SpectroscopyLogger writes sessions.
    log_dir: str = "spectroscopy_logs"

    # Path the SampleRunner reads raw 2D frames from in mock/dev mode.
    test_image_path: str = "test_spectrum.npy"

    # Streaming knobs - tune for the rover radio.
    camera_fps: int = 5
    camera_jpeg_quality: int = 70

    # Where the built React app lives. Served at "/".
    frontend_dist: str = "frontend/dist"

    # URL of the robot-side camera switching service (camera_service.py).
    cam_svc_url: str = ""

    # Shared token sent as X-Camera-Token header to the camera service.
    cam_svc_token: str = ""

    # Spectrometer source for SampleRunner session logging only.
    #   "mock"  – test_spectrum.npy
    #   "csv"   – legacy local CSV poller (not used for dashboard graph)
    spectrometer_source: str = "mock"

    @property
    def camera_specs(self) -> List[str]:
        return [s.strip() for s in self.cameras.split(",") if s.strip()]

    @property
    def auth_enabled(self) -> bool:
        return bool(self.token)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
