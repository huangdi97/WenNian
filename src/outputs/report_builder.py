"""Markdown report builder for the WenNian longevity assessment.

Generates structured markdown reports including biological age summary,
per-clock details, biomarker contributions, disclaimers, and methodology
transparency sections.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# Clock display name mapping
CLOCK_DISPLAY_NAMES: Dict[str, str] = {
    "phenoage": "PhenoAge",
    "kdm": "KDM",
    "dnn": "DNN",
    "lifeclock": "LifeClock",
}


def build_markdown_report(
    integrated_report: Any,
    brand_config: Optional[Dict[str, Any]] = None,
) -> str:
    """Build a full markdown longevity assessment report.

    Args:
        integrated_report: An IntegratedReport or compatible object with
            chronological_age, biological_age, age_acceleration,
            confidence, clock_results, and warnings.
        brand_config: Optional brand customization dict with keys:
            name, logo, theme_color, disclaimer.

    Returns:
        Complete markdown report string.
    """
    brand = brand_config or {}
    brand_name = brand.get("name", "问年 WenNian")
    disclaimer = brand.get(
        "disclaimer",
        "本报告不构成医疗诊断，所有结果仅供健康参考。如有健康问题请咨询执业医师。",
    )

    chron_age = getattr(integrated_report, "chronological_age", 0)
    bio_age = getattr(integrated_report, "biological_age", 0)
    acceleration = getattr(integrated_report, "age_acceleration", 0)
    confidence = getattr(integrated_report, "confidence", 0)
    lower = getattr(integrated_report, "lower_bound", None)
    upper = getattr(integrated_report, "upper_bound", None)
    clock_results = getattr(integrated_report, "clock_results", [])
    warnings = getattr(integrated_report, "warnings", [])

    ensemble_std = getattr(integrated_report, "ensemble_std", None)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: List[str] = []
    lines.append(f"# {brand_name} — 衰老评估报告")
    lines.append(f"> 生成时间: {now}")
    lines.append("")
    lines.append("## 一、生物年龄总结")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 日历年龄 | {chron_age:.1f} 岁 |")
    lines.append(f"| **生物年龄** | **{bio_age:.1f} 岁** |")
    lines.append(f"| 衰老加速 | {acceleration:+.1f} 岁 |")
    lines.append(f"| 置信度 | {confidence:.0%} |")
    if lower is not None and upper is not None:
        lines.append(f"| 置信区间 | [{lower:.1f}, {upper:.1f}] |")
    if ensemble_std is not None:
        lines.append(f"| 集成标准差 | {ensemble_std:.1f} 岁 |")
    lines.append("")
    lines.append("### 解读")
    if abs(acceleration) < 2:
        lines.append(f"您的生物年龄与日历年龄基本一致 (±{abs(acceleration):.1f}岁)。")
    elif acceleration > 0:
        lines.append(f"您的生物年龄比日历年龄大 **{acceleration:.1f} 岁**，提示存在加速衰老趋势，建议关注生活方式和定期体检。")
    else:
        lines.append(f"您的生物年龄比日历年龄年轻 **{abs(acceleration):.1f} 岁**，表明当前衰老速率较慢。")
    lines.append("")
    lines.append("## 二、各时钟详细结果")
    lines.append("")
    lines.append("| 时钟名称 | 预测年龄 | 置信度 | 状态 |")
    lines.append("|----------|----------|--------|------|")
    for cr in clock_results:
        name = getattr(cr, "clock_name", "unknown")
        display = CLOCK_DISPLAY_NAMES.get(name, name)
        pred = getattr(cr, "predicted_age", 0)
        conf = getattr(cr, "confidence", 0)
        status = getattr(cr, "status", "error")
        status_icon = "✓" if status == "ok" else "✗"
        lines.append(f"| {display} | {pred:.1f} | {conf:.0%} | {status_icon} {status} |")
    lines.append("")
    if warnings:
        lines.append("## 三、数据质量提示")
        lines.append("")
        for w in warnings:
            lines.append(f"- ⚠ {w}")
        lines.append("")

    # Stage 2: Organ aging and main driver analysis
    organ_ages = getattr(integrated_report, "organ_ages", None)
    top_drivers = getattr(integrated_report, "top_drivers", None)
    if organ_ages or top_drivers:
        lines.append("## 三、器官衰老雷达")
        lines.append("")
        if organ_ages:
            lines.append("| 器官系统 | 估计年龄 | 异步偏差 | 拐点年龄 |")
            lines.append("|----------|----------|----------|----------|")
            for oa in organ_ages:
                if isinstance(oa, dict):
                    lines.append(
                        f"| {oa.get('organ','?')} | {oa.get('estimated_age',0):.1f}岁 | "
                        f"{oa.get('asynchrony_score',0):+.1f}岁 | {oa.get('inflection_age',0)}岁 |"
                    )
                else:
                    lines.append(
                        f"| {getattr(oa,'organ','?')} | {getattr(oa,'estimated_age',0):.1f}岁 | "
                        f"{getattr(oa,'asynchrony_score',0):+.1f}岁 | {getattr(oa,'inflection_age',0)}岁 |"
                    )
            lines.append("")
        if top_drivers:
            lines.append("### 主驱动维度")
            for i, td in enumerate(top_drivers, 1):
                lines.append(
                    f"{i}. **{td['organ']}**: 估计年龄{td['estimated_age']}岁, "
                    f"偏差{td['age_gap']:+.1f}岁, 优先度: {td['priority']}"
                )
            lines.append("")

    lines.append("## 四、方法学透明")
    lines.append("")
    lines.append("本报告基于以下模型与文献：")
    lines.append("- PhenoAge v1.0 (Levine 2018): 9项血检指标的线性衰老预测模型")
    lines.append("- KDM v1.0 (Klemera & Doubal 2006): 马氏距离衰老评估法")
    lines.append("- DNN v1.0: 三层全连接神经网络衰老时钟")
    lines.append("- LifeClock v1.0: 基于临床参考范围的简化衰老评估")
    lines.append("")
    lines.append("融合算法：加权平均融合，权重基于各时钟置信度。")
    if ensemble_std is not None:
        lines.append(f"集成标准差: {ensemble_std:.1f}岁 (时钟间一致性指标)")
    lines.append("")
    lines.append("### 干预优先级建议")
    lines.append("")
    if top_drivers:
        for i, td in enumerate(top_drivers, 1):
            lines.append(f"{i}. **{td['organ']}** (偏差{td['age_gap']:+.1f}岁, 优先度: {td['priority']})")
        lines.append("")
    else:
        lines.append("暂无器官级数据，请补充更多生物标志物进行器官衰老评估。")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**免责声明**: {disclaimer}")
    lines.append("")
    lines.append(f"© {datetime.now().year} {brand_name}")
    return "\n".join(lines)


def build_compact_report(data: Dict[str, Any]) -> str:
    """Build a compact, single-paragraph report suitable for cards or summaries.

    Args:
        data: Dictionary with keys: biological_age, chronological_age,
              age_acceleration, confidence.

    Returns:
        Short markdown-formatted summary string.
    """
    bio = data.get("biological_age", 0)
    chron = data.get("chronological_age", 0)
    accel = data.get("age_acceleration", 0)
    conf = data.get("confidence", 0)
    direction = "快于" if accel > 0 else ("慢于" if accel < 0 else "一致于")
    return (
        f"**生物年龄 {bio:.1f} 岁** | 日历年龄 {chron:.1f} 岁 | "
        f"衰老速度{direction}日历年龄 ({accel:+.1f}岁) | "
        f"置信度 {conf:.0%} | "
        "免责声明：不构成医疗诊断"
    )


def build_debate_section(debate_result: Dict[str, Any]) -> str:
    """Build a markdown section for the debate log.

    Args:
        debate_result: Debate output from run_debate_pipeline.

    Returns:
        Markdown string with debate summary.
    """
    lines: List[str] = []
    lines.append("## 辩论日志")
    lines.append("")
    lines.append(f"**命题**: {debate_result.get('proposition', '')}")
    lines.append("")

    rounds = debate_result.get("rounds", [])
    for rd in rounds:
        lines.append(f"### 第{rd.get('round_number', '?')}轮")
        lines.append(f"**裁判评分**: {rd.get('judge_score', 0):.1f}/10")
        lines.append(f"**裁判意见**: {rd.get('judge_rationale', '')}")
        lines.append("")

        pro_args = rd.get("pro_arguments", [])
        con_args = rd.get("con_arguments", [])
        if pro_args:
            lines.append("**正方论据**:")
            for a in pro_args:
                claim = a.get("claim", "") if isinstance(a, dict) else getattr(a, "claim", "")
                refs = a.get("references", []) if isinstance(a, dict) else getattr(a, "references", [])
                ref_str = ", ".join(refs[:2]) if refs else ""
                lines.append(f"- {claim}" + (f" [{ref_str}]" if ref_str else ""))
            lines.append("")
        if con_args:
            lines.append("**反方论据**:")
            for a in con_args:
                claim = a.get("claim", "") if isinstance(a, dict) else getattr(a, "claim", "")
                refs = a.get("references", []) if isinstance(a, dict) else getattr(a, "references", [])
                ref_str = ", ".join(refs[:2]) if refs else ""
                lines.append(f"- {claim}" + (f" [{ref_str}]" if ref_str else ""))
            lines.append("")

    winner = debate_result.get("winner", "")
    final_score = debate_result.get("final_score", 0)
    consensus = debate_result.get("consensus_notes", "")
    lines.append(f"**最终裁决**: {winner}方胜出 (得分{final_score:.1f}/10)")
    lines.append(f"**共识**: {consensus}")
    lines.append("")

    return "\n".join(lines)
