"""Sensor sample + latest endpoints (proxied to robot service)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import require_token
from ..robot_client import RobotServiceError

router = APIRouter(prefix="/api/sensors", tags=["sensors"], dependencies=[Depends(require_token)])


def _client(request: Request):
    return request.app.state.robot_client


@router.get("")
def list_sensors(request: Request) -> list:
    try:
        return _client(request).list_sensors()
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/job/status")
def job_status(request: Request) -> dict:
    try:
        return _client(request).job_status()
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/{sensor_id}/sample")
def sample_sensor(sensor_id: str, request: Request) -> dict:
    try:
        return _client(request).start_sensor_sample(sensor_id)
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/{sensor_id}/latest")
def sensor_latest(sensor_id: str, request: Request) -> dict:
    try:
        payload = _client(request).sensor_latest_raw(sensor_id)
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
    if sensor_id == "temp_humidity":
        try:
            return {
                "status": "ok",
                "data": {
                    "timestamp": time.time(),
                    "temperature": float(data["temperature"]),
                    "humidity": float(data["humidity"]),
                },
            }
        except (KeyError, TypeError, ValueError):
            return {"status": "no_data"}

    return {"status": "ok", "data": {**data, "timestamp": time.time()}}
