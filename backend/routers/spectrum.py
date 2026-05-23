"""Spectrum endpoints. Frontend SpectrumChart polls /api/spectrum/latest."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import require_token

router = APIRouter(prefix="/api/spectrum", tags=["spectrum"], dependencies=[Depends(require_token)])


@router.get("/latest")
async def latest(request: Request):
    settings = request.app.state.settings

    # If a Pi spectrum API URL is configured, proxy it directly.
    if settings.spectrum_api_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(settings.spectrum_api_url)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Spectrum API error: {exc.response.text}",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Spectrum API unreachable: {exc}",
            )

    # Default: read from local in-memory state (populated by SampleRunner).
    state = request.app.state.system_state
    payload = state.get_latest_spectrum()
    if payload is None:
        return {"status": "no_data"}
    return {"status": "ok", "data": payload}
