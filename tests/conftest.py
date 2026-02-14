"""
Shared pytest fixtures for all Diago tests.
"""

import os
import tempfile

import numpy as np
import pytest

from core.config import reset_settings
from core.feature_extraction import BehavioralContext, AudioFeatures


# ---------------------------------------------------------------------------
# Settings fixture (ensures clean config per test)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_settings():
    """Reset settings cache before each test."""
    reset_settings()
    yield
    reset_settings()


# ---------------------------------------------------------------------------
# Audio fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_rate():
    """Standard sample rate."""
    return 44100


@pytest.fixture
def silence(sample_rate):
    """1 second of silence."""
    return np.zeros(sample_rate, dtype=np.float32)


@pytest.fixture
def sine_wave(sample_rate):
    """1 second of 440 Hz sine wave."""
    t = np.linspace(0, 1.0, sample_rate, endpoint=False, dtype=np.float32)
    return np.sin(2 * np.pi * 440 * t).astype(np.float32)


@pytest.fixture
def multi_tone(sample_rate):
    """1 second of combined 440 + 880 + 1320 Hz tones (harmonic series)."""
    t = np.linspace(0, 1.0, sample_rate, endpoint=False, dtype=np.float32)
    signal = (
        0.5 * np.sin(2 * np.pi * 440 * t)
        + 0.3 * np.sin(2 * np.pi * 880 * t)
        + 0.2 * np.sin(2 * np.pi * 1320 * t)
    )
    return signal.astype(np.float32)


@pytest.fixture
def white_noise(sample_rate):
    """1 second of white noise."""
    rng = np.random.default_rng(42)
    return rng.standard_normal(sample_rate).astype(np.float32)


@pytest.fixture
def short_audio(sample_rate):
    """0.1 second of 1000 Hz tone."""
    n = int(sample_rate * 0.1)
    t = np.linspace(0, 0.1, n, endpoint=False, dtype=np.float32)
    return np.sin(2 * np.pi * 1000 * t).astype(np.float32)


@pytest.fixture
def impulsive_audio(sample_rate):
    """1 second of audio with periodic impulses (simulates knocking)."""
    audio = np.zeros(sample_rate, dtype=np.float32)
    # Place impulses every ~100ms
    for i in range(0, sample_rate, sample_rate // 10):
        width = min(50, sample_rate - i)
        audio[i:i + width] = 0.8
    return audio


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def db_manager(temp_db_path):
    """Create a fully initialized DatabaseManager with a temp database."""
    from database.db_manager import DatabaseManager
    manager = DatabaseManager(temp_db_path)
    manager.initialize()
    yield manager
    manager.close()


# ---------------------------------------------------------------------------
# Context fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_context():
    """Default (empty) behavioral context."""
    return BehavioralContext()


@pytest.fixture
def bearing_context():
    """Behavioral context suggesting a wheel bearing issue."""
    return BehavioralContext(
        speed_dependency=True,
        noise_character="hum_drone",
        perceived_frequency="mid",
        mileage_range="over_150k",
    )


@pytest.fixture
def belt_context():
    """Behavioral context suggesting a belt issue."""
    return BehavioralContext(
        cold_only=True,
        rpm_dependency=True,
        noise_character="squeal",
        perceived_frequency="high",
    )


@pytest.fixture
def combustion_context():
    """Behavioral context suggesting a combustion issue."""
    return BehavioralContext(
        rpm_dependency=True,
        occurs_at_idle=True,
        noise_character="knock_tap",
        perceived_frequency="low",
    )


# ---------------------------------------------------------------------------
# Temporary WAV file fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_wav_file(sine_wave, sample_rate):
    """Create a temporary WAV file with sine wave data."""
    import soundfile as sf
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(path, sine_wave, sample_rate)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass
