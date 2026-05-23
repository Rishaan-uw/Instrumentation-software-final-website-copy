"""Spectrum endpoints. Frontend SpectrumChart polls /api/spectrum/latest."""

from __future__ import annotations

import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import require_token

router = APIRouter(prefix="/api/spectrum", tags=["spectrum"], dependencies=[Depends(require_token)])


def _live_csv_payload(request: Request) -> dict | None:
    """Return the latest peaks_colors spectrometer data from the Pi CSV poller."""
    result = request.app.state.spectrometer.analyze(None)
    if not result.get("wavelengths"):
        return None
    return {
        "sample_id": "live",
        "timestamp": time.time(),
        **result,
    }


@router.get("/latest")
async def latest(request: Request):
    settings = request.app.state.settings

    # Production: read peaks_colors.csv from the Pi.
    if settings.spectrometer_source == "csv":
        payload = _live_csv_payload(request)
        if payload is None:
            return {"status": "no_data"}
        return {"status": "ok", "data": payload}

    # Optional remote proxy for deployments that expose spectrum over HTTP.
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

    # Dev mock mode: last sample captured by SampleRunner.
    state = request.app.state.system_state
    payload = state.get_latest_spectrum()
    if payload is None:
        return {"status": "no_data"}
    return {"status": "ok", "data": payload}
