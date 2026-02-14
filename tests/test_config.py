"""Tests for core.config module."""

import os
import pytest

from core.config import (
    get_settings,
    reset_settings,
    AppSettings,
    AudioSettings,
    LLMSettings,
    AgentSettings,
)


class TestAppSettings:
    def test_default_values(self):
        settings = get_settings()
        assert settings.app_name == "Diago"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False

    def test_audio_defaults(self):
        settings = get_settings()
        assert settings.audio.sample_rate == 44100
        assert settings.audio.channels == 1
        assert settings.audio.bandpass_low_hz == 20.0
        assert settings.audio.bandpass_high_hz == 8000.0

    def test_llm_defaults(self):
        settings = get_settings()
        assert settings.llm.llm_enabled is False
        assert settings.llm.llm_provider is None

    def test_agent_defaults(self):
        settings = get_settings()
        assert settings.agent.agent_enabled is False

    def test_db_path_is_user_scoped(self):
        settings = get_settings()
        db_path = settings.db_path
        assert "auto_audio.db" in db_path
        # Should NOT be in project root
        assert db_path != os.path.join(os.path.dirname(__file__), "..", "auto_audio.db")

    def test_user_data_dir_exists(self):
        settings = get_settings()
        data_dir = settings.user_data_dir
        assert data_dir.exists()

    def test_reset_clears_cache(self):
        s1 = get_settings()
        reset_settings()
        s2 = get_settings()
        # They should be separate instances
        assert s1 is not s2

    def test_project_root(self):
        settings = get_settings()
        root = settings.project_root
        assert root.exists()
