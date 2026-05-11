"""Tests for OutputConsistency."""

from src.validation.output_consistency import OutputConsistency


class TestOutputConsistency:
    def test_insufficient_history(self):
        oc = OutputConsistency()
        result = oc.check({"biological_age": 42.0, "chronological_age": 40.0})
        assert result["is_consistent"]
        assert "历史数据不足" in result.get("note", "")

    def test_consistent_trajectory(self):
        oc = OutputConsistency()
        # Build history
        for age in range(38, 42):
            oc.add_record({"biological_age": float(age) + 2.0, "chronological_age": float(age)})
        result = oc.check({"biological_age": 44.0, "chronological_age": 42.0})
        assert result["is_consistent"]

    def test_anomalous_jump(self):
        oc = OutputConsistency()
        for age in range(38, 42):
            oc.add_record({"biological_age": float(age) + 1.0, "chronological_age": float(age)})
        # Large jump from ~43 to 55
        result = oc.check({"biological_age": 55.0, "chronological_age": 42.0})
        assert not result["is_consistent"]
        assert len(result["warnings"]) > 0

    def test_trajectory_retrieval(self):
        oc = OutputConsistency(max_history=5)
        for age in range(35, 42):
            oc.add_record({"biological_age": float(age), "chronological_age": float(age)})
        traj = oc.get_trajectory()
        assert len(traj) <= 5

    def test_z_score_computed(self):
        oc = OutputConsistency()
        oc.add_record({"biological_age": 40.0, "chronological_age": 40.0})
        oc.add_record({"biological_age": 41.0, "chronological_age": 41.0})
        result = oc.check({"biological_age": 42.0, "chronological_age": 42.0})
        assert result["z_score"] is not None
        assert result["expected_age"] is not None
