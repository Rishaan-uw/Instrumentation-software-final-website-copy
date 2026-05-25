"""Organic analysis — formatted from robot color_read sensor."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import require_token
from ..robot_client import RobotServiceError

router = APIRouter(prefix="/api/chem", tags=["chem"], dependencies=[Depends(require_token)])

ORGANIC_DETECTED_THRESHOLD = 50.0


@router.get("/latest")
async def latest(request: Request):
    client = request.app.state.robot_client
    try:
        payload = client.sensor_latest_raw("color_read")
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Robot service unreachable",
        )

    if payload.get("status") != "ok":
        return {"status": "no_data"}

    data = payload.get("data") or {}
    try:
        pct_diff = float(data["pct_diff"])
    except (KeyError, TypeError, ValueError):
        return {"status": "no_data"}

    organics_detected = pct_diff >= ORGANIC_DETECTED_THRESHOLD
    return {
        "status": "ok",
        "data": {
            "timestamp": time.time(),
            "pct_diff": pct_diff,
            "organics_detected": organics_detected,
            "interpretation": (
                "Organic signal detected" if organics_detected else "No organic signal detected"
            ),
        },
    }
