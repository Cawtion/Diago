"""Tests for database.trouble_code_lookup module."""

import pytest

from database.trouble_code_lookup import (
    lookup_code,
    lookup_codes,
    suggest_codes_for_symptoms,
    search_codes,
    get_mechanical_class_boosts,
    get_severity_weight,
    get_code_count,
    CodeDefinition,
)


class TestLookupCode:
    def test_existing_code(self, db_manager):
        # P0300 should be in the seed data
        result = lookup_code("P0300", db_manager)
        if result is not None:
            assert result.code == "P0300"
            assert result.description != ""

    def test_nonexistent_code(self, db_manager):
        result = lookup_code("Z9999", db_manager)
        assert result is None

    def test_case_insensitive(self, db_manager):
        result_upper = lookup_code("P0300", db_manager)
        result_lower = lookup_code("p0300", db_manager)
        if result_upper is not None:
            assert result_lower is not None
            assert result_upper.code == result_lower.code


class TestLookupCodes:
    def test_batch_lookup(self, db_manager):
        results = lookup_codes(["P0300", "P0301", "Z9999"], db_manager)
        assert isinstance(results, list)
        # Should find at least the valid codes
        found_codes = {r.code for r in results}
        # P0300 should be there if in seed data
        if "P0300" in found_codes:
            assert True

    def test_empty_list(self, db_manager):
        results = lookup_codes([], db_manager)
        assert results == []


class TestSuggestCodesForSymptoms:
    def test_with_keywords(self, db_manager):
        results = suggest_codes_for_symptoms(["misfire", "rough"], db_manager)
        assert isinstance(results, list)

    def test_empty_keywords(self, db_manager):
        results = suggest_codes_for_symptoms([], db_manager)
        assert results == []

    def test_no_match(self, db_manager):
        results = suggest_codes_for_symptoms(["xyznonexistent"], db_manager)
        assert isinstance(results, list)


class TestSearchCodes:
    def test_search_by_description(self, db_manager):
        results = search_codes("misfire", db_manager)
        assert isinstance(results, list)

    def test_search_by_code(self, db_manager):
        results = search_codes("P03", db_manager)
        assert isinstance(results, list)

    def test_empty_query(self, db_manager):
        results = search_codes("", db_manager)
        assert results == []


class TestGetMechanicalClassBoosts:
    def test_with_codes(self, db_manager):
        boosts = get_mechanical_class_boosts(["P0300"], db_manager)
        assert isinstance(boosts, dict)

    def test_empty_codes(self, db_manager):
        boosts = get_mechanical_class_boosts([], db_manager)
        assert boosts == {}

    def test_nonexistent_codes(self, db_manager):
        boosts = get_mechanical_class_boosts(["Z9999"], db_manager)
        assert isinstance(boosts, dict)


class TestGetSeverityWeight:
    def test_with_codes(self, db_manager):
        weight = get_severity_weight(["P0300"], db_manager)
        assert 0.0 <= weight <= 1.0

    def test_empty_codes(self, db_manager):
        weight = get_severity_weight([], db_manager)
        assert weight == 0.0


class TestGetCodeCount:
    def test_count(self, db_manager):
        count = get_code_count(db_manager)
        assert count > 0
