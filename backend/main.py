"""FastAPI entry point.

Run on the base station / laptop (not on the Pi):
  uvicorn backend.main:app --host 127.0.0.1 --port 8000

Pi robot service (port 9001):
  uvicorn robot_service:app --host 0.0.0.0 --port 9001
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .robot_client import get_robot_client
from .routers import actions, calibration, cameras, chem, control, sensors, sessions, spectrum
from .sources.camera import CameraManager
from .sources.spectrometer import CsvColorSpectrometer, SpectrometerService
from .state import get_state
from .workers.sample_runner import SampleRunner


def _build_spectrometer(settings):
    if settings.spectrometer_source == "csv":
        return CsvColorSpectrometer(color_csv="/home/robot/HR-pi/output_data/peaks_colors.csv")
    return SpectrometerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    state = get_state()

    spectrometer = _build_spectrometer(settings)
    spectrometer.set_calibration([(p.pixel, p.wavelength_nm) for p in state.calibration])

    camera_manager = CameraManager(settings.camera_specs)
    runner = SampleRunner(settings=settings, state=state, spectrometer=spectrometer)
    robot_client = get_robot_client(settings)

    app.state.settings = settings
    app.state.system_state = state
    app.state.spectrometer = spectrometer
    app.state.camera_manager = camera_manager
    app.state.runner = runner
    app.state.robot_client = robot_client

    try:
        yield
    finally:
        runner.stop()
        camera_manager.release_all()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Husky Robotics Science API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(actions.router)
    app.include_router(sensors.router)
    app.include_router(control.router)
    app.include_router(spectrum.router)
    app.include_router(chem.router)
    app.include_router(cameras.router)
    app.include_router(sessions.router)
    app.include_router(calibration.router)

    @app.get("/api/health")
    async def health():
        return {"ok": True, "version": app.version}

    @app.get("/api/info")
    async def info():
        settings = app.state.settings
        return {
            "auth_enabled": settings.auth_enabled,
            "robot_service_url": settings.robot_service_url,
            "cameras": [c.__dict__ for c in app.state.camera_manager.list()],
        }

    _mount_frontend(app)

    return app


def _mount_frontend(app: FastAPI) -> None:
    settings = get_settings()
    dist = settings.frontend_dist
    if not os.path.isdir(dist):
        @app.get("/")
        async def _no_frontend():
            return JSONResponse(
                {
                    "message": (
                        "Frontend not built. Run `cd frontend && npm install && npm run build`, "
                        "or hit the API directly at /api/*"
                    )
                }
            )
        return

    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")


app = create_app()
