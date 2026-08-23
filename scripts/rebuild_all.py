#!/usr/bin/env python3
"""Validate the locked inputs, rebuild every figure, and validate the result."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--portable",
        action="store_true",
        help=(
            "Use cross-platform figure validation (PNG integrity and dimensions) instead of "
            "the reference-environment byte hashes."
        ),
    )
    args = parser.parse_args()
    commands = (
        ("scripts/validate_release.py",),
        ("scripts/build_main_figures.py",),
        ("scripts/build_supplementary_figures.py",),
        ("scripts/validate_release.py", "--portable-figures" if args.portable else "--require-figures"),
    )
    child_environment = os.environ.copy()
    child_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for relative_path, *arguments in commands:
        path = ROOT / relative_path
        if not path.exists():
            print(f"Missing script: {relative_path}", file=sys.stderr)
            return 1
        print(f"Running {relative_path} {' '.join(arguments)}".rstrip(), flush=True)
        subprocess.run(
            [sys.executable, str(path), *arguments],
            cwd=ROOT,
            check=True,
            env=child_environment,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
