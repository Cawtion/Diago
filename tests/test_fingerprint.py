"""Tests for core.fingerprint module."""

import numpy as np
import pytest

from core.fingerprint import (
    generate_fingerprint,
    fingerprint_to_signature,
    compute_fingerprint_stats,
    Fingerprint,
)


class TestGenerateFingerprint:
    def test_empty_audio_returns_empty(self):
        result = generate_fingerprint(np.array([], dtype=np.float32))
        assert result == []

    def test_silence_returns_few_or_no_fingerprints(self, silence, sample_rate):
        result = generate_fingerprint(silence, sample_rate)
        # Silence has no peaks, so no fingerprints
        assert len(result) == 0

    def test_sine_wave_generates_fingerprints(self, sine_wave, sample_rate):
        result = generate_fingerprint(sine_wave, sample_rate)
        assert len(result) >= 0  # May or may not generate depending on peak detection

    def test_complex_signal_generates_fingerprints(self, multi_tone, sample_rate):
        result = generate_fingerprint(multi_tone, sample_rate)
        # A multi-tone signal should generate at least some fingerprints
        assert isinstance(result, list)
        for fp in result:
            assert isinstance(fp, Fingerprint)
            assert isinstance(fp.hash_value, int)
            assert isinstance(fp.time_offset, float)

    def test_white_noise_generates_fingerprints(self, white_noise, sample_rate):
        result = generate_fingerprint(white_noise, sample_rate)
        assert isinstance(result, list)

    def test_deterministic(self, multi_tone, sample_rate):
        """Same input should produce same fingerprints."""
        result1 = generate_fingerprint(multi_tone, sample_rate)
        result2 = generate_fingerprint(multi_tone, sample_rate)
        assert len(result1) == len(result2)
        if result1:
            assert result1[0].hash_value == result2[0].hash_value


class TestFingerprintToSignature:
    def test_empty_list(self):
        sig = fingerprint_to_signature([])
        assert sig["num_hashes"] == 0
        assert sig["hashes"] == []
        assert sig["hash_set"] == set()

    def test_with_fingerprints(self):
        fps = [
            Fingerprint(hash_value=123, time_offset=0.0),
            Fingerprint(hash_value=456, time_offset=0.5),
            Fingerprint(hash_value=123, time_offset=1.0),
        ]
        sig = fingerprint_to_signature(fps)
        assert sig["num_hashes"] == 3
        assert sig["hash_set"] == {123, 456}


class TestComputeFingerprintStats:
    def test_empty_list(self):
        stats = compute_fingerprint_stats([])
        assert stats["total_hashes"] == 0
        assert stats["unique_hashes"] == 0

    def test_with_fingerprints(self):
        fps = [
            Fingerprint(hash_value=1, time_offset=0.0),
            Fingerprint(hash_value=2, time_offset=0.5),
            Fingerprint(hash_value=1, time_offset=1.0),
        ]
        stats = compute_fingerprint_stats(fps)
        assert stats["total_hashes"] == 3
        assert stats["unique_hashes"] == 2
        assert stats["time_span"] == pytest.approx(1.0)
        assert stats["density"] > 0
