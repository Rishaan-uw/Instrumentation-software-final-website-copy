"""Robot action endpoints — proxied to Pi robot service on port 9001."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import require_token
from ..robot_client import RobotServiceError

router = APIRouter(
    prefix="/api/actions",
    tags=["actions"],
    dependencies=[Depends(require_token)],
)


def _client(request: Request):
    return request.app.state.robot_client


@router.get("")
def list_actions(request: Request) -> list:
    try:
        return _client(request).list_actions()
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/{action_id}")
def start_action(action_id: str, request: Request) -> dict:
    try:
        return _client(request).start_action(action_id)
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/{action_id}/status")
def action_status(action_id: str, request: Request) -> dict:
    try:
        return _client(request).action_status(action_id)
    except RobotServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
