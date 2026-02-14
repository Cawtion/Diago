"""Tests for core.preprocessing module."""

import numpy as np
import pytest

from core.preprocessing import (
    preprocess_audio,
    normalize_amplitude,
    bandpass_filter,
    reduce_noise_floor,
)


class TestNormalizeAmplitude:
    def test_normalizes_to_unit_range(self, sine_wave):
        result = normalize_amplitude(sine_wave * 0.5)
        assert np.max(np.abs(result)) == pytest.approx(1.0, abs=0.01)

    def test_already_normalized(self, sine_wave):
        result = normalize_amplitude(sine_wave)
        assert np.max(np.abs(result)) == pytest.approx(1.0, abs=0.01)

    def test_silence_unchanged(self, silence):
        result = normalize_amplitude(silence)
        assert np.allclose(result, silence)

    def test_output_dtype(self, sine_wave):
        result = normalize_amplitude(sine_wave)
        assert result.dtype == np.float32


class TestBandpassFilter:
    def test_preserves_in_band_signal(self, sine_wave, sample_rate):
        # 440 Hz is within 20-8000 Hz
        filtered = bandpass_filter(sine_wave, 20.0, 8000.0, sample_rate)
        # Energy should be largely preserved
        orig_energy = np.sum(sine_wave ** 2)
        filt_energy = np.sum(filtered ** 2)
        assert filt_energy / orig_energy > 0.8

    def test_attenuates_out_of_band(self, sample_rate):
        # Generate a 15000 Hz tone (above 8000 Hz cutoff)
        t = np.linspace(0, 1.0, sample_rate, endpoint=False, dtype=np.float32)
        high_freq = np.sin(2 * np.pi * 15000 * t).astype(np.float32)
        filtered = bandpass_filter(high_freq, 20.0, 8000.0, sample_rate)
        orig_energy = np.sum(high_freq ** 2)
        filt_energy = np.sum(filtered ** 2)
        assert filt_energy / orig_energy < 0.1

    def test_invalid_range_returns_unchanged(self, sine_wave, sample_rate):
        # low >= high should return unchanged
        result = bandpass_filter(sine_wave, 8000.0, 20.0, sample_rate)
        assert np.allclose(result, sine_wave)


class TestReduceNoiseFloor:
    def test_short_audio_unchanged(self, sample_rate):
        short = np.random.randn(100).astype(np.float32)
        result = reduce_noise_floor(short, sample_rate)
        assert np.allclose(result, short)

    def test_preserves_strong_signal(self, sine_wave, sample_rate):
        result = reduce_noise_floor(sine_wave, sample_rate)
        # Strong tonal signal should be largely preserved
        assert len(result) == len(sine_wave)
        correlation = np.corrcoef(sine_wave[:len(result)], result[:len(sine_wave)])[0, 1]
        assert correlation > 0.5

    def test_output_length_matches(self, white_noise, sample_rate):
        result = reduce_noise_floor(white_noise, sample_rate)
        assert len(result) == len(white_noise)


class TestPreprocessAudio:
    def test_empty_audio(self):
        result = preprocess_audio(np.array([], dtype=np.float32))
        assert len(result) == 0

    def test_full_pipeline_runs(self, sine_wave, sample_rate):
        result = preprocess_audio(sine_wave, sample_rate)
        assert len(result) == len(sine_wave)
        assert result.dtype == np.float32

    def test_custom_freq_range(self, sine_wave, sample_rate):
        result = preprocess_audio(sine_wave, sample_rate, low_hz=100.0, high_hz=2000.0)
        assert len(result) > 0
