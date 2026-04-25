#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
TABLE_PATH = ROOT / "data" / "readiness_matrix.csv"
FIG_DIR = ROOT / "figures"
SOURCE_DATA_DIR = ROOT / "source_data"
SOURCE_DATA_PATH = SOURCE_DATA_DIR / "Figure2_readiness_map_source_data.csv"


COLOR_MAP = {
    "Perception AI": "#3b78c0",
    "Judgment AI": "#e06a47",
    "Communication/Workflow AI": "#2f9147",
}

SIZE_MAP = {
    "Moderate": 420,
    "High": 760,
}

Y_MAP = {
    "Moderate": 0.0,
    "High": 1.0,
}


POINT_OFFSETS = {
    "Prostate MRI reader assistance": (-0.12, 0.08),
    "Prostate digital pathology": (0.12, 0.08),
    "Selected bladder cystoscopy systems": (-0.08, 0.08),
    "PSMA PET quantification and lesion support": (-0.12, 0.09),
    "Micro-ultrasound lesion localization": (0.12, 0.09),
    "Renal radiomics and renal-mass prediction": (0.00, 0.00),
    "UTI triage and stewardship support": (-0.12, -0.08),
    "Functional urology and neurourology prediction": (-0.12, -0.08),
    "Surgical video analytics and feedback": (0.10, 0.02),
    "MDT and pathway decision support": (0.12, -0.08),
    "Semen analysis automation": (-0.10, 0.08),
    "AI-assisted sperm selection for ICSI": (0.08, -0.08),
    "Male infertility and sperm-retrieval prediction": (0.12, 0.00),
    "ED and sexual-function outcome prediction": (0.00, -0.10),
    "Ambient documentation support": (0.00, 0.00),
    "Retrieval-grounded guideline support": (0.00, 0.00),
}


LABEL_SPECS = {
    "Prostate MRI reader assistance": {"text": "Prostate MRI", "dx": 0.06, "dy": 0.07, "ha": "left", "va": "bottom"},
    "Prostate digital pathology": {"text": "Prostate pathology", "dx": 0.05, "dy": -0.05, "ha": "left", "va": "center"},
    "Selected bladder cystoscopy systems": {"text": "Bladder cystoscopy", "dx": 0.05, "dy": 0.07, "ha": "left", "va": "bottom"},
    "PSMA PET quantification and lesion support": {"text": "PSMA PET", "dx": -0.12, "dy": 0.08, "ha": "right", "va": "bottom"},
    "Micro-ultrasound lesion localization": {"text": "Micro-ultrasound", "dx": -0.06, "dy": 0.20, "ha": "center", "va": "bottom"},
    "Renal radiomics and renal-mass prediction": {"text": "Renal radiomics", "dx": 0.05, "dy": -0.05, "ha": "left", "va": "center"},
    "UTI triage and stewardship support": {"text": "UTI triage", "dx": 0.04, "dy": 0.06, "ha": "left", "va": "bottom"},
    "Functional urology and neurourology prediction": {"text": "Functional urology", "dx": -0.14, "dy": -0.13, "ha": "right", "va": "center"},
    "Surgical video analytics and feedback": {"text": "Surgical video", "dx": 0.00, "dy": 0.10, "ha": "center", "va": "bottom"},
    "MDT and pathway decision support": {"text": "MDT/pathway support", "dx": -0.12, "dy": -0.17, "ha": "right", "va": "center"},
    "Semen analysis automation": {"text": "Semen analysis", "dx": 0.00, "dy": 0.08, "ha": "center", "va": "bottom"},
    "AI-assisted sperm selection for ICSI": {"text": "ICSI sperm selection", "dx": 0.07, "dy": -0.09, "ha": "left", "va": "center"},
    "Male infertility and sperm-retrieval prediction": {"text": "Male infertility\nprediction", "dx": 0.14, "dy": 0.16, "ha": "left", "va": "center"},
    "ED and sexual-function outcome prediction": {"text": "ED prediction", "dx": 0.05, "dy": -0.06, "ha": "left", "va": "center"},
    "Ambient documentation support": {"text": "Ambient documentation", "dx": 0.05, "dy": 0.04, "ha": "left", "va": "center"},
    "Retrieval-grounded guideline support": {"text": "Retrieval-grounded LLMs", "dx": 0.22, "dy": -0.18, "ha": "left", "va": "center"},
}


def build_plot_frame(df: pd.DataFrame) -> pd.DataFrame:
    plot_df = df.copy()
    plot_df["x"] = plot_df["Highest_Validation_Stage"].astype(float)
    plot_df["y"] = plot_df["Consequence_of_Error"].map(Y_MAP).astype(float)
    plot_df["size"] = plot_df["Likely_Workflow_Value"].map(SIZE_MAP).astype(float)
    plot_df["color"] = plot_df["Task_Class"].map(COLOR_MAP)

    offsets = plot_df["Clinical_Task"].map(POINT_OFFSETS)
    plot_df["x"] = plot_df["x"] + offsets.map(lambda v: v[0] if isinstance(v, tuple) else 0.0)
    plot_df["y"] = plot_df["y"] + offsets.map(lambda v: v[1] if isinstance(v, tuple) else 0.0)
    return plot_df


def add_label(ax, x: float, y: float, spec: dict) -> None:
    tx = x + spec["dx"]
    ty = y + spec["dy"]
    ann = ax.annotate(
        spec["text"],
        xy=(x, y),
        xytext=(tx, ty),
        textcoords="data",
        ha=spec["ha"],
        va=spec["va"],
        fontsize=9.4,
        color="#222222",
        arrowprops=dict(arrowstyle="-", color="#7d7d7d", lw=1.1, shrinkA=3, shrinkB=6),
        zorder=5,
    )
    ann.set_path_effects([pe.withStroke(linewidth=3.0, foreground="white")])


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(TABLE_PATH)
    df.to_csv(SOURCE_DATA_PATH, index=False)
    plot_df = build_plot_frame(df)

    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.set_facecolor("white")
    ax.grid(axis="x", color="#d7ddea", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.grid(axis="y", color="#d7ddea", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)

    for task_class, color in COLOR_MAP.items():
        class_df = plot_df[plot_df["Task_Class"] == task_class]
        ax.scatter(
            class_df["x"],
            class_df["y"],
            s=class_df["size"],
            c=color,
            edgecolors="white",
            linewidths=1.8,
            alpha=0.9,
            label=task_class,
            zorder=3,
        )

    for _, row in plot_df.iterrows():
        add_label(ax, row["x"], row["y"], LABEL_SPECS[row["Clinical_Task"]])

    ax.set_xlim(1.6, 5.6)
    ax.set_ylim(-0.42, 1.42)
    ax.set_xticks([2, 3, 4, 5])
    ax.set_xlabel("Highest validation stage reached", fontsize=15)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Moderate", "High"], fontsize=14)
    ax.set_ylabel("Consequence of error", fontsize=15)
    ax.tick_params(axis="x", labelsize=13)

    leg = fig.legend(
        title="Task class",
        loc="upper left",
        bbox_to_anchor=(0.11, 0.975),
        frameon=False,
        fontsize=11.5,
        ncol=3,
        borderaxespad=0.0,
        handletextpad=0.35,
        columnspacing=1.0,
    )
    leg.get_title().set_fontsize(13.5)
    leg.get_title().set_fontweight("bold")
    leg._legend_box.align = "left"
    for h in leg.legend_handles:
        h.set_sizes([110])
        h.set_alpha(1.0)

    size_x = 4.86
    ax.text(size_x + 0.18, -0.24, "Bubble size", fontsize=15, color="#222222", ha="left", va="center")
    ax.scatter([size_x], [-0.30], s=SIZE_MAP["Moderate"], c="#808080", alpha=0.55, edgecolors="#666666", linewidths=1.2)
    ax.scatter([size_x], [-0.36], s=SIZE_MAP["High"], c="#808080", alpha=0.55, edgecolors="#666666", linewidths=1.2)
    ax.text(size_x + 0.09, -0.30, "Moderate workflow value", fontsize=13.5, color="#222222", va="center")
    ax.text(size_x + 0.09, -0.36, "High workflow value", fontsize=13.5, color="#222222", va="center")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.1)
    ax.spines["bottom"].set_linewidth(1.1)

    fig.subplots_adjust(left=0.16, right=0.90, bottom=0.12, top=0.90)
    png_path = FIG_DIR / "Figure2_readiness_map.png"
    pdf_path = FIG_DIR / "Figure2_readiness_map.pdf"
    fig.savefig(png_path, dpi=300, facecolor="white")
    fig.savefig(pdf_path, facecolor="white")
    plt.close(fig)
    print(f"Wrote {png_path.name} and {pdf_path.name}")


if __name__ == "__main__":
    main()
