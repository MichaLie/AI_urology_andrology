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
    included_before_final_cleanup = int((screened["Final_Decision"] == "INCLUDE").sum())
    final_included = int((screened[analytic_col] == "INCLUDE").sum())
    preprints_removed = summary.get(
        "preprints_removed",
        int(cleanup_notes.str.contains("preprint|non-peer-reviewed", case=False, regex=True).sum()),
    )
    stone_scope_removed = summary.get(
        "stone_scope_removed",
        int(cleanup_notes.str.contains("stone", case=False, regex=True).sum()),
    )
    ai_only_include_population = int(
        screened["Review_Pathway"].fillna("").str.contains("AI-only include", case=False, regex=False).sum()
    )
    ai_only_include_audit_rows = summary.get("ai_only_include_audit_rows", len(ai_include_audit))
    ai_only_include_confirmed = summary.get(
        "ai_only_include_audit_confirmed_includes",
        int((ai_include_audit["Abstract_Informed_Decision"] == "CONFIRM_INCLUDE").sum())
        if "Abstract_Informed_Decision" in ai_include_audit.columns
        else ai_only_include_audit_rows,
    )
    ai_only_include_exclusions = summary.get(
        "ai_only_include_audit_exclusions_applied",
        int((ai_include_audit["Abstract_Informed_Decision"] == "EXCLUDE").sum())
        if "Abstract_Informed_Decision" in ai_include_audit.columns
        else 0,
    )
    retained_before_ai_only_audit_exclusions = summary.get(
        "retained_before_ai_only_include_audit_exclusions",
        included_before_final_cleanup + ai_only_include_exclusions,
    )
    non_urology_scope_removed = int(
        cleanup_notes.str.contains("non-urological ambient documentation", case=False, regex=False).sum()
    )
    other_scope_removed = int(
        cleanup_notes.str.contains("non-urological or nonclinical", case=False, regex=False).sum()
    )
    retracted_removed = int(cleanup_notes.str.contains("retracted publication", case=False, regex=False).sum())
    errata_removed = int(cleanup_notes.str.contains("erratum or correction", case=False, regex=False).sum())
    conference_removed = int(cleanup_notes.str.contains("conference/proceedings", case=False, regex=False).sum())
    duplicate_removed = int(cleanup_notes.str.contains("duplicate", case=False, regex=False).sum())
    residual_out_of_scope_removed = stone_scope_removed + non_urology_scope_removed + other_scope_removed
    publication_type_cleanup_removed = retracted_removed + errata_removed + conference_removed
    publication_or_duplicate_cleanup_removed = publication_type_cleanup_removed + duplicate_removed
    final_file_level_cleanup_removed = (
        preprints_removed
        + residual_out_of_scope_removed
        + publication_type_cleanup_removed
        + duplicate_removed
    )

    fig, ax = plt.subplots(figsize=(10.5, 13.8))
    ax.set_xlim(-0.12, 1.02)
    ax.set_ylim(-0.12, 1.04)
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
        1.002,
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
        0.875,
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
        0.795,
        0.72,
        0.065,
        f"Unique records after paginated uncapped retrieval\nand cross-query deduplication (n = {summary['query_union_unique_records']:,})",
        light_blue,
        fs=11.8,
    )
    add_box(
        ax,
        0.19,
        0.720,
        0.72,
        0.065,
        f"Records removed by conservative relevance filter\nbefore formal screening (n = {summary['pre_screen_relevance_exclusions']:,})",
        light_blue,
        fs=11.8,
    )
    add_box(
        ax,
        0.19,
        0.640,
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
        0.525,
        0.72,
        0.09,
        f"AI-assisted first pass\ninclude {ai_include:,}, exclude {ai_exclude:,}, uncertain {ai_uncertain:,}",
        orange,
        fs=13.5,
        weight="bold",
    )

    # Human-review and audit boxes
    left_x, left_y, left_w, left_h = 0.02, 0.350, 0.33, 0.14
    mid_x, mid_y, mid_w, mid_h = 0.39, 0.350, 0.27, 0.14
    right_x, right_y, right_w, right_h = 0.70, 0.350, 0.27, 0.14
    add_box(
        ax,
        left_x,
        left_y,
        left_w,
        left_h,
        f"Dual human review of records\nrouted to clinician review\n(n = {int(dual_mask.sum()):,})\nretained {dual_include:,}, excluded {dual_exclude:,}",
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
        f"Random audit of AI-only\nincluded records\n(n = {ai_only_include_audit_rows:,} of {ai_only_include_population:,})\n{ai_only_include_confirmed:,} confirmed include,\n{ai_only_include_exclusions:,} excluded",
        pale_green,
        fs=8.5,
    )

    add_box(
        ax,
        0.24,
        0.250,
        0.57,
        0.07,
        f"Records retained after consensus and\nAI-exclude audit correction\n(n = {retained_before_ai_only_audit_exclusions:,})",
        green,
        fs=11.6,
        weight="bold",
    )
    add_box(
        ax,
        0.31,
        0.165,
        0.43,
        0.055,
        f"AI-only Include audit exclusions applied\n(n = {ai_only_include_exclusions:,})",
        pale_green,
        fs=9.0,
    )
    add_box(
        ax,
        0.24,
        0.085,
        0.57,
        0.07,
        f"Records retained after AI-only Include audit\ncorrection before final cleanup\n(n = {included_before_final_cleanup:,})",
        green,
        fs=10.5,
        weight="bold",
    )
    add_box(
        ax,
        0.27,
        0.000,
        0.54,
        0.066,
        (
            f"Final file-level cleanup exclusions (n = {final_file_level_cleanup_removed:,})\n"
            f"preprints (n = {preprints_removed:,}); residual out-of-scope (n = {residual_out_of_scope_removed:,})\n"
            f"publication type (n = {publication_type_cleanup_removed:,}); duplicates/near-duplicates (n = {duplicate_removed:,})"
        ),
        peach,
        fs=8.5,
    )
    add_box(
        ax,
        0.25,
        -0.090,
        0.56,
        0.06,
        f"Final included record set\n(n = {final_included:,})",
        blue,
        fs=11.6,
        weight="bold",
    )

    # Arrows
    down_arrow(ax, center_x, 0.875, 0.860)
    down_arrow(ax, center_x, 0.795, 0.785)
    down_arrow(ax, center_x, 0.720, 0.705)
    down_arrow(ax, center_x, 0.640, 0.615)
    diagonal_arrow(ax, 0.38, 0.525, 0.19, 0.470)
    diagonal_arrow(ax, 0.56, 0.525, 0.52, 0.470)
    diagonal_arrow(ax, 0.70, 0.525, 0.84, 0.470)
    diagonal_arrow(ax, 0.19, 0.350, 0.39, 0.320)
    diagonal_arrow(ax, 0.52, 0.350, 0.53, 0.320)
    diagonal_arrow(ax, 0.84, 0.350, 0.66, 0.320)
    down_arrow(ax, 0.525, 0.250, 0.220)
    down_arrow(ax, 0.525, 0.165, 0.155)
    down_arrow(ax, 0.525, 0.085, 0.066)
    down_arrow(ax, 0.525, 0.000, -0.030)

    # Left-side stage labels, centered to relevant boxes
    label_x = -0.11
    ax.text(label_x, 0.815, "IDENTIFICATION", ha="left", va="center", fontsize=12, fontweight="bold", color=blue)
    ax.text(label_x, 0.485, "SCREENING", ha="left", va="center", fontsize=13, fontweight="bold", color=orange)
    ax.text(label_x, 0.150, "ELIGIBILITY", ha="left", va="center", fontsize=13, fontweight="bold", color=green)
    ax.text(label_x, -0.060, "INCLUDED", ha="left", va="center", fontsize=13, fontweight="bold", color=blue)

    png_path = FIG_DIR / "Figure1_PRISMA_flow.png"
    pdf_path = FIG_DIR / "Figure1_PRISMA_flow.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=0.22)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    source_rows = [
        ("pubmed_hits_across_queries", "PubMed hits across queries", summary["pubmed_hits_across_queries"]),
        ("query_union_unique_records", "Unique records after deduplication", summary["query_union_unique_records"]),
        ("pre_screen_relevance_exclusions", "Prescreen relevance exclusions", summary["pre_screen_relevance_exclusions"]),
        ("unique_records_screened", "Records screened", summary["unique_records_screened"]),
        ("ai_include", "AI include", ai_include),
        ("ai_exclude", "AI exclude", ai_exclude),
        ("ai_uncertain", "AI uncertain", ai_uncertain),
        ("human_dual_review_rows", "Dual human review rows", int(dual_mask.sum())),
        ("human_dual_review_retained", "Dual human review retained", dual_include),
        ("human_dual_review_excluded", "Dual human review excluded", dual_exclude),
        ("human_exclude_audit_rows", "AI-exclude audit rows", int(audit_mask.sum())),
        ("human_exclude_audit_overturned", "AI-exclude audit overturned", audit_overturned),
        ("human_exclude_audit_confirmed_exclude", "AI-exclude audit confirmed exclude", audit_confirmed),
        ("ai_only_include_population", "AI-only Include population", ai_only_include_population),
        ("ai_only_include_audit_rows", "AI-only Include audit rows", ai_only_include_audit_rows),
        (
            "retained_before_ai_only_include_audit_exclusions",
            "Retained after consensus and AI-exclude audit correction before AI-only Include audit exclusions",
            retained_before_ai_only_audit_exclusions,
        ),
        (
            "ai_only_include_audit_exclusions_applied",
            "AI-only Include audit exclusions applied",
            ai_only_include_exclusions,
        ),
        (
            "included_before_final_cleanup",
            "Included before final file-level cleanup after audit correction",
            included_before_final_cleanup,
        ),
        ("preprints_removed", "Preprints removed", preprints_removed),
        ("stone_scope_removed", "Stone-scope records removed", stone_scope_removed),
        ("non_urology_documentation_removed", "Non-urology ambient-documentation records removed", non_urology_scope_removed),
        ("other_scope_removed", "Other non-urological or nonclinical records removed", other_scope_removed),
        ("residual_out_of_scope_removed", "Residual out-of-scope records removed", residual_out_of_scope_removed),
        ("retracted_publications_removed", "Retracted publications removed", retracted_removed),
        ("errata_corrections_removed", "Errata/correction notices removed", errata_removed),
        ("conference_proceedings_removed", "Conference/proceedings records removed", conference_removed),
        ("publication_type_cleanup_removed", "Publication-type cleanup records removed", publication_type_cleanup_removed),
        ("duplicate_or_near_duplicate_removed", "Duplicate or near-duplicate records removed", duplicate_removed),
        ("final_file_level_cleanup_removed", "Final file-level cleanup records removed", final_file_level_cleanup_removed),
        ("final_included_records", "Final included record set", final_included),
        (
            "ai_only_include_audit_confirmed_includes",
            "AI-only Include audit confirmed includes",
            ai_only_include_confirmed,
        ),
    ]
    source_path = ROOT / "source_data" / "Figure1_PRISMA_flow_source_data.csv"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(source_rows, columns=["Metric_Key", "Metric_Label", "Value"]).to_csv(source_path, index=False)
    print(f"Wrote {png_path.name} and {pdf_path.name}")


if __name__ == "__main__":
    main()
