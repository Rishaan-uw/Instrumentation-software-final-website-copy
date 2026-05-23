"""Color read test endpoints backed by colorReadTest.csv."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..auth import require_token

router = APIRouter(prefix="/api/chem", tags=["chem"], dependencies=[Depends(require_token)])


@router.get("/latest")
async def latest(request: Request):
    chem = request.app.state.chem_source
    reading = chem.latest()
    if reading is None:
        return {"status": "no_data"}
    return {"status": "ok", "data": reading}
