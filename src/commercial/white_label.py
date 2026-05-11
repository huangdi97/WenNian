"""White-label batch PDF generator with ZIP packaging.

Generates branded PDF reports for arbitrary numbers of subjects,
with per-subject brand customization and ZIP download support.
"""

import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.outputs.report_builder import build_markdown_report
from src.outputs.pdf_generator import generate_pdf
from src.integrator import AgingIntegrator
from src.clocks import ClockRegistry
from src.clocks.phenoage import PhenoAgeClock
from src.clocks.kdm import KDMClock
from src.clocks.dnn import DNNClock
from src.clocks.lifeclock import LifeClock


def _setup_integrator() -> AgingIntegrator:
    registry = ClockRegistry()
    registry.clear()
    registry.register(phenoage=PhenoAgeClock())
    registry.register(kdm=KDMClock())
    registry.register(dnn=DNNClock())
    registry.register(lifeclock=LifeClock())
    return AgingIntegrator(registry=registry)


def generate_batch_reports(
    subjects: List[Dict[str, Any]],
    brand_config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Generate assessment reports for a batch of subjects.

    Args:
        subjects: List of dicts, each with 'subject_id' and 'biomarkers'.
        brand_config: Brand customization dict (name, logo, theme_color, disclaimer).
        output_dir: Optional directory to save individual PDFs.

    Returns:
        List of result dicts with subject_id, report_md, pdf_path, biological_age.
    """
    integrator = _setup_integrator()
    brand = brand_config or {"name": "问年 WenNian"}

    results = []
    for subject in subjects:
        subject_id = subject.get("subject_id", f"SUBJ-{len(results)+1:04d}")
        biomarkers = subject.get("biomarkers", {})

        try:
            result = integrator.assess(biomarkers)
            report_md = build_markdown_report(result, brand_config=brand)

            pdf_path = None
            if output_dir:
                out = Path(output_dir)
                out.mkdir(parents=True, exist_ok=True)
                pdf_path = str(out / f"{subject_id}_report.pdf")
                generate_pdf(report_md, brand_config=brand, output_path=pdf_path)

            results.append({
                "subject_id": subject_id,
                "report_md": report_md,
                "pdf_path": pdf_path,
                "biological_age": result.biological_age,
                "chronological_age": result.chronological_age,
                "age_acceleration": result.age_acceleration,
                "confidence": result.confidence,
                "status": "success",
            })
        except Exception as e:
            results.append({
                "subject_id": subject_id,
                "report_md": "",
                "pdf_path": None,
                "biological_age": 0,
                "status": f"error: {e}",
            })

    return results


def create_zip_package(
    results: List[Dict[str, Any]],
    brand_config: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Create a ZIP file containing all reports and a summary CSV.

    Args:
        results: List of results from generate_batch_reports.
        brand_config: Brand config for the summary report.

    Returns:
        ZIP file content as bytes.
    """
    brand = brand_config or {"name": "问年 WenNian"}
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        csv_lines = ["subject_id,chronological_age,biological_age,age_acceleration,confidence,status"]
        for r in results:
            csv_lines.append(
                f"{r['subject_id']},{r.get('chronological_age',0)},"
                f"{r.get('biological_age',0)},{r.get('age_acceleration',0)},"
                f"{r.get('confidence',0)},{r['status']}"
            )
        zf.writestr("summary.csv", "\n".join(csv_lines))

        for r in results:
            if r["status"] == "success" and r.get("report_md"):
                pdf_bytes = generate_pdf(r["report_md"], brand_config=brand)
                zf.writestr(f"reports/{r['subject_id']}.pdf", pdf_bytes)

        zf.writestr("README.txt", (
            f"问年 WenNian 批量评估报告\n"
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"品牌: {brand.get('name', 'WenNian')}\n"
            f"免责声明: 不构成医疗诊断\n"
        ))

    return buf.getvalue()


def apply_brand_template(
    base_config: Dict[str, Any],
    template: str = "default",
) -> Dict[str, Any]:
    """Apply a brand template to the base configuration.

    Args:
        base_config: Base brand configuration.
        template: Template name ('default', 'medical', 'corporate', 'minimal').

    Returns:
        Updated brand configuration.
    """
    templates = {
        "default": {"theme_color": "#2E86AB"},
        "medical": {"theme_color": "#1B6B4A", "disclaimer": "本报告仅供临床参考，不替代专业医疗诊断。"},
        "corporate": {"theme_color": "#003366"},
        "minimal": {"theme_color": "#333333"},
    }
    template_cfg = templates.get(template, templates["default"])
    result = dict(base_config)
    result.update(template_cfg)
    return result
