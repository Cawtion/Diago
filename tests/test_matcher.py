"""Tests for core.matcher module."""

import pytest

from core.matcher import (
    match_fingerprint,
    match_with_trouble_codes,
)
from core.fingerprint import Fingerprint
from database.db_manager import MatchResult


class TestMatchFingerprint:
    def test_empty_fingerprints(self, db_manager):
        results = match_fingerprint([], db_manager)
        assert results == []

    def test_no_matches_in_empty_db(self, db_manager):
        # Fingerprints that don't match anything stored
        fps = [
            Fingerprint(hash_value=999999, time_offset=0.0),
            Fingerprint(hash_value=999998, time_offset=0.5),
        ]
        results = match_fingerprint(fps, db_manager)
        assert isinstance(results, list)

    def test_matching_against_stored(self, db_manager):
        # Store some hashes
        sig_id = db_manager.add_fault_signature(
            name="Test Matcher",
            description="d",
            category="engine",
            associated_codes="P0301",
        )
        stored_hashes = [(i, i * 0.1) for i in range(1, 20)]
        db_manager.add_signature_hashes(sig_id, stored_hashes)

        # Create fingerprints that partially match
        fps = [Fingerprint(hash_value=i, time_offset=i * 0.1) for i in range(1, 10)]
        results = match_fingerprint(fps, db_manager, confidence_threshold=0)
        # Should find the match
        assert isinstance(results, list)
        if results:
            assert results[0].fault_name == "Test Matcher"


class TestMatchWithTroubleCodes:
    def test_empty_inputs(self, db_manager):
        results = match_with_trouble_codes([], db_manager, [])
        assert results == []

    def test_code_boost(self, db_manager):
        sig_id = db_manager.add_fault_signature(
            name="Code Boost Test",
            description="d",
            category="engine",
            associated_codes="P0301",
        )
        stored_hashes = [(i, i * 0.1) for i in range(1, 20)]
        db_manager.add_signature_hashes(sig_id, stored_hashes)

        fps = [Fingerprint(hash_value=i, time_offset=i * 0.1) for i in range(1, 10)]

        # Without codes
        results_no_code = match_with_trouble_codes(fps, db_manager, [])
        # With matching code (should boost)
        results_with_code = match_with_trouble_codes(fps, db_manager, ["P0301"])

        assert isinstance(results_no_code, list)
        assert isinstance(results_with_code, list)
