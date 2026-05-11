"""Tests for StabilityGuard."""

import math
import pytest
from src.validation.stability_guard import StabilityGuard


class TestStabilityGuard:
    @pytest.fixture
    def guard(self):
        return StabilityGuard()

    def test_normal_float(self, guard):
        assert guard.guard_scalar(3.14) == 3.14

    def test_nan_to_default(self, guard):
        result = guard.guard_scalar(float("nan"))
        assert result == 0.0
        assert len(guard.get_violations()) > 0

    def test_inf_to_default(self, guard):
        result = guard.guard_scalar(float("inf"))
        assert result == 0.0

    def test_negative_inf(self, guard):
        result = guard.guard_scalar(float("-inf"))
        assert result == 0.0

    def test_clamp_max(self, guard):
        result = guard.guard_scalar(200.0, max_value=120.0)
        assert result == 120.0

    def test_clamp_min(self, guard):
        result = guard.guard_scalar(-10.0, min_value=0.0)
        assert result == 0.0

    def test_none_handling(self, guard):
        result = guard.guard_scalar(None)
        assert result == 0.0

    def test_string_handling(self, guard):
        result = guard.guard_scalar("hello")
        assert result == 0.0

    def test_guard_dict(self, guard):
        data = {"a": 1.0, "b": float("nan"), "c": 3.0}
        result = guard.guard_dict(data)
        assert result["a"] == 1.0
        assert result["b"] == 0.0
        assert result["c"] == 3.0

    def test_guard_division(self, guard):
        assert guard.guard_division(10.0, 2.0) == 5.0
        assert guard.guard_division(5.0, 0.0) == 0.0

    def test_raise_on_nan(self):
        guard = StabilityGuard(raise_on_nan=True)
        from src.core.exceptions import ComputationError
        with pytest.raises(ComputationError):
            guard.guard_scalar(float("nan"))

    def test_clear_violations(self, guard):
        guard.guard_scalar(float("nan"))
        assert len(guard.get_violations()) > 0
        guard.clear_violations()
        assert len(guard.get_violations()) == 0
