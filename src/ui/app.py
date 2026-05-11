"""WenNian Gradio web interface - 3-tab MVP UI (self-contained).

Provides interactive access to core WenNian capabilities:
1. Full Spectrum aging assessment
2. Health interview
3. White-label report generation

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