"""
cross_basin_figure.py — Visual companion to Table 9 (Section 4.8), the
supplementary cross-basin transferability check.

Added 2026-08-13 because a reviewer asked for "proof" of the cross-basin
check beyond a data table: this plots the AR(1) coefficient (phi_1, with its
95% confidence interval from the model's own standard errors) for discharge
and rainfall at all three basins -- the primary Conecuh basin plus the two
supplementary basins from cross_basin_check.py -- and colours each bar by
whether that fit's Ljung-Box residual test passes (green) or fails (red).
This is the same evidence already in Table 9 and data/results.json /
data/cross_basin_check.json, shown as a figure instead of only as numbers.

Run:
    python cross_basin_figure.py
Output: figures/Fig9_CrossBasinCheck.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).parent
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

_GREEN = "#2ca02c"
_RED = "#d62728"

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "font.size": 10.5,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def main():
    results = json.loads((PROJECT_ROOT / "data" / "results.json").read_text(encoding="utf-8"))
    cross = json.loads((PROJECT_ROOT / "data" / "cross_basin_check.json").read_text(encoding="utf-8"))

    basins = [
        {
            "key": "conecuh", "label": "Conecuh, AL\n(primary basin)",
            "discharge": {
                "phi1": results["variables"]["discharge"]["phi"][0],
                "se1": results["variables"]["discharge"]["standard_errors"]["phi"][0],
                "lb_p": results["variables"]["discharge"]["diagnostics"]["ljung_box"]["pvalue"],
            },
            "rainfall": {
                "phi1": results["variables"]["rainfall"]["phi"][0],
                "se1": results["variables"]["rainfall"]["standard_errors"]["phi"][0],
                "lb_p": results["variables"]["rainfall"]["diagnostics"]["ljung_box"]["pvalue"],
            },
        },
        {
            "key": "10023000", "label": "Great Basin, NV/UT\n(arid interior West)",
            "discharge": {
                "phi1": cross["10023000"]["discharge"]["phi"][0],
                "se1": cross["10023000"]["discharge"]["phi_se"][0],
                "lb_p": cross["10023000"]["discharge"]["ljung_box_pvalue"],
            },
            "rainfall": {
                "phi1": cross["10023000"]["rainfall"]["phi"][0],
                "se1": cross["10023000"]["rainfall"]["phi_se"][0],
                "lb_p": cross["10023000"]["rainfall"]["ljung_box_pvalue"],
            },
        },
        {
            "key": "01013500", "label": "New England\n(humid continental)",
            "discharge": {
                "phi1": cross["01013500"]["discharge"]["phi"][0],
                "se1": cross["01013500"]["discharge"]["phi_se"][0],
                "lb_p": cross["01013500"]["discharge"]["ljung_box_pvalue"],
            },
            "rainfall": {
                "phi1": cross["01013500"]["rainfall"]["phi"][0],
                "se1": cross["01013500"]["rainfall"]["phi_se"][0],
                "lb_p": cross["01013500"]["rainfall"]["ljung_box_pvalue"],
            },
        },
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    x = np.arange(len(basins))

    for ax, var, title in zip(axes, ["discharge", "rainfall"], ["Discharge", "Rainfall"]):
        phi1 = np.array([b[var]["phi1"] for b in basins])
        se1 = np.array([b[var]["se1"] if b[var]["se1"] is not None else np.nan for b in basins])
        lb_p = [b[var]["lb_p"] for b in basins]
        ci = 1.96 * se1
        colors = [_GREEN if p is not None and p > 0.05 else _RED for p in lb_p]

        ax.bar(x, phi1, yerr=ci, color=colors, alpha=0.85, capsize=5,
               error_kw={"linewidth": 1.3})
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([b["label"] for b in basins], fontsize=9)
        ax.set_ylabel(r"AR(1) coefficient $\phi_1$ (95% CI)")
        ax.set_title(f"{title}: does AR(1) persistence transfer across basins?", fontsize=10.5, pad=12)

        for xi, (p1, s1, p) in enumerate(zip(phi1, se1, lb_p)):
            label = f"$\\phi_1$={p1:.2f}\nLB p={p:.3f}" if p is not None else f"$\\phi_1$={p1:.2f}"
            y = p1 + (1.96 * s1 if not np.isnan(s1) else 0)
            offset = 0.06 if y >= 0 else -0.06
            va = "bottom" if y >= 0 else "top"
            ax.annotate(label, (xi, y + offset), ha="center", va=va, fontsize=8)

        ax.set_ylim(min(-0.6, float(np.nanmin(phi1 - ci)) - 0.15),
                    max(1.5, float(np.nanmax(phi1 + ci)) + 0.4))

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=_GREEN, alpha=0.85, label="Ljung-Box passes (p > 0.05): residuals look like noise"),
        plt.Rectangle((0, 0), 1, 1, color=_RED, alpha=0.85, label="Ljung-Box fails (p ≤ 0.05): residual autocorrelation remains"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=1, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Supplementary cross-basin check: same identification + estimation procedure,\napplied unmodified to two basins outside the primary study area", fontsize=11.5)
    fig.tight_layout(rect=[0, 0.04, 1, 0.90])

    out = FIG_DIR / "Fig9_CrossBasinCheck.png"
    fig.savefig(out, bbox_inches="tight")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
