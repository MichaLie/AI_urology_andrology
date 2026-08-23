from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent
SOURCE_ROOT = REPOSITORY_ROOT / "source_data"
OUTPUT_ROOT = REPOSITORY_ROOT / "figures"

INK = "#172033"
MUTED = "#5B6573"
GRID = "#D8DEE8"
FIGURE_DPI = 600
FINAL_WIDTH_IN = 7.0

STRATUM_COLORS = {
    "Prostate Imaging": "#4E79A7",
    "Prostate Pathology": "#A0CBE8",
    "Bladder Cancer": "#F28E2B",
    "Renal/Kidney": "#FFBE7D",
    "Benign/Functional": "#59A14F",
    "Surgical AI": "#8CD17D",
    "Andrology": "#B6992D",
    "LLMs & GenAI": "#E15759",
    "Implementation/ethics/reporting search stream": "#B07AA1",
    "Broad Reviews": "#79706E",
}
STRATUM_HATCHES = {
    "Prostate Imaging": "",
    "Prostate Pathology": "///",
    "Bladder Cancer": "\\\\\\",
    "Renal/Kidney": "xxx",
    "Benign/Functional": "...",
    "Surgical AI": "+++",
    "Andrology": "---",
    "LLMs & GenAI": "ooo",
    "Implementation/ethics/reporting search stream": "***",
    "Broad Reviews": "|||",
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCE_ROOT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def generate_s1() -> Path:
    rows = read_csv("Supplementary_Figure_S1_publication_trends_source_data.csv")
    years = np.array([int(row["Year_int"]) for row in rows])
    totals = np.array([int(row["Total"]) for row in rows])
    strata = list(STRATUM_COLORS)

    assert totals.sum() == 2892
    assert all(
        sum(int(row[stratum]) for stratum in strata) == int(row["Total"])
        for row in rows
    )

    fig = plt.figure(figsize=(FINAL_WIDTH_IN, 4.8), dpi=FIGURE_DPI, facecolor="white")
    grid = fig.add_gridspec(
        1, 2, width_ratios=(1.58, 1), left=0.085, right=0.985,
        bottom=0.21, top=0.91, wspace=0.26,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])

    bottoms = np.zeros(len(rows))
    handles = []
    for stratum in strata:
        values = np.array([int(row[stratum]) for row in rows])
        bars = ax_a.bar(
            years, values, bottom=bottoms, width=0.72,
            color=STRATUM_COLORS[stratum], edgecolor="#374151", linewidth=0.28,
            hatch=STRATUM_HATCHES[stratum],
            label=stratum, zorder=2,
        )
        handles.append(bars[0])
        bottoms += values

    ax_a.plot(years, totals, color=INK, marker="o", linewidth=2.2,
              markersize=5.5, zorder=4, label="Annual total")
    for year, total in zip(years, totals):
        ax_a.annotate(
            f"{total:,}", (year, total), xytext=(0, 10),
            textcoords="offset points", ha="center", va="bottom",
            fontsize=8.0, color=INK, fontweight="bold",
        )

    ax_a.set_title("A. Annual output by operational analysis group", loc="left", fontsize=10.3,
                   fontweight="bold", color=INK, pad=9)
    ax_a.set_ylabel("PubMed-indexed records", fontsize=8.8, color=INK)
    ax_a.set_xticks(years)
    ax_a.set_ylim(0, 965)
    ax_a.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.75, zorder=0)
    ax_a.spines[["top", "right"]].set_visible(False)
    ax_a.tick_params(axis="both", labelsize=8.2, colors=INK)

    selected = ["LLMs & GenAI", "Renal/Kidney", "Prostate Pathology"]
    markers = ["o", "s", "^"]
    endpoint_offsets = {
        "LLMs & GenAI": (-8, -11),
        "Renal/Kidney": (-8, 0),
        "Prostate Pathology": (-8, 11),
    }
    for stratum, marker in zip(selected, markers):
        values = np.array([int(row[stratum]) for row in rows])
        ax_b.plot(
            years, values, color=STRATUM_COLORS[stratum], marker=marker,
            linewidth=2.6, markersize=6.3, label=stratum, zorder=3,
        )
        ax_b.annotate(
            f"{stratum}  {values[-1]}", (years[-1], values[-1]),
            xytext=endpoint_offsets[stratum],
            textcoords="offset points", ha="right", va="center",
            fontsize=8.0, color=STRATUM_COLORS[stratum], fontweight="bold",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 0.7},
        )

    ax_b.axvline(2022.88, color=MUTED, linestyle=(0, (4, 4)), linewidth=1.25, zorder=1)
    ax_b.set_title("B. Selected trajectories", loc="left", fontsize=10.3,
                   fontweight="bold", color=INK, pad=9)
    ax_b.set_ylabel("PubMed-indexed records", fontsize=8.8, color=INK)
    ax_b.set_xticks(years)
    ax_b.set_xlim(2019.75, 2026.45)
    ax_b.set_ylim(0, 175)
    ax_b.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.75, zorder=0)
    ax_b.spines[["top", "right"]].set_visible(False)
    ax_b.tick_params(axis="both", labelsize=8.2, colors=INK)

    legend = fig.legend(
        handles,
        [
            "Implementation/ethics/\nreporting stream" if value == "Implementation/ethics/reporting search stream" else value
            for value in strata
        ],
        loc="lower center", bbox_to_anchor=(0.5, 0.015),
        ncol=5, frameon=False, fontsize=8.0, handlelength=1.2,
        columnspacing=1.0, handletextpad=0.4,
    )
    for text in legend.get_texts():
        text.set_color(INK)

    output = OUTPUT_ROOT / "Supplementary_Figure_S1_publication_trends.png"
    fig.savefig(output, dpi=FIGURE_DPI, facecolor="white")
    plt.close(fig)
    return output


def generate_s2() -> Path:
    rows = read_csv("Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv")
    rows.sort(key=lambda row: float(row["review_type_pct"]), reverse=True)

    strata = [row["Operational_Analysis_Group"] for row in rows]
    totals = [int(row["total_records"]) for row in rows]
    review = np.array([float(row["review_type_pct"]) for row in rows])
    correspondence_editorial = np.array(
        [float(row["correspondence_editorial_pct"]) for row in rows]
    )
    combined = np.array(
        [float(row["review_or_correspondence_editorial_pct"]) for row in rows]
    )
    display_labels = [
        "Implementation/ethics/reporting\nsearch stream" if value == "Implementation/ethics/reporting search stream" else value
        for value in strata
    ]
    labels = [f"{stratum}  (n={total:,})" for stratum, total in zip(display_labels, totals)]

    assert sum(totals) == 2892
    assert sum(int(row["review_type_records"]) for row in rows) == 468
    assert sum(int(row["correspondence_editorial_records"]) for row in rows) == 96
    assert sum(int(row["review_or_correspondence_editorial_records"]) for row in rows) == 564
    assert all(
        abs((r + c) - n) <= 0.11
        for r, c, n in zip(review, correspondence_editorial, combined)
    )

    fig, ax = plt.subplots(figsize=(FINAL_WIDTH_IN, 5.1), dpi=FIGURE_DPI, facecolor="white")
    fig.subplots_adjust(left=0.33, right=0.985, top=0.96, bottom=0.14)
    y = np.arange(len(rows))

    review_color = "#4E79A7"
    commentary_color = "#C8D3E2"
    ax.barh(y, review, color=review_color, height=0.70,
            label="Review-type records", zorder=2)
    ax.barh(
        y, correspondence_editorial, left=review, color=commentary_color,
        height=0.70, label="Comment, letter, or editorial records", zorder=2,
    )

    for idx, (review_pct, combined_pct) in enumerate(zip(review, combined)):
        if review_pct >= 7.0:
            ax.text(review_pct - 0.9, idx, f"{review_pct:.1f}%", ha="right", va="center",
                    fontsize=8.0, color="white", fontweight="bold")
        if abs(combined_pct - review_pct) <= 0.11:
            continue
        outside_label = (
            f"{review_pct:.1f}% review | {combined_pct:.1f}% combined"
            if review_pct < 7.0
            else f"{combined_pct:.1f}% combined"
        )
        ax.text(
            combined_pct + 1.0, idx,
            outside_label,
            ha="left", va="center", fontsize=8.0, color=MUTED,
        )

    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 112)
    ax.set_xlabel("Share of operational-analysis-group output (%)", fontsize=8.8, color=INK, labelpad=7)
    ax.grid(axis="x", color=GRID, linewidth=0.8, alpha=0.75, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=8.2, colors=INK)
    ax.tick_params(axis="y", labelsize=8.6, colors=INK, pad=6, length=0)
    ax.legend(frameon=False, loc="lower right", fontsize=8.2, ncol=1)

    output = OUTPUT_ROOT / "Supplementary_Figure_S2_review_burden.png"
    fig.savefig(output, dpi=FIGURE_DPI, facecolor="white")
    plt.close(fig)
    return output


def verify_image(path: Path, minimum_width: int, minimum_height: int) -> dict[str, object]:
    with Image.open(path) as image:
        assert image.width >= minimum_width and image.height >= minimum_height
        assert image.mode in {"RGB", "RGBA"}
        extrema = image.convert("RGB").getextrema()
        assert any(low < high for low, high in extrema), f"{path.name} appears blank"
        return {
            "path": str(path),
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
        }


if __name__ == "__main__":
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    results = [
        verify_image(generate_s1(), 4000, 2800),
        verify_image(generate_s2(), 4000, 3000),
    ]
    for result in results:
        print(result)
