"""
Signatures API Routes
Endpoints for fault signature management.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.deps import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SignatureResponse(BaseModel):
    """Fault signature."""
    id: int
    name: str
    description: str
    category: str
    associated_codes: str
    created_at: str


class CreateSignatureRequest(BaseModel):
    """Request to create a new fault signature."""
    name: str
    description: str
    category: str
    associated_codes: str = ""


class SignatureStatsResponse(BaseModel):
    """Signature database statistics."""
    total_signatures: int
    total_hashes: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[SignatureResponse])
async def list_signatures():
    """List all fault signatures."""
    db = get_db_manager()
    sigs = db.get_all_signatures()
    return [
        SignatureResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            category=s.category,
            associated_codes=s.associated_codes,
            created_at=s.created_at,
        )
        for s in sigs
    ]


@router.get("/stats", response_model=SignatureStatsResponse)
async def signature_stats():
    """Get signature database statistics."""
    db = get_db_manager()
    return SignatureStatsResponse(
        total_signatures=db.get_signature_count(),
        total_hashes=db.get_total_hash_count(),
    )


@router.get("/{signature_id}", response_model=SignatureResponse)
async def get_signature(signature_id: int):
    """Get a specific fault signature by ID."""
    db = get_db_manager()
    sig = db.get_signature_by_id(signature_id)
    if sig is None:
        raise HTTPException(status_code=404, detail="Signature not found")
    return SignatureResponse(
        id=sig.id,
        name=sig.name,
        description=sig.description,
        category=sig.category,
        associated_codes=sig.associated_codes,
        created_at=sig.created_at,
    )


@router.post("/", response_model=dict)
async def create_signature(request: CreateSignatureRequest):
    """Create a new fault signature."""
    db = get_db_manager()
    sig_id = db.add_fault_signature(
        name=request.name,
        description=request.description,
        category=request.category,
        associated_codes=request.associated_codes,
    )
    return {"signature_id": sig_id}


@router.delete("/{signature_id}")
async def delete_signature(signature_id: int):
    """Delete a fault signature and its hashes."""
    db = get_db_manager()
    sig = db.get_signature_by_id(signature_id)
    if sig is None:
        raise HTTPException(status_code=404, detail="Signature not found")
    db.delete_signature(signature_id)
    return {"deleted": True, "signature_id": signature_id}
