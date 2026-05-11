"""Tests for instant feedback module."""

import pytest
from src.outputs.instant_feedback import (
    generate_daily_card, generate_trend_card, generate_intervention_reminder,
)


class TestInstantFeedback:
    def test_generate_daily_card(self):
        card = generate_daily_card(42.5, 40.0)
        assert "衰老日报" in card
        assert "42.5" in card
        assert "40" in card
        assert "免责声明" in card

    def test_generate_daily_card_with_previous(self):
        card = generate_daily_card(42.5, 40.0, previous_biological_age=41.0)
        assert "较上次变化" in card

    def test_generate_daily_card_accelerated(self):
        card = generate_daily_card(48.0, 40.0)
        assert "偏快" in card or "加速" in card

    def test_generate_trend_card(self):
        history = [
            ("2026-05-01", 42.0), ("2026-05-02", 42.1),
            ("2026-05-03", 41.9), ("2026-05-04", 42.2),
        ]
        card = generate_trend_card(history, days=7)
        assert "衰老趋势" in card
        assert "42.0" in card

    def test_generate_trend_card_insufficient(self):
        history = [("2026-05-01", 42.0)]
        card = generate_trend_card(history)
        assert "数据不足" in card

    def test_generate_trend_card_empty(self):
        card = generate_trend_card([])
        assert "暂无历史数据" in card

    def test_generate_intervention_reminder(self):
        card = generate_intervention_reminder("运动计划", 2.5, days_remaining=15)
        assert "运动计划" in card
        assert "2.5" in card
        assert "15" in card

    def test_generate_intervention_reminder_low_adherence(self):
        card = generate_intervention_reminder("Diet", 1.0, adherence_pct=50)
        assert "需要改善" in card
