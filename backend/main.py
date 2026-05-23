"""FastAPI entry point.

Wires together:
  - config + system state + auth
  - chem source (mock or csv)
  - camera manager
  - spectrometer service + sample runner
  - all routers
  - the built React frontend (served from / when present)

Run on the rover:
  uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import actions, calibration, cameras, chem, control, sessions, spectrum
from .sources.camera import CameraManager
from .sources.chem import build_chem_source
from .sources.spectrometer import CsvColorSpectrometer, SpectrometerService
from .state import get_state
from .workers.sample_runner import SampleRunner


def _build_spectrometer(settings):
    if settings.spectrometer_source == "csv":
        return CsvColorSpectrometer(
            color_csv=settings.color_csv_path,
            organic_pct_csv=settings.organic_pct_csv_path,
        )
    return SpectrometerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    state = get_state()

    spectrometer = _build_spectrometer(settings)
    spectrometer.set_calibration([(p.pixel, p.wavelength_nm) for p in state.calibration])

    chem_source = build_chem_source(settings.chem_source)
    chem_source.start()

    camera_manager = CameraManager(settings.camera_specs)

    runner = SampleRunner(settings=settings, state=state, spectrometer=spectrometer)

    app.state.settings = settings
    app.state.system_state = state
    app.state.spectrometer = spectrometer
    app.state.chem_source = chem_source
    app.state.camera_manager = camera_manager
    app.state.runner = runner

    try:
        yield
    finally:
        runner.stop()
        chem_source.stop()
        camera_manager.release_all()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Husky Robotics Science API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS is permissive because operators typically open the page directly
    # from the Pi on the rover network. Tighten in production if needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(actions.router)
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
            "chem_source": settings.chem_source,
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
