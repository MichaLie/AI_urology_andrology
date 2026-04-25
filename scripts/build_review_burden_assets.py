#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_IN = ROOT / "data" / "included_records.csv"
DATA_OUT_DIR = ROOT / "data"
SOURCE_DATA_DIR = ROOT / "source_data"
FIG_OUT_DIR = ROOT / "figures"
DOMAIN_SOURCE_OUT = SOURCE_DATA_DIR / "Supplementary_Figure_S2_review_paradox_by_domain_source_data.csv"


def classify(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    pub = out["Publication_Type"].fillna("")
    out["is_review"] = pub.str.contains(r"(?:^|; )Review(?:$|;)", regex=True)
    out["is_commentary"] = pub.str.contains(r"(?:^|; )(?:Comment|Letter|Editorial)(?:$|;)", regex=True)
    out["is_non_original"] = out["is_review"] | out["is_commentary"]
    return out


def build_domain_table(df: pd.DataFrame) -> pd.DataFrame:
    domain = (
        df.groupby("Domain_Group")
        .agg(
            total_records=("PMID", "size"),
            review_records=("is_review", "sum"),
            commentary_records=("is_commentary", "sum"),
            non_original_records=("is_non_original", "sum"),
        )
        .reset_index()
    )
    domain["original_records"] = domain["total_records"] - domain["non_original_records"]
    domain["review_pct"] = (100 * domain["review_records"] / domain["total_records"]).round(1)
    domain["commentary_pct"] = (100 * domain["commentary_records"] / domain["total_records"]).round(1)
    domain["non_original_pct"] = (100 * domain["non_original_records"] / domain["total_records"]).round(1)
    domain["review_per_100_original"] = (
        100 * domain["review_records"] / (domain["total_records"] - domain["review_records"])
    ).round(1)
    domain = domain.sort_values(["review_pct", "review_records", "total_records"], ascending=[False, False, False])
    return domain[
        [
            "Domain_Group",
            "total_records",
            "original_records",
            "review_records",
            "commentary_records",
            "non_original_records",
            "review_pct",
            "commentary_pct",
            "non_original_pct",
            "review_per_100_original",
        ]
    ]


def build_year_table(df: pd.DataFrame) -> pd.DataFrame:
    year = (
        df.groupby("Year")
        .agg(
            total_records=("PMID", "size"),
            review_records=("is_review", "sum"),
            commentary_records=("is_commentary", "sum"),
            non_original_records=("is_non_original", "sum"),
        )
        .reset_index()
        .sort_values("Year")
    )
    year["review_pct"] = (100 * year["review_records"] / year["total_records"]).round(1)
    year["non_original_pct"] = (100 * year["non_original_records"] / year["total_records"]).round(1)
    return year


def make_figure(domain: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    plot_df = domain.copy().iloc[::-1]
    labels = [f"{d} (n={n})" for d, n in zip(plot_df["Domain_Group"], plot_df["total_records"])]
    y = range(len(plot_df))
    analytic_set_n = int(domain["total_records"].sum())

    ax.barh(y, plot_df["non_original_pct"], color="#d6dde7", label="Non-original items")
    ax.barh(y, plot_df["review_pct"], color="#486a8b", label="Review-labelled items")

    for yi, review_pct, non_original_pct in zip(y, plot_df["review_pct"], plot_df["non_original_pct"]):
        ax.text(non_original_pct + 1.2, yi, f"{non_original_pct:.1f}%", va="center", ha="left", fontsize=8, color="#556270")
        ax.text(max(review_pct - 1.2, 0.5), yi, f"{review_pct:.1f}%", va="center", ha="right", fontsize=8, color="white")

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, max(35, float(plot_df["non_original_pct"].max()) + 10))
    ax.set_xlabel("Share of domain output (%)", fontsize=10)
    ax.set_title(
        f"Review and non-original publication burden by domain in the {analytic_set_n:,}-record included set",
        fontsize=11,
    )
    ax.grid(axis="x", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    fig.tight_layout()

    png = FIG_OUT_DIR / "Supplementary_Figure_S2_review_paradox_by_domain.png"
    pdf = FIG_OUT_DIR / "Supplementary_Figure_S2_review_paradox_by_domain.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIG_OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_IN)
    df = classify(df)

    domain = build_domain_table(df)
    year = build_year_table(df)

    domain.to_csv(DOMAIN_SOURCE_OUT, index=False)
    year.to_csv(DATA_OUT_DIR / "review_burden_by_year.csv", index=False)

    make_figure(domain)
    print("Wrote review burden data tables and figure assets.")


if __name__ == "__main__":
    main()
