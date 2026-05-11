"""Tests for src/utils/helpers.py."""

import math
from src.utils.helpers import safe_float, safe_div, truncate_string, hash_dict


class TestSafeFloat:
    def test_normal_float(self):
        assert safe_float(3.14) == 3.14

    def test_int_to_float(self):
        assert safe_float(42) == 42.0
        assert isinstance(safe_float(42), float)

    def test_string_to_float(self):
        assert safe_float("3.14") == 3.14

    def test_none_returns_default(self):
        assert safe_float(None, default=99.0) == 99.0

    def test_nan_returns_default(self):
        assert safe_float(float("nan"), default=0.0) == 0.0

    def test_inf_returns_default(self):
        assert safe_float(float("inf"), default=1.0) == 1.0

    def test_min_bound(self):
        assert safe_float(-10.0, min_val=0.0) == 0.0

    def test_max_bound(self):
        assert safe_float(200.0, max_val=100.0) == 100.0

    def test_invalid_string(self):
        assert safe_float("hello") == 0.0


class TestSafeDiv:
    def test_normal_division(self):
        assert safe_div(10.0, 2.0) == 5.0

    def test_divide_by_zero(self):
        assert safe_div(10.0, 0.0) == 0.0

    def test_zero_numerator(self):
        assert safe_div(0.0, 5.0) == 0.0

    def test_default_on_zero_denom(self):
        assert safe_div(5.0, 0.0, default=99.0) == 99.0

    def test_invalid_types(self):
        assert safe_div("a", "b") == 0.0


class TestTruncateString:
    def test_no_truncation(self):
        assert truncate_string("hello", 10) == "hello"

    def test_truncation(self):
        result = truncate_string("hello world this is long", 10)
        assert result.endswith("...")
        assert len(result) == 10

    def test_exact_length(self):
        assert truncate_string("abc", 3) == "abc"


class TestHashDict:
    def test_consistent_hash(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 2, "a": 1}
        assert hash_dict(d1) == hash_dict(d2)

    def test_different_values(self):
        assert hash_dict({"a": 1}) != hash_dict({"a": 2})

    def test_returns_string(self):
        assert isinstance(hash_dict({"x": "y"}), str)

    def test_length(self):
        assert len(hash_dict({"a": 1})) == 64
