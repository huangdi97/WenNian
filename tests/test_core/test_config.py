"""Tests for core.config module."""

import os
import pytest
from pathlib import Path

from src.core.config import AppConfig, load_config, _ConfigProxy, ConfigurationError


class TestAppConfig:
    """Tests for the AppConfig singleton."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton between tests."""
        AppConfig._instance = None
        yield
        AppConfig._instance = None

    def test_load_default_config(self):
        config = AppConfig()
        assert config.get("clocks.weights.phenoage") == 1.0
        assert config.get("ui.default_age") == 40
        assert config.get("api.port") == 8000

    def test_get_with_default(self):
        config = AppConfig()
        assert config.get("nonexistent.key", 42) == 42
        assert config.get("nonexistent.key") is None

    def test_get_nested_keys(self):
        config = AppConfig()
        assert config.get("clocks.weights.kdm") == 0.8

    def test_attribute_access(self):
        config = AppConfig()
        assert config.clocks.weights.phenoage == 1.0

    def test_attribute_access_nonexistent(self):
        config = AppConfig()
        with pytest.raises(AttributeError):
            _ = config.nonexistent

    def test_to_dict(self):
        config = AppConfig()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert "clocks" in d
        assert d["clocks"]["weights"]["phenoage"] == 1.0

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("WENNIAN_CLOCKS__WEIGHTS__PHENOAGE", "0.5")
        config = AppConfig()
        assert config.get("clocks.weights.phenoage") == 0.5

    def test_env_override_bool(self, monkeypatch):
        monkeypatch.setenv("WENNIAN_SOME__FLAG", "true")
        config = AppConfig()
        assert config.get("some.flag") is True


class TestLoadConfig:
    """Tests for load_config helper."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        AppConfig._instance = None
        yield
        AppConfig._instance = None

    def test_load_default(self):
        config = load_config("default")
        assert config is not None
        assert config.get("ui.title") is not None
