"""Tests for organ clocks dimension module."""

import pytest
from src.dimensions import (
    assess_organ_ages, identify_top_drivers, build_radar_data,
    OrganAge, ORGAN_INFLECTION_POINTS,
)


class TestOrganClocks:
    def test_assess_with_blood_markers(self, sample_biomarkers):
        results = assess_organ_ages(sample_biomarkers)
        assert len(results) > 0
        for oa in results:
            assert isinstance(oa, OrganAge)
            assert oa.organ in ORGAN_INFLECTION_POINTS

    def test_assess_empty_biomarkers(self):
        results = assess_organ_ages({})
        assert results == []

    def test_assess_missing_organ_markers(self):
        results = assess_organ_ages({"age": 40, "albumin": 43})
        assert len(results) >= 1  # At least liver can be assessed

    def test_inflection_points_known(self):
        assert "血管" in ORGAN_INFLECTION_POINTS
        assert "脑" in ORGAN_INFLECTION_POINTS
        assert ORGAN_INFLECTION_POINTS["血管"] == 30.0
        assert ORGAN_INFLECTION_POINTS["脑"] == 50.0

    def test_identify_top_drivers(self, sample_biomarkers):
        organ_ages = assess_organ_ages(sample_biomarkers)
        drivers = identify_top_drivers(organ_ages, top_n=2)
        assert len(drivers) <= 2
        for d in drivers:
            assert "organ" in d
            assert "priority" in d

    def test_build_radar_data(self, sample_biomarkers):
        organ_ages = assess_organ_ages(sample_biomarkers)
        radar = build_radar_data(organ_ages)
        assert "labels" in radar
        assert "values" in radar
        assert "inflections" in radar
        assert len(radar["labels"]) == len(radar["values"])

    def test_organ_age_sorted_by_asynchrony(self, sample_biomarkers):
        results = assess_organ_ages(sample_biomarkers)
        if len(results) >= 2:
            assert results[0].asynchrony_score >= results[-1].asynchrony_score
