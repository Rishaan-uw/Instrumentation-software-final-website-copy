"""Sessions browser + zip export.

Reads from the directory layout written by `datalogger.SpectroscopyLogger`:
  spectroscopy_logs/session_<id>/session_log.json
  spectroscopy_logs/session_<id>/spectra/
  spectroscopy_logs/session_<id>/images/
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from ..auth import require_token

router = APIRouter(prefix="/api/sessions", tags=["sessions"], dependencies=[Depends(require_token)])


def _log_dir(request: Request) -> str:
    return request.app.state.settings.log_dir


def _session_path(log_dir: str, session_id: str) -> str:
    return os.path.join(log_dir, f"session_{session_id}")


@router.get("")
async def list_sessions(request: Request) -> Dict[str, Any]:
    log_dir = _log_dir(request)
    if not os.path.isdir(log_dir):
        return {"sessions": []}

    sessions: List[Dict[str, Any]] = []
    for entry in sorted(os.listdir(log_dir), reverse=True):
        if not entry.startswith("session_"):
            continue
        log_file = os.path.join(log_dir, entry, "session_log.json")
        if not os.path.exists(log_file):
            continue
        try:
            with open(log_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        sessions.append(
            {
                "session_id": data.get("session_id", entry.removeprefix("session_")),
                "start_time": data.get("start_time"),
                "end_time": data.get("end_time"),
                "measurement_count": len(data.get("measurements", [])),
            }
        )
    return {"sessions": sessions}


@router.get("/{session_id}")
async def get_session(session_id: str, request: Request) -> Dict[str, Any]:
    log_file = os.path.join(_session_path(_log_dir(request), session_id), "session_log.json")
    if not os.path.exists(log_file):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    with open(log_file) as f:
        return json.load(f)


@router.get("/{session_id}/export")
async def export_session(session_id: str, request: Request) -> StreamingResponse:
    session_dir = _session_path(_log_dir(request), session_id)
    if not os.path.isdir(session_dir):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(session_dir):
            for name in files:
                full = os.path.join(root, name)
                arcname = os.path.relpath(full, session_dir)
                zf.write(full, arcname)
    buffer.seek(0)

    headers = {"Content-Disposition": f'attachment; filename="session_{session_id}.zip"'}
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)
