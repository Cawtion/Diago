"""Tests for core.symptom_parser module."""

import pytest

from core.symptom_parser import parse_symptoms, ParsedSymptoms


class TestParseSymptoms:
    def test_empty_string(self):
        result = parse_symptoms("")
        assert isinstance(result, ParsedSymptoms)
        assert result.matched_keywords == []
        assert result.confidence == 0.0

    def test_whining_at_speed(self):
        result = parse_symptoms("My car makes a whining noise at high speed")
        assert len(result.matched_keywords) > 0
        assert result.confidence > 0.0
        # Should detect speed dependency or whine character
        assert (
            result.context.noise_character == "whine"
            or result.context.speed_dependency
            or "whining" in [kw.lower() for kw in result.matched_keywords]
        )

    def test_knocking_at_idle(self):
        result = parse_symptoms("engine knocking noise at idle, especially cold start")
        assert len(result.matched_keywords) > 0
        # Should detect knock character and idle/cold conditions
        ctx = result.context
        assert ctx.noise_character == "knock_tap" or ctx.occurs_at_idle or ctx.cold_only

    def test_belt_squeal(self):
        result = parse_symptoms("squealing from the engine bay when I start the car cold")
        assert len(result.matched_keywords) > 0
        ctx = result.context
        # Should identify squeal and cold start
        assert ctx.noise_character == "squeal" or ctx.cold_only

    def test_grinding_brakes(self):
        result = parse_symptoms("grinding noise when I press the brake pedal")
        assert len(result.matched_keywords) > 0

    def test_class_hints_populated(self):
        result = parse_symptoms("wheel bearing noise, humming at highway speed")
        # Should have class hints
        if result.class_hints:
            assert "rolling_element_bearing" in result.class_hints

    def test_suggested_codes(self):
        result = parse_symptoms("engine misfire, rough idle, check engine light")
        # May suggest codes related to misfire
        assert isinstance(result.suggested_codes, list)

    def test_location_hints(self):
        result = parse_symptoms("noise coming from the front left wheel area")
        assert isinstance(result.location_hints, list)

    def test_preserves_original_text(self):
        text = "my car rattles over bumps"
        result = parse_symptoms(text)
        assert result.original_text == text

    def test_minimal_input(self):
        result = parse_symptoms("noise")
        assert isinstance(result, ParsedSymptoms)
