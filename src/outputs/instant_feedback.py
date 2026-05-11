"""Daily aging feedback card generator.

Produces compact, embeddable aging feedback suitable for daily
check-ins, notification cards, and health tracking apps.
"""

from datetime import datetime
from typing import Any, Dict, Optional


def generate_daily_card(
    biological_age: float,
    chronological_age: float,
    age_acceleration: Optional[float] = None,
    confidence: float = 0.5,
    previous_biological_age: Optional[float] = None,
    notes: Optional[str] = None,
) -> str:
    """Generate a compact daily aging feedback card.

    Args:
        biological_age: Current biological age.
        chronological_age: Current chronological age.
        age_acceleration: Computed acceleration (auto-computed if None).
        confidence: Confidence score 0-1.
        previous_biological_age: Previous measurement for trend.
        notes: Optional personalized notes.

    Returns:
        Markdown card string.
    """
    if age_acceleration is None:
        age_acceleration = biological_age - chronological_age

    now = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"## 衰老日报 {now}",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 日历年龄 | {chronological_age:.0f} 岁 |",
        f"| 生物年龄 | {biological_age:.1f} 岁 |",
        f"| 衰老速度 | {age_acceleration:+.1f} 岁 |",
        f"| 置信度 | {confidence:.0%} |",
    ]

    if previous_biological_age is not None:
        trend = biological_age - previous_biological_age
        trend_icon = "↗" if trend > 0.2 else ("↘" if trend < -0.2 else "→")
        lines.append(f"| 较上次变化 | {trend:+.1f} 岁 {trend_icon} |")
    lines.append("")

    # Daily tip based on acceleration
    tips = _get_daily_tip(age_acceleration)
    if tips:
        lines.append(f"### 今日提示")
        lines.append(tips)
        lines.append("")

    if notes:
        lines.append(f"> {notes}")
        lines.append("")

    lines.append("---")
    lines.append("*免责声明: 不构成医疗诊断*")
    return "\n".join(lines)


def generate_trend_card(
    history: list,
    days: int = 7,
) -> str:
    """Generate a weekly trend summary card.

    Args:
        history: List of (date_str, biological_age) tuples.
        days: Number of days to include.

    Returns:
        Markdown trend card string.
    """
    if not history:
        return "# 暂无历史数据"

    recent = history[-days:]
    if len(recent) < 2:
        return (
            f"## 衰老趋势 (7日)\n\n"
            f"数据不足，需要至少2天数据来显示趋势。"
        )

    first_age = recent[0][1]
    last_age = recent[-1][1]
    trend = last_age - first_age
    trend_icon = "↗" if trend > 0.2 else ("↘" if trend < -0.2 else "→")

    lines = [
        f"## 衰老趋势 ({len(recent)}日)",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 起始生物年龄 | {first_age:.1f} 岁 |",
        f"| 当前生物年龄 | {last_age:.1f} 岁 |",
        f"| {len(recent)}日变化 | {trend:+.1f} 岁 {trend_icon} |",
        "",
    ]

    # Daily breakdown
    lines.append("### 每日记录")
    for date_str, bio_age in recent:
        lines.append(f"- {date_str}: {bio_age:.1f} 岁")
    lines.append("")

    lines.append("---")
    lines.append("*免责声明: 不构成医疗诊断*")
    return "\n".join(lines)


def generate_intervention_reminder(
    intervention_name: str,
    target_age_reduction: float,
    days_remaining: int = 30,
    adherence_pct: float = 100.0,
) -> str:
    """Generate an intervention adherence reminder card.

    Args:
        intervention_name: Name of the intervention.
        target_age_reduction: Expected age reduction.
        days_remaining: Days remaining in the program.
        adherence_pct: Current adherence percentage.

    Returns:
        Markdown reminder card string.
    """
    adherence_status = "优秀" if adherence_pct >= 90 else ("良好" if adherence_pct >= 70 else "需要改善")

    return (
        f"## 干预提醒: {intervention_name}\n\n"
        f"| 指标 | 数值 |\n"
        f"|------|------|\n"
        f"| 目标效果 | {target_age_reduction:.1f} 岁减少 |\n"
        f"| 剩余天数 | {days_remaining} 天 |\n"
        f"| 依从性 | {adherence_pct:.0f}% ({adherence_status}) |\n"
        f"\n"
        f"💡 保持依从性是获得最佳效果的关键。\n"
        f"\n---\n"
        f"*免责声明: 不构成医疗诊断*"
    )


def _get_daily_tip(acceleration: float) -> str:
    """Get a daily health tip based on aging acceleration.

    Args:
        acceleration: Age acceleration in years.

    Returns:
        Tip string.
    """
    if acceleration > 3:
        return (
            "您当前的衰老速度偏快。建议：\n"
            "- 保持每天30分钟中等强度运动\n"
            "- 确保7-8小时睡眠\n"
            "- 减少加工食品摄入\n"
            "- 定期体检跟踪关键指标"
        )
    elif acceleration > 0:
        return (
            "维持健康生活方式对延缓衰老至关重要：\n"
            "- 均衡饮食，多摄入蔬菜水果\n"
            "- 适度运动，每周150分钟\n"
            "- 管理压力，保持社交活跃"
        )
    elif acceleration > -2:
        return (
            "您的衰老速度正常。继续保持：\n"
            "- 规律的作息和饮食习惯\n"
            "- 定期体检监测关键指标"
        )
    else:
        return (
            "您的衰老速度较慢，做得不错！\n"
            "- 分享您的健康习惯\n"
            "- 帮助家人和朋友一起保持健康"
        )
