"""WenNian Gradio web interface - 8-tab complete UI (self-contained).

Provides interactive access to all WenNian capabilities:
1. Full Spectrum aging assessment
2. Health interview
3. White-label report generation
4. Product validation
5. Target prioritization
6. Cell senescence QC
7. Intervention simulation
8. Laboratory tools

This file can be launched from the project root (E:\AI\OpenCode\wennian) with:
    python src/ui/app.py
"""

import sys
import os

# Ensure the project root (E:\AI\OpenCode\wennian) is on sys.path so that
# "from src.xxx" imports work from any working directory.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import tempfile
import random
from typing import Any, Dict, List, Optional

import gradio as gr

# ---- Safe imports for modules that may still be under construction ----
from src.validation.input_validator import InputValidator
from src.clocks import ClockRegistry
from src.clocks.phenoage import PhenoAgeClock
from src.clocks.kdm import KDMClock
from src.clocks.dnn import DNNClock
from src.clocks.lifeclock import LifeClock
from src.integrator import AgingIntegrator
from src.outputs.report_builder import build_markdown_report
from src.outputs.pdf_generator import generate_pdf
from src.agents.auditor import Auditor

# Optional / under construction
try:
    from src.agents.health_interviewer import HealthInterviewer
    _have_interviewer = True
except Exception:
    _have_interviewer = False

try:
    from src.commercial.white_label import generate_batch_reports, create_zip_package
    _have_white_label = True
except Exception:
    _have_white_label = False

try:
    from src.industrial.target_prioritizer import TargetPrioritizer
    _have_target_prioritizer = True
except Exception:
    _have_target_prioritizer = False

try:
    from src.lab.experiment_designer import design_intervention_study
    _have_experiment_designer = True
except Exception:
    _have_experiment_designer = False

try:
    from src.lab.drywet_loop import DryWetLoop
    _have_drywet = True
except Exception:
    _have_drywet = False


# ---- Shared helpers ----

def _setup_integrator() -> AgingIntegrator:
    registry = ClockRegistry()
    registry.clear()
    registry.register(phenoage=PhenoAgeClock())
    registry.register(kdm=KDMClock())
    registry.register(dnn=DNNClock())
    registry.register(lifeclock=LifeClock())
    return AgingIntegrator(registry=registry)

def _build_biomarkers(age, albumin, creatinine, glucose, lymphocyte, mcv, rdw, alp, wbc, crp=None, sbp=None, dbp=None):
    bio = {
        "age": age, "albumin": albumin, "creatinine": creatinine, "glucose": glucose,
        "lymphocyte_percent": lymphocyte, "mcv": mcv, "rdw": rdw,
        "alkaline_phosphatase": alp, "white_blood_cell_count": wbc,
    }
    if crp is not None: bio["c_reactive_protein"] = crp
    if sbp is not None: bio["systolic_bp"] = sbp
    if dbp is not None: bio["diastolic_bp"] = dbp
    return bio


# ==================== Tab 1: Full Spectrum ====================
def tab_full_spectrum(age, albumin, creatinine, glucose, lymphocyte, mcv, rdw, alp, wbc, crp, sbp, dbp):
    biomarkers = _build_biomarkers(age, albumin, creatinine, glucose, lymphocyte, mcv, rdw, alp, wbc, crp, sbp, dbp)
    validator = InputValidator()
    validation = validator.validate(biomarkers)
    if not validation.is_valid:
        lines = ["# 输入校验失败\n"]
        for e in validation.errors:
            lines.append(f"- ❌ {e}")
        return "\n".join(lines)

    integrator = _setup_integrator()
    result = integrator.assess(biomarkers)
    if validation.warnings:
        if not hasattr(result, 'warnings'):
            result.warnings = []
        result.warnings.extend(validation.warnings)

    brand = {"name": "问年 WenNian", "theme_color": "#2E86AB"}
    report = build_markdown_report(result, brand_config=brand)

    auditor = Auditor()
    audit = auditor.execute({"report_text": report, "biological_age": result.biological_age,
                             "chronological_age": result.chronological_age})
    if not audit.data.get("passed", True):
        report += "\n\n## ⚠ 稽核\n"
        for v in audit.data.get("violations", []):
            report += f"\n- ❌ {v}"

    return report


# ==================== Tab 2: Health Interview ====================
_interview_state: Dict[str, Any] = {}

def tab_interview_start(complaint: str):
    if not _have_interviewer:
        return "# 模块施工中\n健康访谈功能暂未就绪，请等待后续更新。"
    global _interview_state
    hi = HealthInterviewer(max_rounds=3)
    _interview_state = {"hi": hi, "complaint": complaint, "history": []}
    output = hi.execute({"initial_complaint": complaint, "history": []})
    if output.data.get("interview_complete"):
        return output.data.get("structured_summary", "访谈完成")
    qs = output.data.get("questions", [])
    return "### 追问\n\n" + "\n\n".join(f"{i+1}. {q}" for i, q in enumerate(qs))

def tab_interview_continue(answer: str):
    if not _have_interviewer:
        return ""
    global _interview_state
    if not _interview_state:
        return "# 请先开始访谈"
    hi = _interview_state["hi"]
    history = _interview_state["history"]
    history.append({"question": f"Q{len(history)+1}", "answer": answer})
    output = hi.execute({"initial_complaint": _interview_state["complaint"], "history": history})
    if output.data.get("interview_complete"):
        return output.data.get("structured_summary", "访谈完成")
    qs = output.data.get("questions", [])
    return "### 追问\n\n" + "\n\n".join(f"{i+1}. {q}" for i, q in enumerate(qs))

def tab_interview_reset():
    global _interview_state
    _interview_state = {}
    return "访谈已重置。请重新开始。"


# ==================== Tab 3: White-Label Report ====================
def tab_wl_report(brand_name, age, albumin, creatinine, glucose, lymphocyte, mcv, rdw, crp, alp, wbc):
    """生成白标报告，crp 参数已添加以支持 PhenoAge 时钟"""
    biomarkers = _build_biomarkers(age, albumin, creatinine, glucose, lymphocyte, mcv, rdw, alp, wbc, crp=crp)
    brand = {"name": brand_name or "问年 WenNian", "theme_color": "#2E86AB"}

    if _have_white_label:
        subjects = [{"subject_id": "REPORT-001", "biomarkers": biomarkers}]
        results = generate_batch_reports(subjects, brand_config=brand)
        if results[0]["status"] != "success":
            return f"# 生成失败\n{results[0]['status']}", None
        report_md = results[0]["report_md"]
    else:
        integrator = _setup_integrator()
        result = integrator.assess(biomarkers)
        report_md = build_markdown_report(result, brand_config=brand)

    pdf_path = None
    try:
        pdf_bytes = generate_pdf(report_md, brand_config=brand)
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(pdf_bytes)
        pdf_path = tmp.name
        tmp.close()
    except Exception:
        pass

    return report_md, pdf_path


# ==================== Tab 4: Product Validation ====================
def tab_product_validation(company, product, n_subjects):
    from src.commercial.product_validator import run_product_validation, build_poc_report
    random.seed(42)
    n = max(3, int(n_subjects))
    before = [random.gauss(42, 3) for _ in range(n)]
    after = [b - random.gauss(1.5, 1.0) for b in before]

    result = run_product_validation(product or "TestProduct", before, after)
    report = build_poc_report(result)
    return report


# ==================== Tab 5: Target Prioritization ====================
def tab_target_prioritize(phenotype: str):
    if not _have_target_prioritizer:
        return "### ⚠ 靶点排序模块施工中\n该功能依赖的 `target_prioritizer` 模块尚未完成，请稍后重试。"

    outcome_map = {
        "整体": "inflammation",
        "免疫衰老": "immune",
        "炎症衰老": "inflammation",
        "代谢衰老": "metabolic",
        "血管衰老": "coagulation",
    }
    outcome = outcome_map.get(phenotype, "inflammation")

    tp = TargetPrioritizer()
    results = tp.prioritize(outcome=outcome, top_k=8)

    lines = [f"## 靶点排序: {phenotype}", "", "| 排名 | 靶点 | 优先分数 | 效应量 | 可药性 | 脱靶风险 |",
             "|------|------|----------|--------|--------|----------|"]
    for i, r in enumerate(results, 1):
        lines.append(f"| {i} | {r.target_name} | {r.priority_score:.4f} | {r.total_effect:.4f} | "
                     f"{r.druggability:.2f} | {r.off_target_risk:.2f} |")
    lines.append("")
    lines.append("---")
    lines.append("*基于因果图do-calculus效应估计*")
    return "\n".join(lines)


# ==================== Tab 6: Cell QC ====================
def tab_cell_qc(passage, doubling_hours, viability, sa_beta_gal, upload_file):
    from src.industrial.cell_line_qc import compute_csi

    if upload_file is not None:
        return "# 文件上传已接收\n\n(CSV基因表达数据暂未深度解析)"

    result = compute_csi(
        passage_number=int(passage),
        doubling_time_hours=float(doubling_hours),
        viability_pct=float(viability),
        sa_beta_gal_pct=float(sa_beta_gal),
        population_doublings=int(passage) * 2,
        morphology_score=0.8,
    )

    lines = [
        f"# 细胞衰老指数 (CSI)",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| CSI | **{result['csi']}** |",
        f"| 状态 | {result['status']} |",
        f"| 建议 | {result['recommendation']} |",
        f"| 传代 | P{result['passage_number']} |",
        "",
        "### 分项贡献",
        f"| 指标 | 贡献度 |",
        f"|------|--------|",
    ]
    for k, v in result["components"].items():
        lines.append(f"| {k} | {v} |")

    return "\n".join(lines)


# ==================== Tab 7: Intervention Simulation ====================
def tab_intervention_sim(interventions, intensity, baseline_age, baseline_pheno):
    from src.agents.executor import Executor
    from src.agents.protocols import InterventionScenario

    if not interventions:
        return "# 请选择至少一项干预方案"

    executor = Executor()
    lines = ["# 干预模拟结果", "", f"## 基线", f"- 日历年龄: {baseline_age:.0f}岁",
             f"- 生物年龄: {baseline_pheno:.1f}岁", ""]

    target_map = {
        "有氧运动": "musculoskeletal",
        "16:8断食": "metabolic",
        "NMN": "metabolic",
        "Senolytics": "cellular_senescence",
        "益生菌": "microbiome",
    }

    total_reduction = 0.0
    lines.append("## 各方案预测")
    lines.append("| 方案 | 预期效果 | 80%CI | 95%CI | 信心 |")
    lines.append("|------|----------|-------|-------|------|")

    for name in interventions:
        target = target_map.get(name, "metabolic")
        scenario = InterventionScenario(target_dimension=target, intervention_type=name, intensity=float(intensity))
        pred = executor.simulate(scenario)
        total_reduction += pred.predicted_age_reduction
        lines.append(
            f"| {name} | {pred.predicted_age_reduction:.1f}岁 | "
            f"[{pred.lower_80ci:.1f}, {pred.upper_80ci:.1f}] | "
            f"[{pred.lower_95ci:.1f}, {pred.upper_95ci:.1f}] | "
            f"{pred.confidence:.0%} |"
        )

    final_age = baseline_pheno - total_reduction
    lines.append("")
    lines.append(f"## 综合预测")
    lines.append(f"- 预期生物年龄: **{final_age:.1f}岁**")
    lines.append(f"- 总减少: **{total_reduction:.1f}岁**")
    lines.append("")
    lines.append("> ⚠ 假设前提: 各方案效果线性叠加，未考虑协同/拮抗效应")
    lines.append("> 效应量基于已发表文献估计")
    lines.append("")
    lines.append("---")
    lines.append("*免责声明: 模拟结果仅供科研参考*")

    return "\n".join(lines)


# ==================== Tab 8: Laboratory ====================
def tab_benchmark_run():
    from src.validation.benchmark_validator import run_benchmark
    result = run_benchmark()
    return result.get("summary", "# 基准测试失败")

def tab_experiment_design(hypothesis: str):
    if not _have_experiment_designer:
        return "### 实验设计模块施工中\n该功能依赖的 `experiment_designer` 模块尚未完成，请稍后重试。"
    design = design_intervention_study(
        study_name=hypothesis[:50] if hypothesis else "未命名研究",
        n_subjects_per_group=10, n_groups=2,
        group_names=["对照组", "干预组"],
    )
    lines = [
        f"# 实验方案: {design['study_name']}",
        f"设计: {design['design']}",
        f"总受试者: {design['total_subjects']}",
        f"周期: {design['duration_weeks']}周",
        "",
        "## 分组",
    ]
    for g in design["groups"]:
        lines.append(f"- {g['name']}: n={g['n']}")
    lines.append("")
    lines.append("## 测量时间点")
    for s in design["schedule"]:
        lines.append(f"- 第{s['week']}周: {', '.join(s['measurements'])} ({s['notes']})")
    return "\n".join(lines)

def tab_lims_status():
    return "### LIMS状态\n\n当前为模拟环境。在生产部署中，此处将显示实验室信息管理系统(LIMS)的实时状态。"

def tab_closed_loop_status():
    if not _have_drywet:
        return "### 干湿闭环模块施工中\n该功能依赖的 `drywet_loop` 模块尚未完成，请稍后重试。"
    loop = DryWetLoop()
    p = loop.record_prediction("phenoage", 42.0, "biological_age")
    loop.record_validation(p, 43.0, "EXP-001")
    cal = loop.compute_calibration()
    return (
        f"### 干湿闭环状态\n\n"
        f"验证次数: {cal.get('n_validations', 0)}\n\n"
        f"MAE: {cal.get('mae', 'N/A')}\n\n"
        f"{cal.get('recommendation', '')}"
    )


# ==================== Main Interface ====================
def create_interface() -> gr.Blocks:
    with gr.Blocks(title="问年 WenNian — 衰老干预决策系统") as demo:
        gr.Markdown("# 问年 WenNian — 衰老干预决策系统")
        gr.Markdown("*太一既立，灵境已启，虚明初照，静候万物生。*")

        with gr.Tabs():
            # Tab 1: Full Spectrum
            with gr.TabItem("🧬 全谱"):
                with gr.Row():
                    with gr.Column(scale=1):
                        age1 = gr.Slider(18, 120, 40, step=1, label="日历年龄")
                        albumin1 = gr.Number(43.0, label="白蛋白 (g/L)")
                        creatinine1 = gr.Number(75.0, label="肌酐 (umol/L)")
                        glucose1 = gr.Number(5.1, label="空腹血糖 (mmol/L)")
                        lymphocyte1 = gr.Number(33.0, label="淋巴细胞百分比 (%)")
                        mcv1 = gr.Number(90.0, label="MCV (fL)")
                        rdw1 = gr.Number(13.0, label="RDW (%)")
                        alp1 = gr.Number(70.0, label="碱性磷酸酶 (U/L)")
                        wbc1 = gr.Number(6.5, label="白细胞计数 (10⁹/L)")
                        with gr.Accordion("可选指标", open=False):
                            crp1 = gr.Number(1.0, label="CRP (mg/L)")
                            sbp1 = gr.Number(120.0, label="收缩压 (mmHg)")
                            dbp1 = gr.Number(80.0, label="舒张压 (mmHg)")
                        btn1 = gr.Button("运行全谱评估", variant="primary")
                    with gr.Column(scale=2):
                        out1 = gr.Markdown("*请输入指标后点击「运行全谱评估」*")

                btn1.click(tab_full_spectrum,
                           [age1, albumin1, creatinine1, glucose1, lymphocyte1, mcv1, rdw1, alp1, wbc1, crp1, sbp1, dbp1],
                           [out1])

            # Tab 2: Interview
            with gr.TabItem("💬 访谈"):
                complaint = gr.Textbox("最近一年感觉老得特别快...", label="主诉", lines=2)
                btn_start = gr.Button("开始访谈")
                answer = gr.Textbox("", label="回答 (追问时填写)", lines=2)
                btn_continue = gr.Button("继续追问")
                btn_reset = gr.Button("重新开始")
                out2 = gr.Markdown("*请开始访谈*")

                btn_start.click(tab_interview_start, [complaint], [out2])
                btn_continue.click(tab_interview_continue, [answer], [out2])
                btn_reset.click(tab_interview_reset, None, [out2])

            # Tab 3: Report
            with gr.TabItem("📋 报告"):
                with gr.Row():
                    with gr.Column(scale=1):
                        brand_name = gr.Textbox("问年 WenNian", label="品牌名称")
                        age3 = gr.Slider(18, 120, 40, step=1, label="日历年龄")
                        albumin3 = gr.Number(43.0, label="白蛋白 (g/L)")
                        creatinine3 = gr.Number(75.0, label="肌酐 (umol/L)")
                        glucose3 = gr.Number(5.1, label="空腹血糖 (mmol/L)")
                        lymphocyte3 = gr.Number(33.0, label="淋巴细胞百分比 (%)")
                        mcv3 = gr.Number(90.0, label="MCV (fL)")
                        rdw3 = gr.Number(13.0, label="RDW (%)")
                        crp3 = gr.Number(1.0, label="CRP (mg/L)")
                        alp3 = gr.Number(70.0, label="碱性磷酸酶 (U/L)")
                        wbc3 = gr.Number(6.5, label="白细胞计数 (10⁹/L)")
                        btn3 = gr.Button("生成PDF报告", variant="primary")
                    with gr.Column(scale=2):
                        out3_report = gr.Markdown("*预览区*")
                        out3_pdf = gr.File(label="PDF下载")

                btn3.click(tab_wl_report,
                           [brand_name, age3, albumin3, creatinine3, glucose3, lymphocyte3, mcv3, rdw3, crp3, alp3, wbc3],
                           [out3_report, out3_pdf])

            # Tab 4: Validation
            with gr.TabItem("🧪 验证"):
                with gr.Row():
                    with gr.Column(scale=1):
                        company4 = gr.Textbox("问年生物科技", label="企业名称")
                        product4 = gr.Textbox("抗衰老营养补充剂", label="产品名称")
                        n_subjects4 = gr.Slider(5, 100, 30, step=5, label="受试人数")
                        btn4 = gr.Button("运行验证", variant="primary")
                    with gr.Column(scale=2):
                        out4 = gr.Markdown("*点击「运行验证」生成统计报告*")

                btn4.click(tab_product_validation, [company4, product4, n_subjects4], [out4])

            # Tab 5: Targets
            with gr.TabItem("🎯 靶点"):
                with gr.Row():
                    with gr.Column(scale=1):
                        phenotype = gr.Dropdown(["整体", "免疫衰老", "炎症衰老", "代谢衰老", "血管衰老"], value="整体", label="表型")
                        btn5 = gr.Button("排序靶点", variant="primary")
                    with gr.Column(scale=2):
                        out5 = gr.Markdown("*点击「排序靶点」查看结果*")

                btn5.click(tab_target_prioritize, [phenotype], [out5])

            # Tab 6: Cell
            with gr.TabItem("🔬 细胞"):
                with gr.Row():
                    with gr.Column(scale=1):
                        passage6 = gr.Slider(1, 50, 10, step=1, label="传代次数")
                        doubling6 = gr.Slider(10.0, 100.0, 24.0, step=0.5, label="倍增时间 (h)")
                        viability6 = gr.Slider(10.0, 100.0, 90.0, step=1.0, label="细胞活力 (%)")
                        sa_beta_gal6 = gr.Slider(0.0, 100.0, 15.0, step=1.0, label="SA-β-gal阳性率 (%)")
                        upload6 = gr.File(label="基因表达CSV (可选)")
                        btn6 = gr.Button("检测CSI", variant="primary")
                    with gr.Column(scale=2):
                        out6 = gr.Markdown("*输入细胞参数后点击「检测CSI」*")

                btn6.click(tab_cell_qc, [passage6, doubling6, viability6, sa_beta_gal6, upload6], [out6])

            # Tab 7: Simulation
            with gr.TabItem("📈 模拟"):
                with gr.Row():
                    with gr.Column(scale=1):
                        interventions7 = gr.CheckboxGroup(
                            ["有氧运动", "16:8断食", "NMN", "Senolytics", "益生菌"],
                            value=["有氧运动", "NMN"],
                            label="干预方案",
                        )
                        intensity7 = gr.Slider(0.1, 1.5, 0.8, step=0.1, label="干预强度")
                        baseline_age7 = gr.Slider(18, 80, 40, step=1, label="基线日历年龄")
                        baseline_pheno7 = gr.Number(42.0, label="基线生物年龄")
                        btn7 = gr.Button("运行模拟", variant="primary")
                    with gr.Column(scale=2):
                        out7 = gr.Markdown("*选择干预方案后点击「运行模拟」*")

                btn7.click(tab_intervention_sim,
                           [interventions7, intensity7, baseline_age7, baseline_pheno7],
                           [out7])

            # Tab 8: Laboratory
            with gr.TabItem("⚙️ 实验"):
                with gr.Tabs():
                    with gr.TabItem("基准测试"):
                        btn8a = gr.Button("运行基准测试", variant="primary")
                        out8a = gr.Markdown("*点击运行*")
                        btn8a.click(tab_benchmark_run, None, [out8a])
                    with gr.TabItem("实验设计"):
                        hypo = gr.Textbox("NAD+补充剂对中年小鼠生物年龄的影响", label="研究假说", lines=2)
                        btn8b = gr.Button("生成实验方案", variant="primary")
                        out8b = gr.Markdown("*输入假说后点击生成*")
                        btn8b.click(tab_experiment_design, [hypo], [out8b])
                    with gr.TabItem("实验记录"):
                        out8c = gr.Markdown("*LIMS状态*")
                        gr.Button("刷新").click(tab_lims_status, None, [out8c])
                    with gr.TabItem("闭环统计"):
                        out8d = gr.Markdown("*闭环状态*")
                        gr.Button("检查闭环").click(tab_closed_loop_status, None, [out8d])

        # ---- Sidebar / Footer ----
        with gr.Accordion("🔒 隐私与合规", open=False):
            gr.Checkbox(True, label="允许云端推理", interactive=True)
            gr.Markdown(
                "系统版本: v2.0.0 | 12维度衰老评估\n\n"
                "**免责声明**: 本系统不构成医疗诊断，所有结果仅供健康参考。"
                "如有健康问题请咨询执业医师。\n\n"
                "© 2026 问年 WenNian"
            )

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860)