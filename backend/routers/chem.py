"""Chem endpoints backed by the configured ChemSource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ..auth import require_token

router = APIRouter(prefix="/api/chem", tags=["chem"], dependencies=[Depends(require_token)])


@router.get("/latest")
async def latest(request: Request):
    chem = request.app.state.chem_source
    reading = chem.latest()
    if reading is None:
        return {"status": "no_data"}
    return {"status": "ok", "data": reading}


@router.get("/history")
async def history(request: Request, minutes: int = Query(5, ge=1, le=60)):
    chem = request.app.state.chem_source
    return {"status": "ok", "data": chem.history(minutes=minutes)}
