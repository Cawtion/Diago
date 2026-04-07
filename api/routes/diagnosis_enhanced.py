"""
api/routes/diagnosis_enhanced.py
Register in api/main.py:
    from api.routes.diagnosis_enhanced import router as diagnosis_enhanced_router
    app.include_router(diagnosis_enhanced_router, prefix="/api/v1", tags=["diagnosis-enhanced"])
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.ultimate_diagnostic_engine import UltimateDiagnosticEngine, VehicleContext
from database.obd_code_manager import get_obd_manager
from database.tsb_manager import get_tsb_manager

router = APIRouter()
_engine: Optional[UltimateDiagnosticEngine] = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = UltimateDiagnosticEngine()
    return _engine


class AudioFeaturesIn(BaseModel):
    category:    str  = Field(..., example="engine")
    subcategory: str  = Field(..., example="misfire")
    is_anomaly:  bool = False
    features:    Dict[str, float] = Field(default_factory=dict)

class DiagnoseRequest(BaseModel):
    make:           str
    model:          str
    year:           int
    obd_codes:      List[str] = Field(default_factory=list)
    symptoms:       str = ""
    audio_features: Optional[AudioFeaturesIn] = None
    engine_code:    Optional[str] = None
    mileage:        Optional[int] = None
    vin:            Optional[str] = None

class TSBMatchOut(BaseModel):
    tsb_id: str; title: str; match_score: float
    make: str; model: str; years: str; reason: str

class DiagnoseResponse(BaseModel):
    primary_diagnosis: str; primary_confidence: float
    overall_confidence: float; reliability_level: str
    secondary_diagnoses: List[Dict[str, Any]]
    detected_patterns: List[Dict[str, Any]]
    tsb_matches: List[TSBMatchOut]
    recommended_tests: List[Dict[str, Any]]
    modality_contributions: Dict[str, float]
    explanation: str; needs_more_data: bool
    suggested_additional_inputs: List[str]

class OBDLookupResponse(BaseModel):
    code: str; description: str; category: str; severity: str
    system: str; symptoms: List[str]; common_causes: List[str]; related_codes: List[str]

class TSBSearchRequest(BaseModel):
    codes:    List[str] = Field(default_factory=list)
    symptoms: str = ""
    make:     Optional[str] = None
    model:    Optional[str] = None
    year:     Optional[int] = None


@router.post("/diagnose/enhanced", response_model=DiagnoseResponse)
def diagnose_enhanced(req: DiagnoseRequest):
    vehicle = VehicleContext(make=req.make, model=req.model, year=req.year,
                             engine_code=req.engine_code, mileage=req.mileage, vin=req.vin)
    audio = req.audio_features.dict() if req.audio_features else None
    result = _get_engine().diagnose(vehicle=vehicle, obd_codes=req.obd_codes or None,
                                    symptoms=req.symptoms or None, audio_features=audio)
    return DiagnoseResponse(
        primary_diagnosis=result.primary_diagnosis,
        primary_confidence=result.primary_confidence,
        overall_confidence=result.overall_confidence,
        reliability_level=result.reliability_level,
        secondary_diagnoses=result.secondary_diagnoses,
        detected_patterns=result.detected_patterns,
        tsb_matches=[TSBMatchOut(**m) for m in result.tsb_matches],
        recommended_tests=result.recommended_tests,
        modality_contributions=result.modality_contributions,
        explanation=result.explanation,
        needs_more_data=result.needs_more_data,
        suggested_additional_inputs=result.suggested_additional_inputs,
    )

@router.get("/obd/lookup/{code}", response_model=OBDLookupResponse)
def obd_lookup(code: str):
    info = get_obd_manager().lookup(code.upper())
    if not info:
        raise HTTPException(status_code=404, detail=f"OBD code {code.upper()} not found")
    return OBDLookupResponse(code=info.code, description=info.description,
        category=info.category, severity=info.severity, system=info.system,
        symptoms=info.symptoms, common_causes=info.common_causes, related_codes=info.related_codes)

@router.post("/obd/analyze")
def obd_analyze(codes: List[str]):
    if not codes:
        raise HTTPException(status_code=422, detail="Provide at least one code")
    return get_obd_manager().analyze_code_combination(codes)

@router.post("/tsb/search")
def tsb_search(req: TSBSearchRequest):
    matches = get_tsb_manager().search_comprehensive(
        codes=req.codes or None, symptoms=req.symptoms or None,
        vehicle_make=req.make, vehicle_model=req.model, vehicle_year=req.year)
    return [{'tsb_id': m.tsb.tsb_id, 'title': m.tsb.title,
              'match_score': round(m.match_score, 3), 'make': m.tsb.make,
              'model': m.tsb.model, 'years': f"{m.tsb.year_start}–{m.tsb.year_end}",
              'systems': m.tsb.systems, 'root_cause': m.tsb.root_cause,
              'labor_hours': m.tsb.labor_hours, 'reason': m.reason}
             for m in matches[:10]]

@router.get("/tsb/{tsb_id}")
def tsb_detail(tsb_id: str):
    tsb = get_tsb_manager().get_tsb_by_id(tsb_id)
    if not tsb:
        raise HTTPException(status_code=404, detail=f"TSB {tsb_id} not found")
    from dataclasses import asdict
    return asdict(tsb)