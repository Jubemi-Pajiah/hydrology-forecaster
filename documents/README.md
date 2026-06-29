# Documents — what to send to the supervisor

These are the finished, up-to-date deliverables for the project
*"Computer Hydrological Forecasting"* (discharge-only ARIMA approach, Conecuh River).

| File | What it is |
|------|------------|
| `Chapter3_4_5_Hydrological_Forecasting.docx` | The written thesis — Chapter 3 (Methodology), Chapter 4 (Results & Discussion), Chapter 5 (Conclusion) and References. All figures are **embedded** in the document. |
| `Project_Overview.pdf` | A plain-English overview of the project (simple version, technical version, and how to use the software). |

## Before sending the thesis as a PDF
The thesis is a `.docx`. To produce a faithful PDF on this machine:
1. Open `Chapter3_4_5_Hydrological_Forecasting.docx` in **WPS Writer**.
2. Press **Ctrl+A** then **F9** to refresh any fields (page numbers, etc.).
3. Export to PDF.

## Regenerating these files
Both files are generated from code and the latest results, so do not hand-edit them.
To rebuild after a model change:
```bash
python run_pipeline.py        # refreshes data/results.json + figures/
python write_document.py      # rebuilds the .docx here
python make_overview_pdf.py   # rebuilds the .pdf here
```
