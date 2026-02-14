"""
Trouble Codes API Routes
Endpoints for OBD-II code lookup and search.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.deps import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class CodeResponse(BaseModel):
    """OBD-II trouble code definition."""
    code: str
    description: str
    system: str
    subsystem: str
    mechanical_classes: list[str]
    symptoms: list[str]
    severity: str


class CodeSearchResponse(BaseModel):
    """Search results for trouble codes."""
    query: str
    results: list[CodeResponse]
    count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _code_prefix_to_system(prefix: str) -> str:
    """Map OBD code prefix to system name."""
    return {"P": "powertrain", "B": "body", "C": "chassis", "U": "network"}.get(
        prefix.upper(), "unknown"
    )


@router.get("/lookup/{code}", response_model=CodeResponse)
async def lookup_code(code: str):
    """Look up a single OBD-II trouble code. Falls back to Car API if not in local DB."""
    from database.trouble_code_lookup import lookup_code as _lookup
    from api.services.car_api import get_obd_code as car_api_lookup

    db = get_db_manager()
    result = _lookup(code, db)
    if result is not None:
        return CodeResponse(
            code=result.code,
            description=result.description,
            system=result.system,
            subsystem=result.subsystem,
            mechanical_classes=result.mechanical_classes,
            symptoms=result.symptoms,
            severity=result.severity,
        )

    # Fallback: Car API (optional)
    external = car_api_lookup(code)
    if external:
        prefix = (code.strip().upper() + "X")[0]
        return CodeResponse(
            code=external["code"],
            description=external["description"],
            system=_code_prefix_to_system(prefix),
            subsystem="",
            mechanical_classes=[],
            symptoms=[],
            severity="medium",
        )

    raise HTTPException(status_code=404, detail=f"Code {code} not found")


@router.get("/lookup", response_model=list[CodeResponse])
async def lookup_codes(codes: str = Query(..., description="Comma-separated codes")):
    """Look up multiple OBD-II trouble codes."""
    from database.trouble_code_lookup import lookup_codes as _lookup_many
    db = get_db_manager()
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    results = _lookup_many(code_list, db)
    return [
        CodeResponse(
            code=r.code,
            description=r.description,
            system=r.system,
            subsystem=r.subsystem,
            mechanical_classes=r.mechanical_classes,
            symptoms=r.symptoms,
            severity=r.severity,
        )
        for r in results
    ]


@router.get("/search", response_model=CodeSearchResponse)
async def search_codes(q: str = Query(..., min_length=1)):
    """Free-text search across trouble code definitions."""
    from database.trouble_code_lookup import search_codes as _search
    db = get_db_manager()
    results = _search(q, db)
    return CodeSearchResponse(
        query=q,
        results=[
            CodeResponse(
                code=r.code,
                description=r.description,
                system=r.system,
                subsystem=r.subsystem,
                mechanical_classes=r.mechanical_classes,
                symptoms=r.symptoms,
                severity=r.severity,
            )
            for r in results
        ],
        count=len(results),
    )


@router.get("/symptoms", response_model=list[CodeResponse])
async def suggest_by_symptoms(
    keywords: str = Query(..., description="Comma-separated symptom keywords"),
):
    """Find codes matching symptom keywords."""
    from database.trouble_code_lookup import suggest_codes_for_symptoms
    db = get_db_manager()
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    results = suggest_codes_for_symptoms(kw_list, db)
    return [
        CodeResponse(
            code=r.code,
            description=r.description,
            system=r.system,
            subsystem=r.subsystem,
            mechanical_classes=r.mechanical_classes,
            symptoms=r.symptoms,
            severity=r.severity,
        )
        for r in results
    ]
