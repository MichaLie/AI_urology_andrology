#!/usr/bin/env python3
"""Create spreadsheet-safe CSV views while retaining canonical raw JSONL data.

Spreadsheet applications can execute cells whose first non-whitespace
character is ``=``, ``+``, ``-`` or ``@``. CSV quoting does not prevent that.
The public workflow therefore prefixes such text cells with a single quote in
the spreadsheet-facing CSV. The unmodified logical records are written to a
companion JSON Lines file by the calling script.
"""

from __future__ import annotations

import re
from typing import Any


FORMULA_LIKE_TEXT = re.compile(r"^[\t\r\n ]*[=+\-@]")
NEGATIVE_NUMBER = re.compile(r"^-\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?$")
SAFE_PREFIX = "'"


def is_formula_like_text(value: Any) -> bool:
    """Return True only for strings that a spreadsheet may treat as formulae."""
    if not isinstance(value, str) or not FORMULA_LIKE_TEXT.match(value):
        return False
    candidate = value.lstrip("\t\r\n ")
    return not (candidate.startswith("-") and NEGATIVE_NUMBER.fullmatch(candidate))


def escape_spreadsheet_cell(value: Any) -> Any:
    """Prefix formula-like text with an apostrophe; leave all other values intact."""
    if is_formula_like_text(value):
        return SAFE_PREFIX + value
    return value


def spreadsheet_safe_dataframe(dataframe):
    """Return a safe copy plus a transparent column-level transformation report.

    The function deliberately uses DataFrame duck typing so this module and its
    security regression tests retain a standard-library-only import surface.
    """
    safe = dataframe.copy()
    escaped_by_column: dict[str, int] = {}
    for column in safe.columns:
        changed = 0

        def convert(value):
            nonlocal changed
            escaped = escape_spreadsheet_cell(value)
            if escaped != value:
                changed += 1
            return escaped

        safe[column] = safe[column].map(convert)
        if changed:
            escaped_by_column[str(column)] = changed
    return safe, {
        "strategy": "apostrophe-prefix-before-formula-like-text",
        "trigger_regex": FORMULA_LIKE_TEXT.pattern,
        "escaped_cells": sum(escaped_by_column.values()),
        "escaped_by_column": escaped_by_column,
        "canonical_raw_format": "JSON Lines",
    }


def regression_probes() -> dict[str, bool]:
    """Return deterministic safety results used by the release validator."""
    dangerous = ("=1+1", "+SUM(A1:A2)", "-2+3", "@SUM(A1:A2)", "  =1+1", "\t@SUM(A1:A2)")
    benign = (
        "ordinary text",
        "1-2",
        "-2",
        "-1e-3",
        "  -1E+3",
        "'=@already-text",
        "",
    )
    return {
        "all_dangerous_escaped": all(str(escape_spreadsheet_cell(value)).startswith("'") for value in dangerous),
        "all_benign_unchanged": all(escape_spreadsheet_cell(value) == value for value in benign),
        "idempotent_for_safe_prefix": escape_spreadsheet_cell("'=1+1") == "'=1+1",
        "non_string_unchanged": escape_spreadsheet_cell(-2) == -2,
    }


if __name__ == "__main__":
    checks = regression_probes()
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    raise SystemExit(0 if all(checks.values()) else 1)
