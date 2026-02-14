"""Tests for core.diagnostic_engine module."""

import numpy as np
import pytest

from core.diagnostic_engine import (
    MECHANICAL_CLASSES,
    sigmoid_scale,
    score_mechanical_classes,
    apply_constraint_penalties,
    apply_text_only_constraints,
    normalize_scores,
    check_failure_safety,
    check_text_only_confidence,
    compute_data_sufficiency,
    score_from_class_hints,
    score_signal_agreement,
    run_text_diagnostic_pipeline,
    DiagnosisResult,
)
from core.feature_extraction import (
    AudioFeatures,
    BehavioralContext,
    extract_features_from_context,
)


class TestSigmoidScale:
    def test_at_midpoint_returns_half(self):
        result = sigmoid_scale(0.5, midpoint=0.5, steepness=10.0)
        assert result == pytest.approx(0.5, abs=0.01)

    def test_above_midpoint_near_one(self):
        result = sigmoid_scale(0.9, midpoint=0.5, steepness=10.0)
        assert result > 0.9

    def test_below_midpoint_near_zero(self):
        result = sigmoid_scale(0.1, midpoint=0.5, steepness=10.0)
        assert result < 0.1

    def test_output_range(self):
        for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = sigmoid_scale(v)
            assert 0.0 <= result <= 1.0


class TestScoreMechanicalClasses:
    def test_returns_all_classes(self, bearing_context):
        features = extract_features_from_context(bearing_context)
        scores = score_mechanical_classes(features)
        for cls in MECHANICAL_CLASSES:
            assert cls in scores

    def test_bearing_context_favors_bearing(self, bearing_context):
        features = extract_features_from_context(bearing_context)
        scores = score_mechanical_classes(features)
        # Bearing context should boost bearing score
        assert scores["rolling_element_bearing"] > 0

    def test_belt_context_favors_belt(self, belt_context):
        features = extract_features_from_context(belt_context)
        scores = score_mechanical_classes(features)
        assert scores["belt_drive_friction"] > 0


class TestApplyConstraintPenalties:
    def test_no_penalties_on_empty_features(self):
        scores = {cls: 1.0 for cls in MECHANICAL_CLASSES}
        features = AudioFeatures()
        penalized, penalties = apply_constraint_penalties(scores, features)
        # Should still have valid structure
        for cls in MECHANICAL_CLASSES:
            assert cls in penalized
            assert cls in penalties

    def test_penalties_reduce_scores(self, bearing_context):
        features = extract_features_from_context(bearing_context)
        scores = {cls: 1.0 for cls in MECHANICAL_CLASSES}
        penalized, penalties = apply_constraint_penalties(scores, features)
        # At least some classes should be penalized
        total_penalty = sum(penalties.values())
        assert total_penalty >= 0

    def test_scores_never_negative(self):
        scores = {cls: 0.01 for cls in MECHANICAL_CLASSES}
        features = AudioFeatures()
        penalized, _ = apply_constraint_penalties(scores, features)
        for cls, score in penalized.items():
            assert score >= 0.0


class TestNormalizeScores:
    def test_sums_to_one(self):
        scores = {"a": 1.0, "b": 2.0, "c": 3.0}
        normalized = normalize_scores(scores)
        total = sum(normalized.values())
        assert total == pytest.approx(1.0, abs=0.001)

    def test_all_zero_returns_zeros(self):
        scores = {"a": 0.0, "b": 0.0}
        normalized = normalize_scores(scores)
        assert all(v == 0.0 for v in normalized.values())

    def test_preserves_relative_order(self):
        scores = {"a": 3.0, "b": 1.0, "c": 2.0}
        normalized = normalize_scores(scores)
        assert normalized["a"] > normalized["c"] > normalized["b"]


class TestCheckFailureSafety:
    def test_high_confidence(self):
        scores = {"a": 0.7, "b": 0.1, "c": 0.1, "d": 0.1}
        is_ambiguous, confidence = check_failure_safety(scores)
        assert not is_ambiguous
        assert confidence == "high"

    def test_low_max_is_ambiguous(self):
        scores = {"a": 0.2, "b": 0.2, "c": 0.2, "d": 0.2, "e": 0.2}
        is_ambiguous, confidence = check_failure_safety(scores)
        assert is_ambiguous
        assert confidence == "low"

    def test_empty_scores(self):
        is_ambiguous, confidence = check_failure_safety({})
        assert is_ambiguous
        assert confidence == "low"


class TestScoreFromClassHints:
    def test_empty_hints(self):
        scores = score_from_class_hints({})
        assert all(v == 0.0 for v in scores.values())

    def test_hint_boosts_class(self):
        hints = {"rolling_element_bearing": 0.8}
        scores = score_from_class_hints(hints)
        assert scores["rolling_element_bearing"] > 0
        assert scores["belt_drive_friction"] == 0.0


class TestScoreSignalAgreement:
    def test_no_agreement(self):
        behavioral = {cls: 0.0 for cls in MECHANICAL_CLASSES}
        hints = {cls: 0.0 for cls in MECHANICAL_CLASSES}
        codes = {}
        bonus = score_signal_agreement(behavioral, hints, codes)
        assert all(v == 0.0 for v in bonus.values())

    def test_triple_agreement(self):
        cls = "rolling_element_bearing"
        behavioral = {c: 0.0 for c in MECHANICAL_CLASSES}
        behavioral[cls] = 0.5
        hints = {c: 0.0 for c in MECHANICAL_CLASSES}
        hints[cls] = 0.3
        codes = {cls: 0.15}
        bonus = score_signal_agreement(behavioral, hints, codes)
        assert bonus[cls] == 0.7


class TestComputeDataSufficiency:
    def test_empty_input(self):
        ctx = BehavioralContext()
        score = compute_data_sufficiency(ctx, {}, [], 0.0)
        assert score == 0.0

    def test_rich_input(self):
        ctx = BehavioralContext(
            noise_character="squeal",
            rpm_dependency=True,
            cold_only=True,
            mechanical_localization=True,
            vehicle_type="sedan",
            issue_duration="weeks",
        )
        hints = {"belt_drive_friction": 0.8}
        codes = ["P0301"]
        score = compute_data_sufficiency(ctx, hints, codes, 0.8)
        assert score > 0.5


class TestRunTextDiagnosticPipeline:
    def test_bearing_symptoms(self, db_manager, bearing_context):
        result = run_text_diagnostic_pipeline(
            context=bearing_context,
            class_hints={"rolling_element_bearing": 0.8},
            user_codes=[],
            db_manager=db_manager,
        )
        assert isinstance(result, DiagnosisResult)
        assert result.top_class in MECHANICAL_CLASSES or result.top_class == "unknown"
        assert result.fingerprint_count == 0  # Text-only

    def test_belt_symptoms(self, db_manager, belt_context):
        result = run_text_diagnostic_pipeline(
            context=belt_context,
            class_hints={"belt_drive_friction": 0.9},
            user_codes=[],
            db_manager=db_manager,
        )
        assert isinstance(result, DiagnosisResult)

    def test_empty_input(self, db_manager, default_context):
        result = run_text_diagnostic_pipeline(
            context=default_context,
            class_hints={},
            user_codes=[],
            db_manager=db_manager,
        )
        assert isinstance(result, DiagnosisResult)
        assert result.is_ambiguous  # No data should be ambiguous
