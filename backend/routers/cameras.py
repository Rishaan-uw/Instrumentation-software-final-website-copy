"""Camera listing, MJPEG stream, snapshot, and robot camera-switcher endpoints."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse

from ..auth import require_token_for_cameras

router = APIRouter(
    prefix="/api/cameras",
    tags=["cameras"],
    dependencies=[Depends(require_token_for_cameras)],
)


# ── Helper: forward a request to the robot camera service ─────────────────────

async def _cam_svc_post(request: Request, path: str) -> dict:
    """POST to camera_service.py on the rover and return its JSON response."""
    settings = request.app.state.settings
    base = settings.cam_svc_url.rstrip("/")
    if not base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Camera switching service not configured (HUSKY_CAM_SVC_URL is empty).",
        )
    headers = {}
    if settings.cam_svc_token:
        headers["X-Camera-Token"] = settings.cam_svc_token
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(f"{base}{path}", headers=headers)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Camera service unreachable: {exc}",
        )


@router.get("")
async def list_cameras(request: Request):
    manager = request.app.state.camera_manager
    return {"cameras": [c.__dict__ for c in manager.list()]}


@router.get("/{cam_id}/snapshot")
async def snapshot(cam_id: str, request: Request):
    manager = request.app.state.camera_manager
    cam = manager.get(cam_id)
    if cam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown camera")
    settings = request.app.state.settings
    jpeg = cam.read_jpeg(quality=settings.camera_jpeg_quality)
    return Response(content=jpeg, media_type="image/jpeg")


@router.get("/{cam_id}/stream")
async def stream(cam_id: str, request: Request):
    manager = request.app.state.camera_manager
    cam = manager.get(cam_id)
    if cam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown camera")
    settings = request.app.state.settings
    media_type, body = cam.mjpeg_stream(settings.camera_fps, settings.camera_jpeg_quality)
    return StreamingResponse(body, media_type=media_type)


# ── Robot camera switcher ──────────────────────────────────────────────────────

@router.post("/{camera_id}/activate")
async def activate_camera(camera_id: str, request: Request):
    """Tell the rover camera service to switch to the given camera.

    camera_id must be one of the IDs registered in camera_service.py on the rover
    (e.g. "fov" or "arm").  The MJPEG stream URL stays the same; only the physical
    device behind it changes.
    """
    return await _cam_svc_post(request, f"/camera/{camera_id}/activate")


@router.post("/stop")
async def stop_camera(request: Request):
    """Stop whichever camera is currently streaming on the rover."""
    return await _cam_svc_post(request, "/camera/stop")


@router.get("/switcher/status")
async def switcher_status(request: Request):
    """Return the rover camera service status (active camera, stream URL)."""
    settings = request.app.state.settings
    base = settings.cam_svc_url.rstrip("/")
    if not base:
        return {"configured": False}
    headers = {}
    if settings.cam_svc_token:
        headers["X-Camera-Token"] = settings.cam_svc_token
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{base}/camera/status", headers=headers)
            resp.raise_for_status()
            return {"configured": True, **resp.json()}
    except Exception as exc:
        return {"configured": True, "error": str(exc)}
