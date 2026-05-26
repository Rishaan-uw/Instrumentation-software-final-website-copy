"""Robot action endpoints — proxied to Pi robot service on port 9001."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ..auth import require_token
from ..robot_client import RobotServiceError

router = APIRouter(
    prefix="/api/actions",
    tags=["actions"],
    dependencies=[Depends(require_token)],
)


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
def list_actions(request: Request) -> list:
    try:
        return _client(request).list_actions()
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/{action_id}")
def start_action(action_id: str, request: Request, body: StartRequest | None = None) -> dict:
    camera_device = _validated_camera_device(body.camera_device if body else None)
    forward_device = camera_device if action_id == "calibrate_spectrometer" else None
    try:
        return _client(request).start_action(action_id, camera_device=forward_device)
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/{action_id}/status")
def action_status(action_id: str, request: Request) -> dict:
    try:
        return _client(request).action_status(action_id)
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
