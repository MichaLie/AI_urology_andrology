#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "figures"


def add_box(ax, xy: tuple[float, float], width: float, height: float, title: str, body: str, color: str) -> None:
    x, y = xy
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.2,
        edgecolor="#6b7280",
        facecolor=color,
    )
    ax.add_patch(box)
    ax.text(x + 0.18, y + height - 0.20, title, ha="left", va="top", fontsize=11.5, fontweight="bold", color="#111827")
    ax.text(
        x + 0.18,
        y + height - 0.52,
        fill(body, width=36),
        ha="left",
        va="top",
        fontsize=9.6,
        color="#1f2937",
        linespacing=1.22,
    )


def draw_panel_a(ax) -> None:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    ax.text(0.0, 5.75, "A. Determinants of translational readiness", fontsize=15, fontweight="bold", color="#111827")
    ax.text(0.0, 5.35, "Readiness rises when technical validation is paired with workflow evidence and retained clinical oversight.", fontsize=10.5, color="#374151")

    rows = [
        (
            "Implementation-planning candidates",
            "Prostate MRI reader assistance; prostate digital pathology; UTI triage.",
            "#dbeafe",
        ),
        (
            "Near-implementation candidates",
            "Selected bladder cystoscopy systems; AI-assisted sperm selection for ICSI.",
            "#dcfce7",
        ),
        (
            "Promising adjuncts",
            "PSMA PET quantification; micro-ultrasound; surgical video analytics; male infertility prediction; patient-message support; retrieval-grounded LLMs.",
            "#fef3c7",
        ),
        (
            "Earlier or contextual areas",
            "Contextual MDT/pathway triage and ambient documentation exemplars, renal radiomics, functional-urology models, ED prediction, and autonomous LLM advice remain limited by validation or safety gaps.",
            "#fee2e2",
        ),
    ]
    y = 4.25
    for title, body, color in rows:
        add_box(ax, (0.2, y), 9.2, 0.78, title, body, color)
        y -= 1.05


def draw_panel_b(ax) -> None:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    ax.text(0.0, 5.75, "B. Human-AI collaboration models", fontsize=15, fontweight="bold", color="#111827")
    ax.text(0.0, 5.35, "The credible role is supervised augmentation, with the human checkpoint placed where error consequences are manageable.", fontsize=10.5, color="#374151")

    columns = [
        (
            "Second reader",
            "Imaging and pathology systems surface candidate lesions or classifications for clinician confirmation.",
            "Prostate MRI\nProstate pathology\nBladder cystoscopy",
            "#e0f2fe",
        ),
        (
            "Workflow triage",
            "Rules or models route routine cases while preserving escalation for uncertainty and high-risk findings.",
            "UTI stewardship\nMDT/pathway triage\nGuideline support",
            "#ecfdf5",
        ),
        (
            "Laboratory support",
            "AI assists bounded laboratory steps, but clinical outcome benefit still needs prospective proof.",
            "ICSI sperm selection\nSperm-retrieval prediction\nMicroscopy support",
            "#fff7ed",
        ),
        (
            "Communication support",
            "Drafting or summarizing is acceptable only with clinician review, provenance checks, and hallucination monitoring.",
            "Patient messages\nAmbient scribes\nPatient-facing summaries",
            "#f3e8ff",
        ),
    ]

    x = 0.15
    for title, body, examples, color in columns:
        add_box(ax, (x, 2.05), 2.25, 2.75, title, body, color)
        ax.text(x + 0.18, 2.55, examples, ha="left", va="top", fontsize=9.5, color="#111827", linespacing=1.35)
        x += 2.42

    ax.text(
        0.25,
        0.85,
        "Minimum safeguards: external validation, local calibration, clinician comparison, prospective workflow testing, failure-mode analysis, and post-deployment monitoring.",
        fontsize=10.5,
        color="#111827",
        ha="left",
        va="center",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#f9fafb", edgecolor="#9ca3af"),
    )


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(12.2, 12.8))
    draw_panel_a(axes[0])
    draw_panel_b(axes[1])
    fig.subplots_adjust(left=0.04, right=0.98, top=0.98, bottom=0.04, hspace=0.20)

    png_path = FIG_DIR / "Figure3_translation_and_collaboration_models.png"
    pdf_path = FIG_DIR / "Figure3_translation_and_collaboration_models.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {png_path.name} and {pdf_path.name}")


if __name__ == "__main__":
    main()
