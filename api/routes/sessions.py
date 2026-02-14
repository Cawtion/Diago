"""
Sessions API Routes
Endpoints for analysis session CRUD.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.deps import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SessionResponse(BaseModel):
    """Analysis session."""
    id: int
    timestamp: str
    audio_path: str
    user_codes: str
    notes: str
    duration_seconds: float


class SessionMatchResponse(BaseModel):
    """Match result for a session."""
    fault_name: str
    confidence_pct: float
    trouble_codes: str
    description: str
    category: str
    signature_id: int


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    audio_path: str = ""
    user_codes: str = ""
    notes: str = ""
    duration_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[SessionResponse])
async def list_sessions(limit: int = 50):
    """Retrieve recent analysis sessions."""
    db = get_db_manager()
    sessions = db.get_session_history(limit)
    return [
        SessionResponse(
            id=s.id,
            timestamp=s.timestamp,
            audio_path=s.audio_path,
            user_codes=s.user_codes,
            notes=s.notes,
            duration_seconds=s.duration_seconds,
        )
        for s in sessions
    ]


@router.post("/", response_model=dict)
async def create_session(request: CreateSessionRequest):
    """Create a new analysis session."""
    db = get_db_manager()
    session_id = db.create_session(
        audio_path=request.audio_path,
        user_codes=request.user_codes,
        notes=request.notes,
        duration_seconds=request.duration_seconds,
    )
    return {"session_id": session_id}


@router.get("/{session_id}/matches", response_model=list[SessionMatchResponse])
async def get_session_matches(session_id: int):
    """Get match results for a specific session."""
    db = get_db_manager()
    matches = db.get_session_matches(session_id)
    return [
        SessionMatchResponse(
            fault_name=m.fault_name,
            confidence_pct=m.confidence_pct,
            trouble_codes=m.trouble_codes,
            description=m.description,
            category=m.category,
            signature_id=m.signature_id,
        )
        for m in matches
    ]


@router.delete("/{session_id}")
async def delete_session(session_id: int):
    """Delete an analysis session."""
    db = get_db_manager()
    db.delete_session(session_id)
    return {"deleted": True, "session_id": session_id}
