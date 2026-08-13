"""
make_overview_pdf.py — Generate a plain-English project overview PDF.

The actual content (all section text, Q&A, bullets, code blocks) lives in
overview_render.py, shared with make_overview_docx.py, so the PDF and the
.docx version can't drift apart the way two independently hand-written
documents can. This file only implements the fpdf-backed rendering target.

Run:  python make_overview_pdf.py
Output: documents/Project_Overview.pdf
"""

import json
from pathlib import Path
from fpdf import FPDF

from overview_render import render

_DOCS = Path(__file__).parent / "documents"
_DOCS.mkdir(exist_ok=True)
OUTPUT = str(_DOCS / "Project_Overview.pdf")

# Load pipeline results so the overview always reflects the latest run
_RES = Path(__file__).parent / "data" / "results.json"
try:
    with open(_RES) as _f:
        R = json.load(_f)
except Exception:
    R = {}

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY   = (30, 58, 95)
BLUE   = (37, 99, 235)
GREY   = (90, 100, 115)
LIGHT  = (239, 246, 255)
CODEBG = (244, 246, 248)
TEXT   = (30, 41, 59)


def clean(s: str) -> str:
    """Replace non-latin-1 characters so the core PDF fonts can render them."""
    repl = {
        "³": "^3", "²": "^2", "→": "->", "—": "-",
        "–": "-", "₀": "0", "°": " deg", "≈": "~",
        "≥": ">=", "≤": "<=", "•": "-", "×": "x",
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "…": "...", "­": "", " ": " ", "φ": "phi", "θ": "theta",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 8, "Computer Hydrological Forecasting - Project Overview",
                  align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    # ── building blocks (this is the target interface overview_render.py uses) ─
    def title_block(self, title, subtitle, facts, note):
        self.ln(14)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "B", 24)
        self.multi_cell(0, 12, clean(title), align="C")
        self.ln(2)
        self.set_text_color(*BLUE)
        self.set_font("Helvetica", "", 13)
        self.multi_cell(0, 8, clean(subtitle), align="C")
        self.ln(6)
        self.set_draw_color(*BLUE)
        self.set_line_width(0.6)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(8)
        self.set_text_color(*GREY)
        self.set_font("Helvetica", "", 11)
        for line in facts:
            self.cell(0, 7, clean(line), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
        self.set_fill_color(*LIGHT)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "I", 11)
        self.multi_cell(0, 7, clean(note), align="C", fill=True)

    def h1(self, num, title):
        self.ln(2)
        self.set_fill_color(*LIGHT)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 11, clean(f"  {num}.  {title}"), fill=True, new_x="LMARGIN",
                  new_y="NEXT")
        self.ln(3)

    def h2(self, title):
        self.ln(1)
        self.set_text_color(*BLUE)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, clean(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_text_color(*TEXT)
        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 6, clean(text))
        self.ln(2)

    def note(self, text):
        self.set_fill_color(*LIGHT)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "I", 10.5)
        self.multi_cell(0, 6, clean(text), fill=True)
        self.ln(2)

    def bullet(self, text, label=None):
        self.set_text_color(*TEXT)
        self.set_font("Helvetica", "", 11)
        self.cell(6, 6, clean("-"))
        if label:
            self.set_font("Helvetica", "B", 11)
            self.write(6, clean(label + " "))
            self.set_font("Helvetica", "", 11)
        self.write(6, clean(text))
        self.ln(8)

    def qa(self, question, answer, pointer):
        self.set_x(self.l_margin)
        self.set_fill_color(*LIGHT)
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "B", 11.5)
        self.multi_cell(0, 6.5, clean("Q: " + question), fill=True)
        self.set_x(self.l_margin)
        self.set_text_color(*TEXT)
        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 6, clean(answer))
        self.set_x(self.l_margin)
        self.set_text_color(*BLUE)
        self.set_font("Helvetica", "I", 10)
        self.multi_cell(0, 6, clean("-> Where to look: " + pointer))
        self.ln(4)

    def code(self, lines):
        self.set_fill_color(*CODEBG)
        self.set_text_color(*TEXT)
        self.set_font("Courier", "", 10)
        for ln in lines:
            self.cell(0, 6, clean("  " + ln), fill=True, new_x="LMARGIN",
                      new_y="NEXT")
        self.ln(3)


def build():
    pdf = PDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(20, 18, 20)
    pdf.add_page()

    render(pdf, R)

    pdf.output(OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    build()
