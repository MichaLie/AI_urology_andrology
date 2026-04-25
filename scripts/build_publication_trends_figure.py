#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "included_records.csv"
FIG_DIR = ROOT / "figures"
SOURCE_DATA_DIR = ROOT / "source_data"
OUT_TABLE = SOURCE_DATA_DIR / "Supplementary_Figure_S1_publication_trends_source_data.csv"

COLOR_MAP = {
    "Prostate Imaging": "#2f6db3",
    "Prostate Pathology": "#f39c74",
    "Bladder Cancer": "#d7654d",
    "Renal/Kidney": "#5fa0d3",
    "Benign/Functional": "#9e9e9e",
    "Surgical AI": "#b31b34",
    "Andrology": "#7b4fa1",
    "LLMs & GenAI": "#21823b",
    "Governance": "#f4a73c",
    "Broad Reviews": "#cbd6ec",
}


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    included = pd.read_csv(DATA_PATH)
    trends = (
        included.groupby(["Year", "Domain_Group"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
        .reset_index()
        .rename(columns={"Year": "Year_int"})
    )
    domain_order = [
        "Prostate Imaging",
        "Prostate Pathology",
        "Bladder Cancer",
        "Renal/Kidney",
        "Benign/Functional",
        "Surgical AI",
        "Andrology",
        "LLMs & GenAI",
        "Governance",
        "Broad Reviews",
    ]
    for domain in domain_order:
        if domain not in trends.columns:
            trends[domain] = 0
    trends["Total"] = trends[domain_order].sum(axis=1)
    trends = trends[["Year_int"] + domain_order + ["Total"]]
    trends.to_csv(OUT_TABLE, index=False)

    years = trends["Year_int"].astype(str).tolist()
    x = range(len(years))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    bottom = [0] * len(trends)
    for domain in domain_order:
        values = trends[domain].tolist()
        ax1.bar(
            x,
            values,
            bottom=bottom,
            label=domain,
            color=COLOR_MAP.get(domain, "#7f8c8d"),
            edgecolor="white",
            linewidth=0.4,
        )
        bottom = [b + v for b, v in zip(bottom, values)]

    ax1.plot(x, trends["Total"], color="black", marker="o", linewidth=1.5)
    for idx, total in enumerate(trends["Total"]):
        ax1.text(idx, total + 12, str(int(total)), ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax1.set_xticks(list(x), years)
    ax1.set_ylabel("Number of publications")
    ax1.set_title("A. Publication trends by clinical domain, 2020-2026", loc="left", fontsize=13, fontweight="bold")
    ax1.legend(ncol=2, fontsize=8, loc="upper left")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    subset = [col for col in ["LLMs & GenAI", "Governance", "Prostate Pathology"] if col in trends.columns]
    markers = {"LLMs & GenAI": "o", "Governance": "s", "Prostate Pathology": "D"}
    for domain in subset:
        ax2.plot(
            x,
            trends[domain],
            marker=markers[domain],
            linewidth=2,
            color=COLOR_MAP[domain],
            label=domain,
        )
        for idx, value in enumerate(trends[domain]):
            if value > 0:
                ax2.text(
                    idx,
                    value + 2.5,
                    str(int(value)),
                    color=COLOR_MAP[domain],
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                )

    if "LLMs & GenAI" in subset and 2023 in set(trends["Year_int"].astype(int)):
        llm_2023 = trends.loc[trends["Year_int"] == 2023, "LLMs & GenAI"].iloc[0]
        ax2.annotate(
            "ChatGPT release\nNov 2022",
            xy=(3, llm_2023),
            xytext=(1.3, max(58, llm_2023 + 20)),
            arrowprops=dict(arrowstyle="->", lw=1.0, color=COLOR_MAP["LLMs & GenAI"]),
            fontsize=9,
            color=COLOR_MAP["LLMs & GenAI"],
            fontstyle="italic",
        )

    ax2.set_xticks(list(x), years)
    ax2.set_ylabel("Number of publications")
    ax2.set_title("B. Contrasting growth trajectories in selected domains", loc="left", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=9, loc="upper left")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout()
    png = FIG_DIR / "Supplementary_Figure_S1_publication_trends.png"
    pdf = FIG_DIR / "Supplementary_Figure_S1_publication_trends.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT_TABLE.name}, {png.name}, and {pdf.name}")


if __name__ == "__main__":
    main()
