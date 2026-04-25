#!/usr/bin/env python3
"""Run all deterministic rebuild scripts for the reproducibility repository."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

SCRIPTS = [
    "scripts/build_prisma_flow_diagram.py",
    "scripts/build_publication_trends_figure.py",
    "scripts/build_review_burden_assets.py",
    "scripts/build_readiness_map_figure.py",
    "scripts/build_translation_collaboration_figure.py",
    "scripts/build_anchor_evidence_matrix.py",
]


def main() -> int:
    for script in SCRIPTS:
        path = ROOT / script
        if not path.exists():
            print(f"Missing script: {script}", file=sys.stderr)
            return 1
        print(f"Running {script}", flush=True)
        subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
