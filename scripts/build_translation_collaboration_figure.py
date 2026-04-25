#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "figures"
SOURCE_A = ROOT / "assets" / "translation_determinants_panel.png"
SOURCE_B = ROOT / "assets" / "collaboration_models_panel.png"

PANEL_A_CROP_TOP = 240
PANEL_B_CROP_TOP = 180
TARGET_WIDTH = 3200


def load_panel(path: Path, crop_top: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    return img.crop((0, crop_top, img.width, img.height))


def resize_to_width(img: Image.Image, width: int) -> Image.Image:
    scale = width / img.width
    height = round(img.height * scale)
    return img.resize((width, height), Image.Resampling.LANCZOS)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    panel_a = resize_to_width(load_panel(SOURCE_A, PANEL_A_CROP_TOP), TARGET_WIDTH)
    panel_b = resize_to_width(load_panel(SOURCE_B, PANEL_B_CROP_TOP), TARGET_WIDTH)

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(12.2, 12.8),
        gridspec_kw={"height_ratios": [panel_a.height, panel_b.height]},
    )

    panel_specs = [
        (axes[0], panel_a, "A. Determinants of translational readiness"),
        (axes[1], panel_b, "B. Human-AI collaboration models"),
    ]

    for ax, panel, title in panel_specs:
        ax.imshow(panel)
        ax.axis("off")
        ax.text(
            0.0,
            1.015,
            title,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=15,
            fontweight="bold",
            color="#222222",
        )

    fig.subplots_adjust(left=0.03, right=0.97, top=0.98, bottom=0.02, hspace=0.14)

    png_path = FIG_DIR / "Figure3_translation_and_collaboration_models.png"
    pdf_path = FIG_DIR / "Figure3_translation_and_collaboration_models.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {png_path.name} and {pdf_path.name}")


if __name__ == "__main__":
    main()
