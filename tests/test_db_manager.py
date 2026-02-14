"""Tests for database.db_manager module."""

import pytest

from database.db_manager import (
    DatabaseManager,
    FaultSignature,
    AnalysisSession,
    MatchResult,
)


class TestDatabaseInitialization:
    def test_creates_tables(self, db_manager):
        # Should be able to query fault_signatures
        sigs = db_manager.get_all_signatures()
        assert isinstance(sigs, list)

    def test_seeds_fault_signatures(self, db_manager):
        count = db_manager.get_signature_count()
        assert count > 0  # Seed data should have been loaded

    def test_seeds_trouble_codes(self, db_manager):
        cursor = db_manager.connection.execute(
            "SELECT COUNT(*) FROM trouble_code_definitions"
        )
        count = cursor.fetchone()[0]
        assert count > 0


class TestFaultSignatureOperations:
    def test_add_and_retrieve(self, db_manager):
        sig_id = db_manager.add_fault_signature(
            name="Test Fault",
            description="A test fault signature",
            category="engine",
            associated_codes="P0301",
        )
        assert sig_id > 0

        sig = db_manager.get_signature_by_id(sig_id)
        assert sig is not None
        assert sig.name == "Test Fault"
        assert sig.category == "engine"
        assert sig.associated_codes == "P0301"

    def test_get_by_code(self, db_manager):
        db_manager.add_fault_signature(
            name="Code Test",
            description="desc",
            category="engine",
            associated_codes="P0420,P0301",
        )
        results = db_manager.get_signatures_by_code("P0420")
        assert len(results) >= 1
        assert any("P0420" in s.associated_codes for s in results)

    def test_get_nonexistent(self, db_manager):
        result = db_manager.get_signature_by_id(99999)
        assert result is None

    def test_delete_signature(self, db_manager):
        sig_id = db_manager.add_fault_signature(
            name="To Delete", description="d", category="engine", associated_codes="",
        )
        db_manager.delete_signature(sig_id)
        assert db_manager.get_signature_by_id(sig_id) is None


class TestSignatureHashOperations:
    def test_add_and_retrieve_hashes(self, db_manager):
        sig_id = db_manager.add_fault_signature(
            name="Hash Test", description="d", category="engine", associated_codes="",
        )
        hashes = [(12345, 0.0), (67890, 0.5), (11111, 1.0)]
        db_manager.add_signature_hashes(sig_id, hashes)

        retrieved = db_manager.get_signature_hashes(sig_id)
        assert len(retrieved) == 3

    def test_find_matching_hashes(self, db_manager):
        sig_id = db_manager.add_fault_signature(
            name="Match Test", description="d", category="engine", associated_codes="",
        )
        hashes = [(100, 0.0), (200, 0.5), (300, 1.0)]
        db_manager.add_signature_hashes(sig_id, hashes)

        matches = db_manager.find_matching_hashes([100, 300, 999])
        assert len(matches) >= 2
        found_hashes = {h for _, h, _ in matches}
        assert 100 in found_hashes
        assert 300 in found_hashes

    def test_find_matching_empty(self, db_manager):
        assert db_manager.find_matching_hashes([]) == []

    def test_hash_count(self, db_manager):
        sig_id = db_manager.add_fault_signature(
            name="Count Test", description="d", category="engine", associated_codes="",
        )
        db_manager.add_signature_hashes(sig_id, [(1, 0.0), (2, 0.5)])
        assert db_manager.get_hash_count_by_signature(sig_id) == 2


class TestSessionOperations:
    def test_create_and_retrieve(self, db_manager):
        session_id = db_manager.create_session(
            audio_path="/tmp/test.wav",
            user_codes="P0301,P0420",
            notes="Test session",
            duration_seconds=5.0,
        )
        assert session_id > 0

        history = db_manager.get_session_history()
        assert len(history) >= 1
        session = history[0]
        assert session.user_codes == "P0301,P0420"

    def test_session_matches(self, db_manager):
        sig_id = db_manager.add_fault_signature(
            name="Session Match Test", description="d", category="engine",
            associated_codes="P0301",
        )
        session_id = db_manager.create_session(notes="Match test")
        db_manager.add_session_match(session_id, sig_id, 85.5)

        matches = db_manager.get_session_matches(session_id)
        assert len(matches) == 1
        assert matches[0].fault_name == "Session Match Test"
        assert matches[0].confidence_pct == 85.5

    def test_delete_session(self, db_manager):
        session_id = db_manager.create_session(notes="Delete me")
        db_manager.delete_session(session_id)
        history = db_manager.get_session_history()
        assert all(s.id != session_id for s in history)


class TestDatabaseClose:
    def test_close_and_reopen(self, temp_db_path):
        db1 = DatabaseManager(temp_db_path)
        db1.initialize()
        count1 = db1.get_signature_count()
        db1.close()

        db2 = DatabaseManager(temp_db_path)
        db2.initialize()
        count2 = db2.get_signature_count()
        db2.close()

        assert count1 == count2
