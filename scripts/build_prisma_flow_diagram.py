#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "figures"
SUMMARY_PATH = ROOT / "data" / "screening_counts.json"
SCREENING_PATH = ROOT / "data" / "screening_database.csv"
AI_INCLUDE_AUDIT_PATH = ROOT / "data" / "ai_only_include_audit.csv"


def first_existing_column(df: pd.DataFrame, *candidates: str) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise KeyError(f"None of these columns are present: {', '.join(candidates)}")


def add_box(ax, x: float, y: float, w: float, h: float, text: str, fc: str, *, fs: int = 15, weight: str = "normal") -> None:
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=1.6,
        edgecolor="#6d6d6d",
        facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fs,
        fontweight=weight,
        color="#1f1f1f",
        linespacing=1.25,
    )


def down_arrow(ax, x: float, y0: float, y1: float) -> None:
    ax.annotate(
        "",
        xy=(x, y1),
        xytext=(x, y0),
        arrowprops=dict(arrowstyle="->", lw=1.6, color="#585858"),
    )


def diagonal_arrow(ax, x0: float, y0: float, x1: float, y1: float) -> None:
    ax.annotate(
        "",
        xy=(x1, y1),
        xytext=(x0, y0),
        arrowprops=dict(arrowstyle="->", lw=1.6, color="#585858"),
    )


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    screened = pd.read_csv(SCREENING_PATH)
    ai_include_audit = pd.read_csv(AI_INCLUDE_AUDIT_PATH) if AI_INCLUDE_AUDIT_PATH.exists() else pd.DataFrame()

    dual_mask = screened["Review_Pathway"].isin(
        ["Dual human review", "AI uncertain + dual human review", "Dual human review + adjudication"]
    )
    audit_mask = screened["Review_Pathway"] == "AI exclude + 20% human audit"
    analytic_col = first_existing_column(screened, "Analytic_Set_Decision")
    cleanup_col = first_existing_column(screened, "Eligibility_Cleanup_Reason")
    cleanup_notes = screened[cleanup_col].fillna("")

    ai_include = int((screened["AI_Decision"] == "INCLUDE").sum())
    ai_exclude = int((screened["AI_Decision"] == "EXCLUDE").sum())
    ai_uncertain = int((screened["AI_Decision"] == "UNCERTAIN").sum())
    dual_include = int(((screened["Final_Decision"] == "INCLUDE") & dual_mask).sum())
    dual_exclude = int(((screened["Final_Decision"] == "EXCLUDE") & dual_mask).sum())
    audit_overturned = int(((screened["Final_Decision"] == "INCLUDE") & audit_mask).sum())
    audit_confirmed = int(((screened["Final_Decision"] == "EXCLUDE") & audit_mask).sum())
    included_after_consensus = int((screened["Final_Decision"] == "INCLUDE").sum())
    final_included = int((screened[analytic_col] == "INCLUDE").sum())
    preprints_removed = summary.get(
        "preprints_removed",
        int(cleanup_notes.str.contains("preprint|non-peer-reviewed", case=False, regex=True).sum()),
    )
    stone_scope_removed = summary.get(
        "stone_scope_removed",
        int(cleanup_notes.str.contains("stone", case=False, regex=True).sum()),
    )
    ai_only_include_population = summary.get("ai_only_include_population", 0)
    ai_only_include_audit_rows = summary.get("ai_only_include_audit_rows", len(ai_include_audit))
    ai_only_include_retained = (
        int((ai_include_audit["Analytic_Set_Decision"] == "INCLUDE").sum())
        if "Analytic_Set_Decision" in ai_include_audit.columns
        else ai_only_include_audit_rows
    )

    fig, ax = plt.subplots(figsize=(10.5, 11.9))
    ax.set_xlim(-0.12, 1.02)
    ax.set_ylim(-0.03, 1)
    ax.axis("off")

    blue = "#6f95d1"
    light_blue = "#dce8f5"
    orange = "#eb9347"
    peach = "#f5dfd0"
    pale_green = "#e5f0da"
    green = "#98bd65"

    # Title above the top box
    ax.text(
        0.45,
        0.972,
        "Literature Screening Flow Diagram",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color="#111111",
    )

    # Main stacked boxes
    top_x, top_w = 0.15, 0.80
    center_x = top_x + top_w / 2

    add_box(
        ax,
        top_x,
        0.84,
        top_w,
        0.065,
        f"PubMed hits returned across 20 domain-specific queries\n(n = {summary['pubmed_hits_across_queries']:,})",
        blue,
        fs=12.5,
        weight="bold",
    )
    add_box(
        ax,
        0.19,
        0.75,
        0.72,
        0.065,
        f"Unique records after paginated uncapped retrieval\nand cross-query deduplication (n = {summary['query_union_unique_records']:,})",
        light_blue,
        fs=11.8,
    )
    add_box(
        ax,
        0.19,
        0.66,
        0.72,
        0.065,
        f"Records removed by conservative relevance filter\nbefore formal screening (n = {summary['pre_screen_relevance_exclusions']:,})",
        light_blue,
        fs=11.8,
    )
    add_box(
        ax,
        0.19,
        0.57,
        0.72,
        0.065,
        f"Records entering AI-assisted\ntitle/abstract screening\n(n = {summary['records_for_ai_screening']:,})",
        blue,
        fs=11.8,
        weight="bold",
    )
    add_box(
        ax,
        0.20,
        0.44,
        0.72,
        0.09,
        f"AI-assisted first pass\ninclude {ai_include:,}, exclude {ai_exclude:,}, uncertain {ai_uncertain:,}",
        orange,
        fs=13.5,
        weight="bold",
    )

    # Human-review and audit boxes
    left_x, left_y, left_w, left_h = 0.02, 0.25, 0.33, 0.14
    mid_x, mid_y, mid_w, mid_h = 0.39, 0.25, 0.27, 0.14
    right_x, right_y, right_w, right_h = 0.70, 0.25, 0.27, 0.14
    add_box(
        ax,
        left_x,
        left_y,
        left_w,
        left_h,
        f"Dual human review of records\nrequiring adjudication\n(n = {int(dual_mask.sum()):,})\nretained {dual_include:,}, excluded {dual_exclude:,}",
        peach,
        fs=9.5,
    )
    add_box(
        ax,
        mid_x,
        mid_y,
        mid_w,
        mid_h,
        f"Random 20% human audit\nof AI excludes\n(n = {int(audit_mask.sum()):,})\n{audit_overturned:,} overturned,\n{audit_confirmed:,} confirmed exclude",
        pale_green,
        fs=8.7,
    )
    add_box(
        ax,
        right_x,
        right_y,
        right_w,
        right_h,
        f"Random audit of AI-only\nincluded records\n(n = {ai_only_include_audit_rows:,} of {ai_only_include_population:,})\n{ai_only_include_retained:,} retained",
        pale_green,
        fs=8.5,
    )

    add_box(
        ax,
        0.24,
        0.16,
        0.57,
        0.07,
        f"Records retained after consensus\nand audit correction\n(n = {included_after_consensus:,})",
        green,
        fs=11.6,
        weight="bold",
    )
    add_box(
        ax,
        0.27,
        0.075,
        0.51,
        0.06,
        f"Post-screening cleanup exclusions\npreprints (n = {preprints_removed:,}) + residual out-of-scope\nrecords (n = {stone_scope_removed:,})",
        peach,
        fs=9.8,
    )
    add_box(
        ax,
        0.25,
        0.0,
        0.56,
        0.06,
        f"Final included record set\n(n = {final_included:,})",
        blue,
        fs=11.6,
        weight="bold",
    )

    # Arrows
    down_arrow(ax, center_x, 0.84, 0.815)
    down_arrow(ax, center_x, 0.75, 0.725)
    down_arrow(ax, center_x, 0.66, 0.635)
    down_arrow(ax, center_x, 0.57, 0.53)
    diagonal_arrow(ax, 0.38, 0.44, 0.19, 0.37)
    diagonal_arrow(ax, 0.56, 0.44, 0.52, 0.37)
    diagonal_arrow(ax, 0.70, 0.44, 0.84, 0.37)
    diagonal_arrow(ax, 0.19, 0.25, 0.39, 0.23)
    diagonal_arrow(ax, 0.52, 0.25, 0.53, 0.23)
    diagonal_arrow(ax, 0.84, 0.25, 0.66, 0.23)
    down_arrow(ax, 0.525, 0.16, 0.135)
    down_arrow(ax, 0.525, 0.075, 0.06)

    # Left-side stage labels, centered to relevant boxes
    label_x = -0.11
    ax.text(label_x, 0.795, "IDENTIFICATION", ha="left", va="center", fontsize=12, fontweight="bold", color=blue)
    ax.text(label_x, 0.485, "SCREENING", ha="left", va="center", fontsize=13, fontweight="bold", color=orange)
    ax.text(label_x, 0.195, "ELIGIBILITY", ha="left", va="center", fontsize=13, fontweight="bold", color=green)
    ax.text(label_x, 0.03, "INCLUDED", ha="left", va="center", fontsize=13, fontweight="bold", color=blue)

    png_path = FIG_DIR / "Figure1_PRISMA_flow.png"
    pdf_path = FIG_DIR / "Figure1_PRISMA_flow.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=0.22)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print(f"Wrote {png_path.name} and {pdf_path.name}")


if __name__ == "__main__":
    main()
