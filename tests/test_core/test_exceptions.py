"""Tests for core.exceptions module."""

import pytest

from src.core.exceptions import (
    WenNianError,
    ConfigurationError,
    ValidationError,
    PermissionDenied,
    ModelNotFound,
    ComputationError,
    RedLineViolation,
)


class TestWenNianError:
    """Tests for the base exception class."""

    def test_create_with_message(self):
        err = WenNianError("test message")
        assert err.message == "test message"
        assert err.details == {}
        assert str(err) == "test message"

    def test_create_with_details(self):
        err = WenNianError("test", details={"key": "val"})
        assert err.details == {"key": "val"}

    def test_subclass_isinstance(self):
        err = ConfigurationError("cfg error")
        assert isinstance(err, WenNianError)
        assert isinstance(err, ConfigurationError)
        assert isinstance(err, Exception)

    def test_all_exception_types(self):
        exceptions = [
            ConfigurationError("cfg"),
            ValidationError("val"),
            PermissionDenied("perm"),
            ModelNotFound("model"),
            ComputationError("comp"),
            RedLineViolation("red"),
        ]
        for exc in exceptions:
            assert isinstance(exc, WenNianError)
            assert exc.message != ""
