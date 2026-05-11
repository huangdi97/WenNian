"""Tests for animal trajectory module."""

import pytest
from src.industrial.animal_trajectory import (
    compute_animal_biological_age, build_animal_trajectory,
    compare_treatment_groups, generate_trajectory_plot_data,
)


class TestAnimalTrajectory:
    def test_compute_young_mouse(self):
        result = compute_animal_biological_age(12, 25, 1.0, 1.0, species="mouse")
        assert result["chronological_age_weeks"] == 12
        assert result["biological_age_weeks"] > 0
        assert 0 < result["lifespan_ratio"] < 1

    def test_compute_old_mouse(self):
        result = compute_animal_biological_age(
            100, 35, 0.5, 0.4, fur_condition=0.3, species="mouse"
        )
        assert result["biological_age_weeks"] > result["chronological_age_weeks"]

    def test_build_trajectory(self):
        measurements = [
            {"chron_age_weeks": 12, "body_weight": 25, "grip_strength": 1.0,
             "gait_speed": 1.0, "timepoint": "baseline", "treatment_group": "control"},
            {"chron_age_weeks": 24, "body_weight": 28, "grip_strength": 0.8,
             "gait_speed": 0.85, "timepoint": "mid", "treatment_group": "control"},
        ]
        traj = build_animal_trajectory(measurements, species="mouse")
        assert len(traj) == 2
        assert traj[1]["biological_age_weeks"] > traj[0]["biological_age_weeks"]

    def test_compare_groups(self):
        measurements = [
            {"chron_age_weeks": 12, "body_weight": 25, "grip_strength": 1.0,
             "gait_speed": 1.0, "treatment_group": "control"},
            {"chron_age_weeks": 24, "body_weight": 28, "grip_strength": 0.8,
             "gait_speed": 0.85, "treatment_group": "control"},
            {"chron_age_weeks": 12, "body_weight": 25, "grip_strength": 1.0,
             "gait_speed": 1.0, "treatment_group": "treatment"},
            {"chron_age_weeks": 24, "body_weight": 27, "grip_strength": 0.9,
             "gait_speed": 0.9, "treatment_group": "treatment"},
        ]
        traj = build_animal_trajectory(measurements)
        comparison = compare_treatment_groups(traj)
        assert "control" in comparison
        assert "treatment" in comparison

    def test_generate_plot_data(self):
        measurements = [
            {"chron_age_weeks": 12, "body_weight": 25, "grip_strength": 1.0,
             "gait_speed": 1.0, "treatment_group": "control"},
            {"chron_age_weeks": 24, "body_weight": 28, "grip_strength": 0.8,
             "gait_speed": 0.85, "treatment_group": "control"},
        ]
        traj = build_animal_trajectory(measurements)
        plot_data = generate_trajectory_plot_data(traj)
        assert "groups" in plot_data
        assert "series" in plot_data

    def test_rat_species(self):
        result = compute_animal_biological_age(50, 300, 0.8, 0.9, species="rat")
        assert result["biological_age_weeks"] > 0
