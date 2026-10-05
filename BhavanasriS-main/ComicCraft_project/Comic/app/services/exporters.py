from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fpdf import FPDF
from PIL import Image

from app.config import BASE_DIR, EXPORTS_DIR


def _pdf_text(value: str) -> str:
    """Keep built-in FPDF Helvetica safe when an LLM returns Unicode punctuation."""
    return str(value).encode("latin-1", errors="replace").decode("latin-1")


def _local_image_path(web_path: str) -> Path:
    relative = web_path.removeprefix("/static/")
    path = BASE_DIR / "static" / relative
    if not path.exists():
        raise FileNotFoundError(f"Panel image not found: {path}")
    return path


def save_pdf(layout: list[dict]) -> str:
    if not layout:
        raise ValueError("Cannot export an empty comic.")

    filename = (
        f"comiccraft_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
        f"{uuid4().hex[:6]}.pdf"
    )

    output = EXPORTS_DIR / filename

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    for panel in layout:
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 18)
        pdf.multi_cell(
            0,
            10,
            f"Panel {panel['panel_number']}: {_pdf_text(panel['title'])}",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        image_path = _local_image_path(panel["image_path"])

        with Image.open(image_path) as img:
            width, height = img.size

        max_w, max_h = 180, 105
        scale = min(max_w / width, max_h / height)

        pdf.image(
            str(image_path),
            x=(210 - width * scale) / 2,
            w=width * scale,
        )

        pdf.ln(5)

        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(
            0,
            6,
            _pdf_text(panel["scene_description"]),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(
            0,
            6,
            _pdf_text(panel["caption"]),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(
            0,
            6,
            _pdf_text(panel["narration"]),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "I", 11)
        pdf.multi_cell(
            0,
            6,
            _pdf_text(panel["dialogue"]),
            new_x="LMARGIN",
            new_y="NEXT",
        )

    pdf.output(str(output))

    return f"/static/exports/{filename}"