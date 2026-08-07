# Documents — what to send to the supervisor

These are the finished, up-to-date deliverables for the project
*"Computer Hydrological Forecasting"* (discharge-only ARIMA approach, Conecuh River).

| File | What it is |
|------|------------|
| `Computer_Hydrological_Forecasting_Full_Report.docx` | **The complete report — send this one.** Title page and front matter, Chapters 1–5, References, and the code Appendix. Formatted to `PROJECT TEMPLATE_Civil.docx`. Figures embedded. |
| `Project_Overview.pdf` | A plain-English overview of the project (simple version, technical version, and how to use the software). |
| `Chapter3_4_5_Hydrological_Forecasting.docx` | Superseded — Chapters 3–5 only, before the merge. Kept for reference. |

### Source material used to build the full report
| File | Role |
|------|------|
| `PROJECT TEMPLATE_Civil.docx` | Departmental template the full report is formatted to. |
| `190402003_ benedict ugbodaga (2).docx` | The author's Chapter 1–3 draft. **Note:** it describes the superseded rainfall–runoff model, so Chapters 1–2 were rewritten onto the ARIMA framing and its Chapter 3 was replaced. |
| `180402008 Busari Hassanat FYP Final Final Final Final (1).pdf` | Reference for the appendix layout (`APPENDIX` → `APPENDIX-A/B/C…`, each with a one-line caption then the code). |

## Before sending the report as a PDF
The report is a `.docx`. To produce a faithful PDF on this machine:
1. Open `Computer_Hydrological_Forecasting_Full_Report.docx` in **WPS Writer**.
2. Press **Ctrl+A** then **F9**. This is required, not optional: it builds the
   Table of Contents, the List of Figures and the List of Tables, which are
   Word fields and are empty until refreshed.
3. Check that the front matter is numbered i, ii, iii… and the body from 1.
4. Export to PDF.

## Regenerating these files
Everything here is generated from code and the latest results, so do not
hand-edit the `.docx`. To rebuild after a model change:
```bash
python run_pipeline.py        # refreshes data/results.json + figures/
python write_full_report.py   # rebuilds the full Chapter 1-5 report here
python make_overview_pdf.py   # rebuilds Project_Overview.pdf here
```
`write_full_report.py` reads every number from `data/results.json` and pulls the
appendix listings straight out of `src/*.py`, so neither the results quoted in
Chapter 4 nor the code in the Appendix can drift from the pipeline.
