"""Tests for core.feature_extraction module."""

import numpy as np
import pytest

from core.feature_extraction import (
    extract_features,
    extract_features_from_context,
    compute_spectral_features,
    compute_temporal_features,
    compute_subband_energies,
    AudioFeatures,
    BehavioralContext,
)


class TestComputeSpectralFeatures:
    def test_sine_wave_has_narrow_bandwidth(self, sine_wave, sample_rate):
        features = compute_spectral_features(sine_wave, sample_rate)
        # Pure tone should have relatively low spectral flatness
        assert features["spectral_flatness"] < 0.5

    def test_white_noise_is_flat(self, white_noise, sample_rate):
        features = compute_spectral_features(white_noise, sample_rate)
        # White noise should have higher flatness than a pure tone
        assert features["spectral_flatness"] > 0.2

    def test_harmonic_signal_has_harmonic_ratio(self, multi_tone, sample_rate):
        features = compute_spectral_features(multi_tone, sample_rate)
        # Harmonic signal should have measurable harmonic ratio
        assert features["harmonic_ratio"] >= 0.0
        assert features["harmonic_ratio"] <= 1.0

    def test_all_features_present(self, sine_wave, sample_rate):
        features = compute_spectral_features(sine_wave, sample_rate)
        expected_keys = [
            "spectral_centroid", "spectral_bandwidth", "spectral_flatness",
            "harmonic_ratio", "spectral_rolloff", "dominant_frequency",
            "spectral_centroid_std", "spectral_entropy",
        ]
        for key in expected_keys:
            assert key in features

    def test_values_in_valid_range(self, sine_wave, sample_rate):
        features = compute_spectral_features(sine_wave, sample_rate)
        for key, value in features.items():
            assert 0.0 <= value <= 1.0, f"{key} = {value} out of [0, 1]"


class TestComputeTemporalFeatures:
    def test_silence_has_zero_rms(self, silence, sample_rate):
        features = compute_temporal_features(silence, sample_rate)
        assert features["rms_energy"] == pytest.approx(0.0, abs=1e-6)

    def test_sine_has_nonzero_rms(self, sine_wave, sample_rate):
        features = compute_temporal_features(sine_wave, sample_rate)
        assert features["rms_energy"] > 0.0

    def test_impulsive_has_high_crest(self, impulsive_audio, sample_rate):
        features = compute_temporal_features(impulsive_audio, sample_rate)
        # Impulsive signal should have higher crest factor than pure tone
        sine_features = compute_temporal_features(
            np.sin(np.linspace(0, 2 * np.pi * 440, sample_rate)).astype(np.float32),
            sample_rate,
        )
        assert features["crest_factor"] > sine_features["crest_factor"]

    def test_all_features_present(self, sine_wave, sample_rate):
        features = compute_temporal_features(sine_wave, sample_rate)
        expected_keys = [
            "rms_energy", "amplitude_variance", "periodicity_score",
            "transient_density", "crest_factor", "zero_crossing_rate",
        ]
        for key in expected_keys:
            assert key in features


class TestComputeSubbandEnergies:
    def test_low_freq_in_low_band(self, sample_rate):
        # 100 Hz tone should have most energy in band_low (20-300 Hz)
        t = np.linspace(0, 1.0, sample_rate, endpoint=False, dtype=np.float32)
        low_tone = np.sin(2 * np.pi * 100 * t).astype(np.float32)
        bands = compute_subband_energies(low_tone, sample_rate)
        assert bands["band_low"] > bands["band_mid"]

    def test_high_freq_in_high_band(self, sample_rate):
        # 7000 Hz tone should have most energy in band_high (6000-8000 Hz)
        t = np.linspace(0, 1.0, sample_rate, endpoint=False, dtype=np.float32)
        high_tone = np.sin(2 * np.pi * 7000 * t).astype(np.float32)
        bands = compute_subband_energies(high_tone, sample_rate)
        assert bands["band_high"] > bands["band_low"]

    def test_bands_sum_to_one(self, sine_wave, sample_rate):
        bands = compute_subband_energies(sine_wave, sample_rate)
        total = sum(bands.values())
        assert total == pytest.approx(1.0, abs=0.01)


class TestExtractFeatures:
    def test_empty_audio_returns_defaults(self):
        features = extract_features(np.array([], dtype=np.float32))
        assert features.spectral_centroid == 0.0
        assert features.rms_energy == 0.0

    def test_with_context(self, sine_wave, sample_rate, bearing_context):
        features = extract_features(sine_wave, sample_rate, bearing_context)
        assert features.speed_dependency == 1.0
        assert features.char_hum_drone == 1.0

    def test_to_dict(self, sine_wave, sample_rate):
        features = extract_features(sine_wave, sample_rate)
        d = features.to_dict()
        assert isinstance(d, dict)
        assert "spectral_centroid" in d
        assert "rms_energy" in d


class TestExtractFeaturesFromContext:
    def test_bearing_context(self, bearing_context):
        features = extract_features_from_context(bearing_context)
        assert features.speed_dependency == 1.0
        assert features.char_hum_drone == 1.0
        assert features.mileage_over_150k == 1.0
        # Spectral features should be zero (no audio)
        assert features.spectral_centroid == 0.0

    def test_belt_context(self, belt_context):
        features = extract_features_from_context(belt_context)
        assert features.cold_only == 1.0
        assert features.rpm_dependency == 1.0
        assert features.char_squeal == 1.0

    def test_default_context_all_zeros(self, default_context):
        features = extract_features_from_context(default_context)
        d = features.to_dict()
        # All behavioral booleans should be 0
        assert d["rpm_dependency"] == 0.0
        assert d["cold_only"] == 0.0
