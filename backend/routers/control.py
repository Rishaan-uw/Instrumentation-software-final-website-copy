"""Control + status endpoints.

The frontend's ControlBar talks to this router.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import require_token

router = APIRouter(prefix="/api", tags=["control"], dependencies=[Depends(require_token)])


def _runner(request: Request):
    return request.app.state.runner


def _state(request: Request):
    return request.app.state.system_state


@router.get("/status")
async def get_status(request: Request):
    return _state(request).snapshot()


async def _activate_default_camera(request: Request) -> None:
    """Fire-and-forget: ask the rover camera service to start the FOV camera.

    Failures are logged but do not block the science session from starting —
    the operator can switch cameras manually from the UI.
    """
    settings = request.app.state.settings
    base = settings.cam_svc_url.rstrip("/")
    if not base:
        return
    headers = {}
    if settings.cam_svc_token:
        headers["X-Camera-Token"] = settings.cam_svc_token
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{base}/camera/video0/activate", headers=headers)
    except Exception:
        pass  # camera switching is best-effort; science session still starts


@router.post("/start")
async def start(request: Request):
    try:
        session_id = _runner(request).start()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    await _activate_default_camera(request)
    return {"ok": True, "session_id": session_id}


@router.post("/stop")
async def stop(request: Request):
    _runner(request).stop()
    return {"ok": True}


@router.post("/sample")
async def take_sample(request: Request):
    try:
        sample_id = _runner(request).take_one()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    return {"ok": True, "sample_id": sample_id}
