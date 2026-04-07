"""
Ultimate Diagnostic Engine - Multi-Modal Fusion for Diago
Place at: core/ultimate_diagnostic_engine.py
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from database.obd_code_manager import OBDCodeManager, get_obd_manager
from database.tsb_manager import TSBManager, TSBMatch, get_tsb_manager


@dataclass
class VehicleContext:
    make: str
    model: str
    year: int
    engine_code: str = None
    mileage: int = None
    vin: str = None


@dataclass
class ModalityResult:
    modality: str
    diagnosis: str
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)
    raw_data: Any = None


@dataclass
class FusedDiagnosis:
    primary_diagnosis: str
    primary_confidence: float
    secondary_diagnoses: List[Dict[str, Any]]
    overall_confidence: float
    reliability_level: str
    modality_contributions: Dict[str, float]
    detected_patterns: List[Dict]
    tsb_matches: List[Dict]
    recommended_tests: List[Dict]
    explanation: str
    needs_more_data: bool
    suggested_additional_inputs: List[str]


class UltimateDiagnosticEngine:
    RELIABILITY_LEVELS = {
        (0.98, 1.01): "EXCELLENT - Proceed with recommended repair",
        (0.95, 0.98): "VERY HIGH - Highly likely correct, minimal verification needed",
        (0.90, 0.95): "HIGH - Likely correct, recommend confirmation test",
        (0.85, 0.90): "MODERATE - Possible diagnosis, verification recommended",
        (0.70, 0.85): "LOW - Multiple possibilities, additional testing needed",
        (0.00, 0.70): "INSUFFICIENT - Cannot determine, more data required",
    }

    BASE_WEIGHTS = {
        'obd_codes': 0.35,
        'tsb':       0.25,
        'audio':     0.20,
        'symptoms':  0.15,
        'live_data': 0.05,
    }

    def __init__(self, obd_manager=None, tsb_manager=None):
        self.obd_manager = obd_manager or get_obd_manager()
        self.tsb_manager = tsb_manager or get_tsb_manager()

    def diagnose(self, vehicle: VehicleContext, obd_codes=None,
                 symptoms=None, audio_features=None, live_data=None) -> FusedDiagnosis:
        modality_results = []
        if obd_codes:
            modality_results.append(self._process_obd_codes(obd_codes))
        if symptoms:
            modality_results.append(self._process_symptoms(symptoms, vehicle))
        if audio_features:
            modality_results.append(self._process_audio(audio_features))

        tsb_matches = self._search_tsbs(obd_codes, symptoms, vehicle)
        fused       = self._fuse_modalities(modality_results, tsb_matches)
        confidence  = self._calculate_confidence(fused, modality_results, tsb_matches)
        tests       = self._generate_test_sequence(obd_codes or [])
        needs_more  = confidence['overall'] < 0.85
        suggested   = self._suggest_additional_inputs(confidence, modality_results)

        return FusedDiagnosis(
            primary_diagnosis=fused['primary'],
            primary_confidence=fused['confidence'],
            secondary_diagnoses=fused['secondary'],
            overall_confidence=confidence['overall'],
            reliability_level=confidence['level'],
            modality_contributions=confidence['contributions'],
            detected_patterns=fused.get('patterns', []),
            tsb_matches=[self._tsb_match_to_dict(m) for m in tsb_matches[:3]],
            recommended_tests=tests,
            explanation=confidence['explanation'],
            needs_more_data=needs_more,
            suggested_additional_inputs=suggested,
        )

    def _process_obd_codes(self, codes):
        analysis = self.obd_manager.analyze_code_combination(codes)
        patterns = analysis.get('detected_patterns', [])
        if patterns:
            diagnosis, confidence = patterns[0]['description'], patterns[0]['confidence']
        else:
            infos = self.obd_manager.lookup_multiple(codes)
            if infos:
                diagnosis, confidence = next(iter(infos.values())).description, 0.60
            else:
                diagnosis, confidence = "Unknown fault", 0.30
        return ModalityResult(modality='obd_codes', diagnosis=diagnosis,
                              confidence=confidence, details=analysis, raw_data=codes)

    def _process_symptoms(self, symptoms, vehicle):
        matching_codes = self.obd_manager.search_by_symptom(symptoms)
        tsb_hits = self.tsb_manager.search_by_symptoms(symptoms, vehicle.make, vehicle.model, vehicle.year)
        if matching_codes:
            diagnosis, confidence = f"Possible issue: {matching_codes[0].description}", 0.50
        elif tsb_hits:
            diagnosis, confidence = f"Possible issue: {tsb_hits[0].tsb.title}", 0.45
        else:
            diagnosis, confidence = "Symptoms require further investigation", 0.30
        return ModalityResult(modality='symptoms', diagnosis=diagnosis, confidence=confidence,
            details={'matching_codes': [c.code for c in matching_codes[:5]],
                     'matching_tsbs': [m.tsb.tsb_id for m in tsb_hits[:3]]}, raw_data=symptoms)

    def _process_audio(self, audio_features):
        category    = audio_features.get('category', 'unknown')
        subcategory = audio_features.get('subcategory', 'unknown')
        is_anomaly  = audio_features.get('is_anomaly', False)
        if is_anomaly:
            diagnosis, confidence = f"Detected {subcategory.replace('_',' ')} in {category}", 0.75
        else:
            diagnosis, confidence = f"{category.replace('_',' ').title()} sounds normal", 0.80
        return ModalityResult(modality='audio', diagnosis=diagnosis, confidence=confidence,
            details={'category': category, 'subcategory': subcategory,
                     'features': audio_features.get('features', {})}, raw_data=audio_features)

    def _search_tsbs(self, codes, symptoms, vehicle):
        return self.tsb_manager.search_comprehensive(
            codes=codes, symptoms=symptoms,
            vehicle_make=vehicle.make, vehicle_model=vehicle.model, vehicle_year=vehicle.year)

    def _fuse_modalities(self, modality_results, tsb_matches):
        weights = self._dynamic_weights(modality_results)
        diag_scores: Dict[str, float] = defaultdict(float)
        diag_sources: Dict[str, list] = defaultdict(list)
        for r in modality_results:
            w = weights.get(r.modality, 0.2)
            diag_scores[r.diagnosis] += r.confidence * w
            diag_sources[r.diagnosis].append(r.modality)
        for m in tsb_matches[:3]:
            key = m.tsb.title
            diag_scores[key] += m.match_score * weights.get('tsb', 0.2)
            diag_sources[key].append('tsb')
        sorted_diags = sorted(diag_scores.items(), key=lambda x: x[1], reverse=True)
        patterns = []
        for r in modality_results:
            if r.modality == 'obd_codes':
                patterns.extend(r.details.get('detected_patterns', []))
        return {
            'primary':    sorted_diags[0][0] if sorted_diags else "Unknown",
            'confidence': sorted_diags[0][1] if sorted_diags else 0.0,
            'secondary':  [{'diagnosis': d, 'score': s, 'sources': diag_sources[d]}
                           for d, s in sorted_diags[1:4]],
            'patterns':   patterns,
        }

    def _dynamic_weights(self, modality_results):
        weights = dict(self.BASE_WEIGHTS)
        for r in modality_results:
            if r.confidence > 0.80:
                weights[r.modality] = min(weights[r.modality] * 1.3, 0.45)
            elif r.confidence < 0.50:
                weights[r.modality] *= 0.70
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()} if total else weights

    def _calculate_confidence(self, fused, modality_results, tsb_matches):
        base = fused['confidence']
        agreement_boost = 0.05 if self._modalities_agree(modality_results) else 0.0
        tsb_boost = 0.05 if tsb_matches and tsb_matches[0].match_score > 0.70 else 0.0
        overall = min(base + agreement_boost + tsb_boost, 1.0)
        contributions = {r.modality: r.confidence for r in modality_results}
        if tsb_matches:
            contributions['tsb'] = tsb_matches[0].match_score
        return {
            'overall': overall, 'base': base,
            'level': self._reliability_label(overall),
            'contributions': contributions,
            'explanation': self._explanation(fused, modality_results, tsb_matches),
        }

    def _modalities_agree(self, results):
        if len(results) < 2: return True
        diags = [r.diagnosis.lower() for r in results if r.confidence > 0.5]
        if len(diags) >= 2:
            return len(set(diags[0].split()) & set(diags[1].split())) >= 2
        return False

    def _reliability_label(self, confidence):
        for (lo, hi), label in self.RELIABILITY_LEVELS.items():
            if lo <= confidence < hi:
                return label
        return "UNKNOWN"

    def _explanation(self, fused, modality_results, tsb_matches):
        parts = [f"Primary diagnosis: {fused['primary']}"]
        mods = [r.modality for r in modality_results if r.confidence > 0.5]
        if mods: parts.append(f"Based on: {', '.join(mods)}")
        if tsb_matches and tsb_matches[0].match_score > 0.5:
            parts.append(f"TSB match: {tsb_matches[0].tsb.tsb_id} — {tsb_matches[0].tsb.title}")
        if fused.get('patterns'):
            parts.append(f"Patterns: {'; '.join(p['description'] for p in fused['patterns'][:2])}")
        return " | ".join(parts)

    def _generate_test_sequence(self, codes):
        tests = self.obd_manager.get_test_sequence(codes) if codes else []
        if not tests:
            tests.append({'priority': 'HIGH', 'test': 'Visual inspection of related components',
                          'focus': 'Look for obvious damage, leaks, or disconnected hoses'})
        return tests[:5]

    def _suggest_additional_inputs(self, confidence, modality_results):
        if confidence['overall'] >= 0.85: return []
        existing = {r.modality for r in modality_results}
        suggestions = []
        if 'obd_codes' not in existing: suggestions.append("Scan for OBD trouble codes")
        if 'audio'     not in existing: suggestions.append("Record audio of the issue")
        if 'symptoms'  not in existing: suggestions.append("Provide a detailed symptom description")
        if 'live_data' not in existing: suggestions.append("Capture live sensor data")
        return suggestions

    @staticmethod
    def _tsb_match_to_dict(match):
        return {
            'tsb_id': match.tsb.tsb_id, 'title': match.tsb.title,
            'match_score': match.match_score, 'make': match.tsb.make,
            'model': match.tsb.model, 'years': f"{match.tsb.year_start}–{match.tsb.year_end}",
            'reason': match.reason,
        }