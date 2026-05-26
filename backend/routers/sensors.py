"""Sensor sample + latest endpoints (proxied to robot service)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ..auth import require_token
from ..robot_client import RobotServiceError

router = APIRouter(prefix="/api/sensors", tags=["sensors"], dependencies=[Depends(require_token)])


def _client(request: Request):
    return request.app.state.robot_client


VALID_CAMERA_DEVICES = {"/dev/video0", "/dev/video2", "/dev/video4"}


class StartRequest(BaseModel):
    camera_device: str | None = None


def _validated_camera_device(value: str | None) -> str:
    if value is None:
        return "/dev/video0"
    if value not in VALID_CAMERA_DEVICES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid camera_device")
    return value


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
def sample_sensor(sensor_id: str, request: Request, body: StartRequest | None = None) -> dict:
    camera_device = _validated_camera_device(body.camera_device if body else None)
    forward_device = camera_device if sensor_id == "peaks_colors" else None
    try:
        return _client(request).start_sensor_sample(sensor_id, camera_device=forward_device)
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
