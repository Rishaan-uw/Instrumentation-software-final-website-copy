"""Spectrometer graph — formatted from robot peaks_colors sensor."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import require_token
from ..robot_client import RobotServiceError

router = APIRouter(prefix="/api/spectrum", tags=["spectrum"], dependencies=[Depends(require_token)])

COLOR_ORDER = ["Blue", "Cyan", "Green", "Yellow", "Orange", "Red"]
MIDPOINTS = [472.5, 492.5, 532.5, 580.0, 605.0, 685.0]


@router.get("/latest")
async def latest(request: Request):
    client = request.app.state.robot_client
    try:
        payload = client.sensor_latest_raw("peaks_colors")
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Robot service unreachable",
        )

    if payload.get("status") != "ok":
        return {"status": "no_data"}

    raw = payload.get("data") or {}
    peaks = raw.get("peaks") or raw
    intensities = []
    for color in COLOR_ORDER:
        try:
            intensities.append(float(peaks[color]))
        except (KeyError, TypeError, ValueError):
            return {"status": "no_data"}

    return {
        "status": "ok",
        "data": {
            "sample_id": "csv-live",
            "timestamp": time.time(),
            "wavelengths": MIDPOINTS,
            "intensities": intensities,
            "peak_wavelengths": MIDPOINTS,
            "peak_intensities": intensities,
        },
    }
