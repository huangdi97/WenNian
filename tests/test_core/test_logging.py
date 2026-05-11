"""Tests for core.logging module."""

import logging
from src.core.logging import setup_logging, get_logger


class TestLogging:
    """Tests for logging setup and retrieval."""

    def test_get_logger(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_setup_logging_basic(self, tmp_path):
        """Smoke test: setting up logging shouldn't crash."""
        class FakeConfig:
            def get(self, key, default=None):
                mapping = {
                    "logging.level": "DEBUG",
                    "logging.dir": str(tmp_path),
                }
                return mapping.get(key, default)

        setup_logging(FakeConfig())
        logger = get_logger("test_log_setup")
        logger.info("test message")
        # Should not raise
