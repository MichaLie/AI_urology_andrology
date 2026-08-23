from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent
SOURCE_ROOT = REPOSITORY_ROOT / "source_data"
FIGURE_ROOT = REPOSITORY_ROOT / "figures"

BLUE = "#5B8FD1"
BLUE_LIGHT = "#DDE9F7"
ORANGE = "#F39A45"
ORANGE_LIGHT = "#FBE8D7"
GREEN = "#83B85A"
GREEN_LIGHT = "#E7F2E0"
PURPLE = "#8064B8"
PURPLE_LIGHT = "#ECE6F6"
GRAY_LIGHT = "#F1F3F5"
GRAY = "#63676D"
INK = "#172033"
MUTED = "#4E5663"
FIGURE_DPI = 600
FINAL_WIDTH_IN = 7.0


def read_metric_source() -> dict[str, int]:
    source = SOURCE_ROOT / "Figure1_PRISMA_flow_source_data.csv"
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    metrics = {row["Metric_Key"]: int(row["Value"]) for row in rows}
    assert len(metrics) == len(rows) == 37
    return metrics


def add_box(ax, x, y, width, height, text, facecolor, *, edgecolor=GRAY, fontsize=13,
            weight="normal", text_color=INK, linewidth=1.7, radius=0.016, zorder=2):
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, zorder=zorder,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2, y + height / 2, text,
        ha="center", va="center", fontsize=fontsize, fontweight=weight,
        color=text_color, linespacing=1.08, zorder=zorder + 1,
    )
    return patch


def arrow(ax, start, end, *, color=GRAY, linewidth=1.6, mutation_scale=15, connectionstyle="arc3"):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", color=color, linewidth=linewidth,
        mutation_scale=mutation_scale, connectionstyle=connectionstyle, zorder=1,
    ))


def generate_figure1(metrics: dict[str, int]) -> Path:
    assert metrics["query_union_unique_records"] - metrics["prescreen_relevance_exclusions"] == metrics["records_screened"]
    assert metrics["records_before_ai_only_sample_exclusions"] - metrics["ai_only_include_sample_excluded"] == metrics["records_after_screening_verification"]
    assert metrics["records_after_screening_verification"] - sum(metrics[key] for key in (
        "preprints_removed", "residual_scope_records_removed", "publication_type_records_removed", "duplicate_records_removed"
    )) == metrics["records_before_final_eligibility_verification"]
    assert metrics["eligibility_candidates_flagged"] + metrics["eligibility_candidates_not_flagged"] == metrics["records_before_final_eligibility_verification"]
    assert (
        metrics["eligibility_candidates_initial_rules"]
        + metrics["eligibility_candidates_second_pass"]
        + metrics.get("eligibility_candidates_renal_boundary_pass", 0)
        + metrics.get("eligibility_candidates_language_boundary_pass", 0)
        + metrics.get("eligibility_candidates_case_report_boundary_pass", 0)
        == metrics["eligibility_candidates_flagged"]
    )
    assert sum(metrics[key] for key in (
        "eligibility_candidates_confirmed_include", "eligibility_candidates_operational_analysis_group_corrected",
        "eligibility_candidates_context_only", "eligibility_candidates_excluded"
    )) == metrics["eligibility_candidates_flagged"]
    assert metrics["eligibility_candidates_not_flagged"] + metrics["eligibility_candidates_confirmed_include"] + metrics["eligibility_candidates_operational_analysis_group_corrected"] == metrics["final_analytic_corpus"]

    # The canvas is the intended final full-page print footprint.  Building at
    # 7 inches rather than drawing at 14 inches and scaling down keeps the
    # declared point sizes faithful to their printed size.
    fig, ax = plt.subplots(figsize=(FINAL_WIDTH_IN, 9.0), dpi=FIGURE_DPI)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.025, right=0.985, bottom=0.015, top=0.992)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    section_style = dict(fontsize=9.2, fontweight="bold", ha="left", va="center")
    ax.text(0.02, 0.982, "IDENTIFICATION", color=BLUE, **section_style)
    ax.text(0.02, 0.755, "SCREENING", color=ORANGE, **section_style)
    ax.text(0.02, 0.447, "ELIGIBILITY", color=GREEN, **section_style)
    ax.text(0.02, 0.112, "INCLUDED", color=BLUE, **section_style)

    add_box(ax, 0.16, 0.925, 0.68, 0.043,
            f"20 prespecified PubMed queries\nHits returned (n = {metrics['pubmed_hits_across_queries']:,})",
            BLUE, fontsize=9.1, weight="bold", text_color="white", linewidth=1.2)
    add_box(ax, 0.18, 0.866, 0.64, 0.039,
            f"Unique records after cross-query deduplication (n = {metrics['query_union_unique_records']:,})",
            BLUE_LIGHT, fontsize=8.8, linewidth=1.1)
    arrow(ax, (0.50, 0.925), (0.50, 0.905), linewidth=1.1, mutation_scale=11)

    add_box(ax, 0.11, 0.793, 0.56, 0.050,
            f"Records entering title and abstract screening\n(n = {metrics['records_screened']:,})",
            BLUE, fontsize=9.0, weight="bold", text_color="white", linewidth=1.2)
    add_box(ax, 0.72, 0.790, 0.25, 0.056,
            f"Prescreen relevance\nexclusions (n = {metrics['prescreen_relevance_exclusions']:,})",
            GRAY_LIGHT, fontsize=8.2, linewidth=1.0)
    arrow(ax, (0.50, 0.866), (0.39, 0.843), connectionstyle="arc3,rad=0.10",
          linewidth=1.1, mutation_scale=11)
    arrow(ax, (0.59, 0.866), (0.72, 0.818), connectionstyle="arc3,rad=-0.08",
          linewidth=1.1, mutation_scale=11)

    add_box(ax, 0.12, 0.685, 0.76, 0.052,
            "AI-assisted first pass\n"
            f"Include {metrics['ai_first_pass_include']:,}   |   Exclude {metrics['ai_first_pass_exclude']:,}   |   Uncertain {metrics['ai_first_pass_uncertain']:,}",
            ORANGE, fontsize=9.1, weight="bold", text_color=INK, linewidth=1.2)
    arrow(ax, (0.39, 0.793), (0.50, 0.737), linewidth=1.1, mutation_scale=11)

    branch_y, branch_h, branch_w = 0.562, 0.085, 0.285
    branch_xs = [0.025, 0.3575, 0.69]
    branch_texts = [
        f"Dual human review\n(n = {metrics['dual_human_review_rows']:,})\n"
        f"Retained {metrics['dual_human_review_retained']:,} | Excluded {metrics['dual_human_review_excluded']:,}",
        f"Audit sample of AI Excludes\n(n = {metrics['ai_exclude_audit_rows']:,})\n"
        f"Retained {metrics['ai_exclude_audit_overturned']:,} | Excluded {metrics['ai_exclude_audit_confirmed']:,}",
        f"AI-only Include sample\n"
        f"(n = {metrics['ai_only_include_sample']:,} of {metrics['ai_only_include_population']:,})\n"
        f"Eligible {metrics['ai_only_include_sample_retained']:,} | Excluded {metrics['ai_only_include_sample_excluded']:,}",
    ]
    branch_colors = [ORANGE_LIGHT, GREEN_LIGHT, GREEN_LIGHT]
    for x, text, color in zip(branch_xs, branch_texts, branch_colors):
        add_box(ax, x, branch_y, branch_w, branch_h, text, color, fontsize=8.0,
                linewidth=1.0, radius=0.012)
        arrow(ax, (0.50, 0.685), (x + branch_w / 2, branch_y + branch_h),
              connectionstyle="arc3,rad=0.06", linewidth=1.0, mutation_scale=10)

    add_box(ax, 0.15, 0.486, 0.70, 0.052,
            f"Screening retained after audit correction (n = {metrics['records_after_screening_verification']:,})\n"
            f"{metrics['records_before_ai_only_sample_exclusions']:,} retained before {metrics['ai_only_include_sample_excluded']:,} sampled Include exclusions",
            GREEN, fontsize=8.7, weight="bold", text_color=INK, linewidth=1.2)
    for x in branch_xs:
        arrow(ax, (x + branch_w / 2, branch_y), (0.50, 0.538),
              connectionstyle="arc3,rad=-0.05", linewidth=1.0, mutation_scale=10)

    cleanup_total = sum(metrics[key] for key in (
        "preprints_removed", "residual_scope_records_removed", "publication_type_records_removed", "duplicate_records_removed"
    ))
    add_box(ax, 0.67, 0.365, 0.30, 0.070,
            f"File-level exclusions (n = {cleanup_total})\n"
            f"Preprints {metrics['preprints_removed']} | Scope {metrics['residual_scope_records_removed']}\n"
            f"Publication type {metrics['publication_type_records_removed']} | Duplicates {metrics['duplicate_records_removed']}",
            ORANGE_LIGHT, fontsize=8.0, linewidth=1.0)
    add_box(ax, 0.10, 0.374, 0.52, 0.052,
            f"Records before final eligibility verification\n(n = {metrics['records_before_final_eligibility_verification']:,})",
            GREEN, fontsize=8.8, weight="bold", text_color=INK, linewidth=1.2)
    arrow(ax, (0.50, 0.486), (0.36, 0.426), connectionstyle="arc3,rad=0.08",
          linewidth=1.1, mutation_scale=11)
    arrow(ax, (0.58, 0.486), (0.67, 0.400), connectionstyle="arc3,rad=-0.08",
          linewidth=1.1, mutation_scale=11)

    add_box(ax, 0.09, 0.263, 0.82, 0.073,
            "Rule-assisted final eligibility verification\n"
            f"Not in verification: {metrics['eligibility_candidates_not_flagged']:,}   |   Verified: {metrics['eligibility_candidates_flagged']:,}\n"
            f"({metrics['eligibility_candidates_initial_rules']:,} initial + "
            f"{metrics['eligibility_candidates_second_pass']:,} boundary + "
            f"{metrics.get('eligibility_candidates_renal_boundary_pass', 0):,} renal + "
            f"{metrics.get('eligibility_candidates_language_boundary_pass', 0):,} language + "
            f"{metrics.get('eligibility_candidates_case_report_boundary_pass', 0):,} case-report)",
            PURPLE_LIGHT, edgecolor=PURPLE, fontsize=8.2, weight="bold", linewidth=1.2)
    arrow(ax, (0.36, 0.374), (0.50, 0.336), connectionstyle="arc3,rad=0.06",
          linewidth=1.1, mutation_scale=11)

    outcome_y, outcome_h, outcome_w = 0.150, 0.074, 0.215
    outcome_xs = [0.022, 0.268, 0.514, 0.760]
    outcome_specs = [
        (f"Eligible\n(n = {metrics['eligibility_candidates_confirmed_include']:,})", GREEN_LIGHT, GREEN),
        (f"Eligible after operational-\nanalysis-group correction\n(n = {metrics['eligibility_candidates_operational_analysis_group_corrected']:,})", BLUE_LIGHT, BLUE),
        (f"Narrative\ncontext only\n(n = {metrics['eligibility_candidates_context_only']:,})", PURPLE_LIGHT, PURPLE),
        (f"Excluded\n(n = {metrics['eligibility_candidates_excluded']:,})", ORANGE_LIGHT, ORANGE),
    ]
    for x, (text, face, edge) in zip(outcome_xs, outcome_specs):
        add_box(ax, x, outcome_y, outcome_w, outcome_h, text, face, edgecolor=edge,
                fontsize=8.0, weight="bold", linewidth=1.0, radius=0.012)
        arrow(ax, (0.50, 0.263), (x + outcome_w / 2, outcome_y + outcome_h),
              connectionstyle="arc3,rad=0.05", linewidth=1.0, mutation_scale=10)

    add_box(ax, 0.15, 0.040, 0.70, 0.055,
            f"Final analytic corpus (n = {metrics['final_analytic_corpus']:,})",
            BLUE, fontsize=10.6, weight="bold", text_color="white", linewidth=1.2)
    arrow(ax, (outcome_xs[0] + outcome_w / 2, outcome_y), (0.47, 0.095),
          connectionstyle="arc3,rad=-0.08", linewidth=1.1, mutation_scale=11)
    arrow(ax, (outcome_xs[1] + outcome_w / 2, outcome_y), (0.54, 0.095),
          connectionstyle="arc3,rad=0.06", linewidth=1.1, mutation_scale=11)

    output = FIGURE_ROOT / "Figure1_PRISMA_flow.png"
    fig.savefig(output, dpi=FIGURE_DPI, facecolor="white")
    plt.close(fig)
    return output


TASK_CLASS_COLORS = {
    "Perception AI": "#3E82CC",
    "Judgment AI": "#ED7045",
    "Communication/Workflow AI": "#2E9B50",
}
TASK_CLASS_MARKERS = {
    "Perception AI": "o",
    "Judgment AI": "s",
    "Communication/Workflow AI": "^",
}

SHORT_LABELS = {
    "Prostate MRI reader assistance": "Prostate MRI",
    "Prostate digital pathology": "Prostate pathology",
    "Selected bladder cystoscopy systems": "Bladder cystoscopy",
    "PSMA PET quantification and lesion support": "PSMA PET",
    "Micro-ultrasound lesion localization": "Micro-ultrasound",
    "Renal radiomics and renal-mass prediction": "Renal radiomics",
    "UTI triage and stewardship support": "UTI triage",
    "Functional urology and neurourology prediction": "Functional urology",
    "Surgical video analytics and feedback": "Surgical video",
    "MDT and pathway decision support": "MDT/pathway support",
    "AI-assisted sperm selection for ICSI": "ICSI sperm selection",
    "Male infertility and sperm-retrieval prediction": "Male infertility prediction",
    "ED and sexual-function outcome prediction": "ED prediction",
    "Clinician-reviewed patient-message response support": "Patient-message support",
    "Ambient documentation support": "Ambient documentation",
    "Retrieval-grounded guideline support": "Retrieval-grounded LLMs",
}

LABEL_OFFSETS = {
    "Prostate MRI reader assistance": (-98, 18),
    "Prostate digital pathology": (25, -25),
    "Selected bladder cystoscopy systems": (-132, 20),
    "PSMA PET quantification and lesion support": (-112, 32),
    "Micro-ultrasound lesion localization": (-25, 43),
    "Renal radiomics and renal-mass prediction": (20, -30),
    "UTI triage and stewardship support": (-95, -38),
    "Functional urology and neurourology prediction": (-130, -50),
    "Surgical video analytics and feedback": (-115, 35),
    "MDT and pathway decision support": (25, 33),
    "AI-assisted sperm selection for ICSI": (25, -36),
    "Male infertility and sperm-retrieval prediction": (30, 40),
    "ED and sexual-function outcome prediction": (28, -34),
    "Clinician-reviewed patient-message response support": (25, 34),
    "Ambient documentation support": (25, -35),
    "Retrieval-grounded guideline support": (30, -45),
}


def generate_figure2() -> Path:
    source = SOURCE_ROOT / "Figure2_readiness_map_source_data.csv"
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 16

    class_order = {"Perception AI": 0, "Judgment AI": 1, "Communication/Workflow AI": 2}
    rows.sort(key=lambda row: (
        class_order[row["Task_Class"]],
        -int(row["Highest_Validation_Stage"]),
        SHORT_LABELS[row["Clinical_Task"]],
    ))

    fig, ax = plt.subplots(figsize=(FINAL_WIDTH_IN, 8.0), dpi=FIGURE_DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for stage in range(1, 7):
        ax.axvline(stage, color="#D7E1EE", linestyle=(0, (4, 4)), linewidth=1.15, zorder=0)

    y_values = list(range(len(rows) - 1, -1, -1))
    last_class = None
    class_boundaries = []
    for index, (row, y) in enumerate(zip(rows, y_values)):
        if last_class is not None and row["Task_Class"] != last_class:
            class_boundaries.append(y + 0.5)
        last_class = row["Task_Class"]
        if index % 2 == 0:
            ax.axhspan(y - 0.5, y + 0.5, color="#F7F9FC", zorder=0)
        task = row["Clinical_Task"]
        stage = int(row["Highest_Validation_Stage"])
        count = int(row["Prospective_or_Validation_Study_Count"])
        color = TASK_CLASS_COLORS[row["Task_Class"]]
        marker = TASK_CLASS_MARKERS[row["Task_Class"]]
        if count > 0:
            ax.scatter(stage, y, s=count * 82, marker=marker, color=color, alpha=0.92,
                       edgecolor="white", linewidth=0.9, zorder=3)
        else:
            ax.scatter(stage, y, s=62, marker=marker, facecolors="none", edgecolors=color,
                       linewidth=1.4, zorder=3)
            ax.scatter(stage, y, s=36, marker="x", color=color, linewidth=1.2, zorder=4)
        ax.text(stage + 0.12, y, f"n={count}", ha="left", va="center", fontsize=8.2,
                color="#444A52", zorder=4)
        error = row["Consequence_of_Error"]
        error_face = "#FBE3DA" if error == "High" else "#E8EDF3"
        error_edge = "#D46B4B" if error == "High" else "#8493A3"
        ax.text(6.88, y, error, ha="center", va="center", fontsize=8.0, color="#31363D",
                bbox=dict(boxstyle="round,pad=0.18", facecolor=error_face,
                          edgecolor=error_edge, linewidth=0.75))

    for boundary in class_boundaries:
        ax.axhline(boundary, color="#9AA6B2", linewidth=1.25, zorder=1)

    contextual_labels = []
    for row in rows:
        label = SHORT_LABELS[row["Clinical_Task"]]
        if int(row["Contextual_Anchor_Count"]) > 0:
            label += "†"
        contextual_labels.append(label)

    ax.set_xlim(0.65, 7.18)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xticks([1, 2, 3, 4, 5, 6])
    ax.set_xticklabels(["1", "2", "3", "4", "5", "6"], fontsize=8.8)
    ax.set_yticks(y_values)
    ax.set_yticklabels(contextual_labels, fontsize=8.4)
    ax.set_xlabel("Highest validation stage reached", fontsize=9.3, labelpad=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_linewidth(1.0)
    ax.tick_params(axis="x", length=4, width=0.9)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.text(6.88, len(rows) - 0.08, "Consequence\nof error", ha="center", va="bottom",
            fontsize=8.2, fontweight="bold", color="#3F4650")

    color_handles = [
        plt.Line2D([0], [0], marker=TASK_CLASS_MARKERS[label], color="none", markerfacecolor=color, markeredgecolor="white",
                   markersize=7, label={
                       "Perception AI": "Perception",
                       "Judgment AI": "Judgment",
                       "Communication/Workflow AI": "Communication",
                   }[label])
        for label, color in TASK_CLASS_COLORS.items()
    ]
    class_legend = ax.legend(handles=color_handles, title="Task class", loc="lower left",
                             bbox_to_anchor=(0.0, 1.015), ncol=3, frameon=False,
                             fontsize=7.8, title_fontsize=7.8, handletextpad=0.35,
                             columnspacing=0.75)
    ax.add_artist(class_legend)

    fig.subplots_adjust(left=0.37, right=0.96, bottom=0.09, top=0.89)
    output = FIGURE_ROOT / "Figure2_readiness_map.png"
    fig.savefig(output, dpi=FIGURE_DPI, facecolor="white")
    plt.close(fig)
    return output


def add_figure3_band(ax, y: float, height: float, heading: str, body: str,
                     facecolor: str, edgecolor: str, *, linestyle: str = "-") -> None:
    patch = FancyBboxPatch(
        (0.065, y), 0.87, height,
        boxstyle="round,pad=0.006,rounding_size=0.012",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=1.0,
        linestyle=linestyle,
    )
    ax.add_patch(patch)
    ax.text(0.085, y + height - 0.016, heading, ha="left", va="top",
            fontsize=9.5, fontweight="bold", color=INK)
    ax.text(0.085, y + 0.016, body, ha="left", va="bottom",
            fontsize=8.5, color="#334155", linespacing=1.12)


def add_figure3_card(ax, x: float, y: float, heading: str, action: str,
                     examples: str, facecolor: str) -> None:
    width, height = 0.41, 0.155
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.006,rounding_size=0.012",
        facecolor=facecolor, edgecolor="#6B7280", linewidth=1.0,
    )
    ax.add_patch(patch)
    ax.text(x + 0.022, y + height - 0.020, heading, ha="left", va="top",
            fontsize=9.6, fontweight="bold", color=INK)
    ax.text(x + 0.022, y + height - 0.064, action, ha="left", va="top",
            fontsize=8.4, color="#334155", linespacing=1.12)
    ax.text(x + 0.022, y + 0.018, examples, ha="left", va="bottom",
            fontsize=8.2, color=INK, linespacing=1.12)


def generate_figure3() -> Path:
    fig, ax = plt.subplots(figsize=(FINAL_WIDTH_IN, 7.8), dpi=FIGURE_DPI)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.015, right=0.985, bottom=0.015, top=0.985)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.035, 0.978, "A. Clinical-readiness tiers and contextual exemplars",
            ha="left", va="top", fontsize=11.3, fontweight="bold", color=INK)
    add_figure3_band(
        ax, 0.865, 0.065, "Supervised implementation-planning candidates",
        "Prostate MRI reader assistance; prostate digital pathology; UTI triage.",
        "#DCEBFA", "#5B8FD1",
    )
    add_figure3_band(
        ax, 0.786, 0.065, "Near-implementation candidates",
        "Selected bladder cystoscopy systems; AI-assisted sperm selection for ICSI.",
        "#E3F5E8", "#83B85A",
    )
    add_figure3_band(
        ax, 0.652, 0.120, "Promising adjuncts",
        "PSMA PET quantification; micro-ultrasound; surgical video analytics;\n"
        "Functional-urology and neurourology prediction; male-infertility prediction;\n"
        "ED/sexual-function prediction; patient-message support.",
        "#FFF2C7", "#C79A23",
    )
    add_figure3_band(
        ax, 0.550, 0.088, "Contextual implementation exemplars",
        "Extracorpus; not assigned to a corpus-supported readiness tier:\n"
        "MDT/pathway triage†; ambient documentation†.",
        "#F8FAFC", "#64748B", linestyle="--",
    )
    add_figure3_band(
        ax, 0.442, 0.092, "Exploratory or not ready for routine deployment",
        "Staged use cases: renal radiomics; retrieval-grounded guideline support.\n"
        "Cross-cutting safety boundary (not separately staged): autonomous LLM advice.",
        "#FBE2E2", "#D27A7A",
    )

    ax.text(0.035, 0.418, "B. Human-AI collaboration models", ha="left", va="top",
            fontsize=11.8, fontweight="bold", color=INK)
    add_figure3_card(
        ax, 0.065, 0.235, "Second reader",
        "Clinician confirms candidate findings\nor classifications.",
        "Prostate MRI | Prostate pathology\nBladder cystoscopy", "#DCEFFA",
    )
    add_figure3_card(
        ax, 0.525, 0.235, "Workflow triage",
        "Routine cases are routed; uncertainty\nand high-risk findings are escalated.",
        "UTI stewardship | MDT/pathway triage†\nGuideline support", "#E5F7ED",
    )
    add_figure3_card(
        ax, 0.065, 0.055, "Laboratory and counselling",
        "AI assists bounded laboratory steps or\nsupports pre-procedural counselling.",
        "ICSI sperm selection | Microscopy support\nSperm-retrieval prediction (counselling)", "#FFF6EA",
    )
    add_figure3_card(
        ax, 0.525, 0.055, "Communication support",
        "AI drafts or summarises; a clinician\nchecks provenance and safety.",
        "Patient messages | Ambient scribes†\nPatient-facing summaries", "#F1E8FF",
    )

    output = FIGURE_ROOT / "Figure3_translation_and_collaboration_models.png"
    fig.savefig(output, dpi=FIGURE_DPI, facecolor="white")
    plt.close(fig)
    return output


def verify_image(path: Path, minimum_width: int, minimum_height: int) -> dict[str, object]:
    with Image.open(path) as image:
        assert image.width >= minimum_width and image.height >= minimum_height
        assert image.mode in {"RGB", "RGBA"}
        extrema = image.convert("RGB").getextrema()
        assert any(low < high for low, high in extrema), f"{path.name} appears blank"
        return {"path": str(path), "width": image.width, "height": image.height, "mode": image.mode}


if __name__ == "__main__":
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    figure1 = generate_figure1(read_metric_source())
    figure2 = generate_figure2()
    figure3 = generate_figure3()
    results = [
        verify_image(figure1, 4000, 5000),
        verify_image(figure2, 4000, 4500),
        verify_image(figure3, 4000, 4400),
    ]
    for result in results:
        print(result)
