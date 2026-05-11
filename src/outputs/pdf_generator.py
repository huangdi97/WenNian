"""PDF report generator for WenNian longevity assessments.

Generates branded PDF documents from markdown content using ReportLab,
with Chinese font support via system font search.
"""

import io
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.exceptions import ComputationError

# Attempt to import ReportLab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, KeepTogether,
    )
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus.paragraph import Paragraph
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# Common Chinese font search paths on different platforms
_FONT_SEARCH_PATHS: List[str] = [
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]


def _find_chinese_font() -> Optional[str]:
    """Search for an available Chinese-capable font on the system.

    Returns:
        Absolute path to the first found font, or None.
    """
    for path in _FONT_SEARCH_PATHS:
        if os.path.exists(path):
            return path
    # Fallback: search Windows fonts directory for any .ttc or .ttf
    if os.name == "nt":
        win_fonts = Path("C:/Windows/Fonts")
        if win_fonts.exists():
            for f in win_fonts.glob("msyh*"):
                return str(f)
            for f in win_fonts.glob("sim*"):
                return str(f)
    return None


def _register_font(font_path: Optional[str] = None) -> str:
    """Register a Chinese-capable font with ReportLab.

    Args:
        font_path: Path to font file, or None to auto-detect.

    Returns:
        The font family name to use in styles.

    Raises:
        ComputationError: If no suitable font is found.
    """
    if not REPORTLAB_AVAILABLE:
        raise ComputationError("ReportLab is not installed")

    font_path = font_path or _find_chinese_font()
    if font_path is None:
        raise ComputationError(
            "No Chinese font found. Install a Chinese font (e.g., Microsoft YaHei, "
            "SimSun, WQY Micro Hei) and set the FONT_PATH environment variable."
        )

    try:
        pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
        pdfmetrics.registerFont(TTFont("ChineseFontBold", font_path))
        return "ChineseFont"
    except Exception as e:
        raise ComputationError(f"Failed to register font {font_path}: {e}") from e


def generate_pdf(
    markdown_content: str,
    brand_config: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None,
    font_path: Optional[str] = None,
) -> bytes:
    """Generate a branded PDF from markdown report content.

    Args:
        markdown_content: The full markdown report text.
        brand_config: Brand customization dictionary.
        output_path: Optional file path to save the PDF. If None, returns bytes.
        font_path: Optional path to a Chinese font file.

    Returns:
        PDF content as bytes.
    """
    if not REPORTLAB_AVAILABLE:
        raise ComputationError(
            "ReportLab is required for PDF generation. Install with: pip install reportlab"
        )

    brand = brand_config or {}
    brand_name = brand.get("name", "问年 WenNian")
    theme_hex = brand.get("theme_color", "#2E86AB")
    disclaimer = brand.get(
        "disclaimer",
        "本报告不构成医疗诊断，所有结果仅供健康参考。如有健康问题请咨询执业医师。",
    )

    font_family = _register_font(font_path)
    theme_color = HexColor(theme_hex)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
        title=f"{brand_name} 衰老评估报告",
        author=brand_name,
    )

    # Build styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CNTitle",
        parent=styles["Title"],
        fontName=font_family,
        fontSize=20,
        textColor=theme_color,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "CNH2",
        parent=styles["Heading2"],
        fontName=font_family,
        fontSize=14,
        textColor=theme_color,
        spaceBefore=12,
        spaceAfter=6,
    )
    h3_style = ParagraphStyle(
        "CNH3",
        parent=styles["Heading3"],
        fontName=font_family,
        fontSize=12,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "CNBody",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=10,
        leading=16,
        spaceAfter=4,
    )
    table_cell_style = ParagraphStyle(
        "CNTableCell",
        parent=body_style,
        fontSize=9,
        leading=14,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=body_style,
        fontSize=8,
        textColor=HexColor("#888888"),
        alignment=TA_CENTER,
    )

    story: List = []

    # Title page header
    story.append(Paragraph(brand_name, title_style))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(HRFlowable(width="100%", color=theme_color, thickness=1))
    story.append(Spacer(1, 4 * mm))

    # Parse markdown into sections
    sections = _parse_markdown_sections(markdown_content)

    for section_title, section_body in sections:
        if section_title:
            story.append(Paragraph(section_title, h2_style if section_title.startswith("一") or section_title.startswith("二") or section_title.startswith("三") or section_title.startswith("四") else h3_style))

        # Check for tables
        lines = section_body.strip().split("\n")
        table_lines = []
        in_table = False
        body_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(stripped)
            elif stripped.startswith("|---"):
                continue  # skip separator lines
            else:
                if in_table and table_lines:
                    story.append(_build_pdf_table(table_lines, font_family, theme_color, table_cell_style))
                    table_lines = []
                    in_table = False
                    story.append(Spacer(1, 2 * mm))
                if stripped:
                    body_lines.append(stripped)

        if in_table and table_lines:
            story.append(_build_pdf_table(table_lines, font_family, theme_color, table_cell_style))
            story.append(Spacer(1, 2 * mm))

        for bl in body_lines:
            if bl.startswith("- "):
                story.append(Paragraph(f"&bull; {bl[2:]}", body_style))
            elif bl.startswith("> "):
                story.append(Paragraph(f"<i>{bl[2:]}</i>", body_style))
            elif bl.startswith("**") and bl.endswith("**"):
                story.append(Paragraph(f"<b>{bl[2:-2]}</b>", body_style))
            else:
                # Clean markdown bold markers: **text** → <b>text</b>
                clean = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', bl)
                story.append(Paragraph(clean, body_style))

    # Disclaimer footer on every page
    def add_page_footer(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont(font_family, 7)
        canvas_obj.setFillColor(HexColor("#999999"))
        canvas_obj.drawCentredString(
            A4[0] / 2.0,
            10 * mm,
            disclaimer,
        )
        canvas_obj.drawRightString(
            A4[0] - 20 * mm,
            10 * mm,
            f"第 {canvas_obj.getPageNumber()} 页",
        )
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=add_page_footer, onLaterPages=add_page_footer)

    pdf_bytes = buf.getvalue()
    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes


def _parse_markdown_sections(content: str) -> List[tuple]:
    """Parse markdown into sections based on ## and ### headings.

    Args:
        content: Raw markdown string.

    Returns:
        List of (title, body) tuples.
    """
    sections: List[tuple] = []
    current_title = ""
    current_body: List[str] = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_body:
                sections.append((current_title, "\n".join(current_body)))
            current_title = line[3:].strip()
            current_body = []
        elif line.startswith("### "):
            if current_body:
                sections.append((current_title, "\n".join(current_body)))
            current_title = line[4:].strip()
            current_body = []
        elif line.startswith("# ") and not current_title:
            current_title = line[2:].strip()
        else:
            current_body.append(line)

    if current_body:
        sections.append((current_title, "\n".join(current_body)))

    return sections


def _build_pdf_table(
    table_lines: List[str],
    font_family: str,
    theme_color: Any,
    cell_style: Any,
) -> Table:
    """Convert markdown table lines to a ReportLab Table flowable.

    Args:
        table_lines: List of markdown table rows (| col1 | col2 |).
        font_family: Registered font family name.
        theme_color: Theme color for the header row.
        cell_style: ParagraphStyle for table cells.

    Returns:
        A ReportLab Table flowable.
    """
    if not table_lines:
        return Spacer(1, 0)

    rows = []
    for i, line in enumerate(table_lines):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if i == 0:
            # Header row
            rows.append([
                Paragraph(f"<b>{c}</b>", ParagraphStyle("CNTH", cell_style, fontSize=9, textColor=HexColor("#FFFFFF")))
                for c in cells
            ])
        else:
            rows.append([Paragraph(c, cell_style) for c in cells])

    col_widths = [(A4[0] - 40 * mm) / max(len(rows[0]), 1)] * len(rows[0]) if rows else None
    t = Table(rows, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), theme_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F5F5F5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t
