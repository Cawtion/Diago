"""
Diagnosis API Routes
Endpoints for running diagnostic analysis (audio + text).
"""

import base64
import io
import logging
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from api.deps import get_db_manager
from core.api import run_diagnosis, export_report
from core.feature_extraction import BehavioralContext

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class BehavioralContextRequest(BaseModel):
    """Behavioral context from the user."""
    rpm_dependency: bool = False
    speed_dependency: bool = False
    load_dependency: bool = False
    cold_only: bool = False
    occurs_at_idle: bool = False
    mechanical_localization: bool = False
    noise_character: str = "unknown"
    perceived_frequency: str = "unknown"
    intermittent: bool = False
    issue_duration: str = "unknown"
    vehicle_type: str = "unknown"
    mileage_range: str = "unknown"
    recent_maintenance: str = "unknown"


class TextDiagnosisRequest(BaseModel):
    """Request for text-only diagnosis."""
    symptoms: str = ""
    codes: list[str] = Field(default_factory=list)
    context: BehavioralContextRequest = Field(default_factory=BehavioralContextRequest)


class ClassScore(BaseModel):
    """A single mechanical class score."""
    class_name: str
    display_name: str
    score: float
    penalty: float


class DiagnosisResponse(BaseModel):
    """Response from the diagnosis endpoint."""
    top_class: str
    top_class_display: str
    confidence: str
    is_ambiguous: bool
    class_scores: list[ClassScore]
    fingerprint_count: int
    llm_narrative: Optional[str] = None
    report_text: str


class ReportRequest(BaseModel):
    """Request to generate a report from a previous diagnosis."""
    top_class: str
    confidence: str
    is_ambiguous: bool
    class_scores: dict[str, float]
    penalties_applied: dict[str, float]
    features: dict
    fingerprint_count: int = 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/text", response_model=DiagnosisResponse)
async def diagnose_text(request: TextDiagnosisRequest):
    """
    Run text-only diagnosis from symptoms, codes, and behavioral context.
    No audio required.
    """
    from core.diagnostic_engine import CLASS_DISPLAY_NAMES

    db = get_db_manager()

    ctx = BehavioralContext(
        rpm_dependency=request.context.rpm_dependency,
        speed_dependency=request.context.speed_dependency,
        load_dependency=request.context.load_dependency,
        cold_only=request.context.cold_only,
        occurs_at_idle=request.context.occurs_at_idle,
        mechanical_localization=request.context.mechanical_localization,
        noise_character=request.context.noise_character,
        perceived_frequency=request.context.perceived_frequency,
        intermittent=request.context.intermittent,
        issue_duration=request.context.issue_duration,
        vehicle_type=request.context.vehicle_type,
        mileage_range=request.context.mileage_range,
        recent_maintenance=request.context.recent_maintenance,
    )

    try:
        result = run_diagnosis(
            audio=None,
            sr=44100,
            codes=request.codes,
            symptoms=request.symptoms,
            context=ctx,
            db_manager=db,
        )
    except Exception as e:
        logger.error("Text diagnosis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    report_text = export_report(result)

    return DiagnosisResponse(
        top_class=result.top_class,
        top_class_display=CLASS_DISPLAY_NAMES.get(result.top_class, result.top_class),
        confidence=result.confidence,
        is_ambiguous=result.is_ambiguous,
        class_scores=[
            ClassScore(
                class_name=cls,
                display_name=CLASS_DISPLAY_NAMES.get(cls, cls),
                score=score,
                penalty=result.penalties_applied.get(cls, 0.0),
            )
            for cls, score in sorted(
                result.class_scores.items(), key=lambda x: x[1], reverse=True
            )
        ],
        fingerprint_count=result.fingerprint_count,
        llm_narrative=result.llm_narrative,
        report_text=report_text,
    )


@router.post("/audio", response_model=DiagnosisResponse)
async def diagnose_audio(
    audio_file: UploadFile = File(...),
    symptoms: str = Form(""),
    codes: str = Form(""),
):
    """
    Run audio diagnosis by uploading an audio file.
    Optionally include symptoms and trouble codes.
    """
    from core.diagnostic_engine import CLASS_DISPLAY_NAMES

    db = get_db_manager()

    # Load audio from uploaded file
    try:
        import soundfile as sf
        audio_bytes = await audio_file.read()
        audio_data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio file: {e}")

    code_list = [c.strip() for c in codes.split(",") if c.strip()]

    try:
        result = run_diagnosis(
            audio=audio_data,
            sr=sr,
            codes=code_list,
            symptoms=symptoms,
            db_manager=db,
        )
    except Exception as e:
        logger.error("Audio diagnosis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    report_text = export_report(result)

    return DiagnosisResponse(
        top_class=result.top_class,
        top_class_display=CLASS_DISPLAY_NAMES.get(result.top_class, result.top_class),
        confidence=result.confidence,
        is_ambiguous=result.is_ambiguous,
        class_scores=[
            ClassScore(
                class_name=cls,
                display_name=CLASS_DISPLAY_NAMES.get(cls, cls),
                score=score,
                penalty=result.penalties_applied.get(cls, 0.0),
            )
            for cls, score in sorted(
                result.class_scores.items(), key=lambda x: x[1], reverse=True
            )
        ],
        fingerprint_count=result.fingerprint_count,
        llm_narrative=result.llm_narrative,
        report_text=report_text,
    )
