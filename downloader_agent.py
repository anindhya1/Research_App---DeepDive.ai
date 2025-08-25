# downloader_agent.py
from pathlib import Path
from typing import Dict, Optional
import base64, io, os, textwrap
from agents import Agent, function_tool, ModelSettings
from writer_agent import ReportData

# Where PDFs will be written (Flask will serve from /static)
EXPORT_DIR = Path("static/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# --- Minimal, robust Markdown -> PDF (plain text rendering) ---
# Uses reportlab to paginate/wrap text; renders the raw Markdown nicely.
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

def _write_text_pdf(md_text: str, out_path: Path, *, title: Optional[str] = None):
    c = canvas.Canvas(str(out_path), pagesize=LETTER)
    width, height = LETTER
    margin = 72  # 1in
    x = margin
    y = height - margin

    # Basic title header (optional)
    if title:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, title)
        y -= 24

    c.setFont("Helvetica", 11)

    # Simple word-wrapping measured against page width
    max_width = width - 2 * margin
    lines = []
    for paragraph in md_text.splitlines() or [""]:
        # treat code fences and blank lines as-is
        if paragraph.strip() == "":
            lines.append("")
            continue
        # soft wrap to ~95 chars, then measure and split if needed
        soft = textwrap.wrap(paragraph, width=95) or [paragraph]
        for ln in soft:
            # further split if still too wide
            while c.stringWidth(ln, "Helvetica", 11) > max_width and " " in ln:
                # binary search would be nicer; keep it simple
                cut = len(ln)
                while c.stringWidth(ln[:cut], "Helvetica", 11) > max_width and cut > 0:
                    cut -= 1
                # backtrack to last space
                sp = ln.rfind(" ", 0, cut)
                if sp <= 0:
                    break
                lines.append(ln[:sp])
                ln = ln[sp + 1 :]
            lines.append(ln)

    for ln in lines:
        if y < margin:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - margin
        c.drawString(x, y, ln)
        y -= 14  # line height

    c.save()

@function_tool
def md_to_pdf(markdown_text: str, filename: str = "report.pdf", title: Optional[str] = None) -> Dict[str, str]:
    """
    Convert Markdown text to a PDF and return info the UI can use.

    Returns:
      {
        "status": "success",
        "filename": "report.pdf",
        "path": "/abs/path/to/report.pdf",
        "url": "/static/exports/report.pdf",
        "pdf_base64": "..."   # optional convenience
      }
    """
    # Normalize filename
    stem = Path(filename).with_suffix(".pdf").name
    out_path = EXPORT_DIR / stem

    # Render (plain Markdown text; robust everywhere)
    _write_text_pdf(markdown_text or "", out_path, title=title)

    # Optional: base64 for direct downloads from API
    data_b64 = base64.b64encode(out_path.read_bytes()).decode("ascii")
    return {
        "status": "success",
        "filename": out_path.name,
        "path": str(out_path.resolve()),
        "url": f"/static/exports/{out_path.name}",
        "pdf_base64": data_b64,
    }

INSTRUCTIONS = (
    "You turn the given report text (in Markdown) into a downloadable PDF. "
    "Use your tool to create a PDF and return its download info."
)

download_agent = Agent(
    name="DownloaderAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[md_to_pdf],
    model_settings=ModelSettings(tool_choice="required"),  # ensure tool is called
)
