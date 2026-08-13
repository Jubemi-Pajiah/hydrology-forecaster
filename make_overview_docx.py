"""
make_overview_docx.py — Generate a plain-English project overview .docx.

The actual content (all section text, Q&A, bullets, code blocks) lives in
overview_render.py, shared with make_overview_pdf.py, so this .docx cannot
drift from the PDF the way two independently hand-written documents can --
both are rendered from the exact same calls, just by different backends.
This file only implements the python-docx-backed rendering target.

Run:  python make_overview_docx.py
Output: documents/Project_Overview.docx
"""

import json
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from overview_render import render

_DOCS = Path(__file__).parent / "documents"
_DOCS.mkdir(exist_ok=True)
OUTPUT = _DOCS / "Project_Overview.docx"

_RES = Path(__file__).parent / "data" / "results.json"
try:
    with open(_RES) as _f:
        R = json.load(_f)
except Exception:
    R = {}

NAVY = RGBColor(30, 58, 95)
BLUE = RGBColor(37, 99, 235)
GREY = RGBColor(90, 100, 115)
TEXT = RGBColor(30, 41, 59)
LIGHT = "EFF6FF"
CODEBG = "F4F6F8"
FONT = "Calibri"
MONO = "Consolas"


def _shade(paragraph, hex_color):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_color)
    pPr.append(shd)


class DocxTarget:
    def __init__(self):
        self.doc = Document()
        section = self.doc.sections[0]
        section.left_margin = section.right_margin = Cm(2.2)
        section.top_margin = section.bottom_margin = Cm(1.8)
        style = self.doc.styles["Normal"]
        style.font.name = FONT
        style.font.size = Pt(11)

    # ── building blocks (the target interface overview_render.py uses) ────────
    def title_block(self, title, subtitle, facts, note):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(60)
        r = p.add_run(title)
        r.bold = True
        r.font.size = Pt(26)
        r.font.color.rgb = NAVY
        r.font.name = FONT

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(16)
        r = p.add_run(subtitle)
        r.font.size = Pt(13)
        r.font.color.rgb = BLUE
        r.font.name = FONT

        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "10")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "2563EB")
        pBdr.append(bottom)
        pPr.append(pBdr)
        p.paragraph_format.space_after = Pt(16)

        for line in facts:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(line)
            r.font.size = Pt(11)
            r.font.color.rgb = GREY
            r.font.name = FONT

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(18)
        _shade(p, LIGHT)
        r = p.add_run(note)
        r.italic = True
        r.font.size = Pt(11)
        r.font.color.rgb = NAVY
        r.font.name = FONT

    def add_page(self):
        self.doc.add_page_break()

    def h1(self, num, title):
        p = self.doc.add_paragraph()
        _shade(p, LIGHT)
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(10)
        r = p.add_run(f"  {num}.  {title}")
        r.bold = True
        r.font.size = Pt(15)
        r.font.color.rgb = NAVY
        r.font.name = FONT

    def h2(self, title):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(title)
        r.bold = True
        r.font.size = Pt(12)
        r.font.color.rgb = BLUE
        r.font.name = FONT

    def body(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(text)
        r.font.size = Pt(11)
        r.font.color.rgb = TEXT
        r.font.name = FONT

    def note(self, text):
        p = self.doc.add_paragraph()
        _shade(p, LIGHT)
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(text)
        r.italic = True
        r.font.size = Pt(10.5)
        r.font.color.rgb = NAVY
        r.font.name = FONT

    def bullet(self, text, label=None):
        p = self.doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(6)
        if label:
            r = p.add_run(label + " ")
            r.bold = True
            r.font.size = Pt(11)
            r.font.color.rgb = TEXT
            r.font.name = FONT
        r = p.add_run(text)
        r.font.size = Pt(11)
        r.font.color.rgb = TEXT
        r.font.name = FONT

    def qa(self, question, answer, pointer):
        p = self.doc.add_paragraph()
        _shade(p, LIGHT)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run("Q: " + question)
        r.bold = True
        r.font.size = Pt(11.5)
        r.font.color.rgb = NAVY
        r.font.name = FONT

        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(answer)
        r.font.size = Pt(11)
        r.font.color.rgb = TEXT
        r.font.name = FONT

        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(10)
        r = p.add_run("-> Where to look: " + pointer)
        r.italic = True
        r.font.size = Pt(10)
        r.font.color.rgb = BLUE
        r.font.name = FONT

    def code(self, lines):
        p = self.doc.add_paragraph()
        _shade(p, CODEBG)
        p.paragraph_format.space_after = Pt(10)
        for i, line in enumerate(lines):
            r = p.add_run("  " + line)
            r.font.name = MONO
            r.font.size = Pt(9.5)
            r.font.color.rgb = TEXT
            if i < len(lines) - 1:
                p.add_run().add_break()


def build():
    t = DocxTarget()
    render(t, R)
    t.doc.save(OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    build()
