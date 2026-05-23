"""Calibration get/set.

Updating calibration here changes both the live `SpectrometerService`
and the persisted `SystemState.calibration` so the next sample uses it.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..auth import require_token
from ..state import CalibrationPoint

router = APIRouter(prefix="/api/calibration", tags=["calibration"], dependencies=[Depends(require_token)])


class CalibrationPointIn(BaseModel):
    pixel: int = Field(ge=0)
    wavelength_nm: float = Field(gt=0)


class CalibrationIn(BaseModel):
    points: List[CalibrationPointIn]


@router.get("")
async def get_calibration(request: Request):
    state = request.app.state.system_state
    return state.snapshot()["calibration"]


@router.post("")
async def set_calibration(payload: CalibrationIn, request: Request):
    if len(payload.points) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="need at least 2 calibration points",
        )
    points = [CalibrationPoint(p.pixel, p.wavelength_nm) for p in payload.points]
    state = request.app.state.system_state
    spectrometer = request.app.state.spectrometer
    state.set_calibration(points)
    spectrometer.set_calibration([(p.pixel, p.wavelength_nm) for p in points])
    return {"ok": True, "calibration": state.snapshot()["calibration"]}
