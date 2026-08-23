#!/usr/bin/env python3
"""Build the checksum map from journal-submission CSV names to repository paths."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "SUBMISSION_FILE_MAP.csv"

FILE_MAP = (
    ("05_supplementary_data/Supplementary_Data_1_PubMed_search_strings.csv", "data/pubmed_search_strings.csv"),
    ("05_supplementary_data/Supplementary_Data_2_screening_database.csv", "data/screening_database.csv"),
    ("05_supplementary_data/Supplementary_Data_3_top25_journals.csv", "data/top_journals.csv"),
    ("05_supplementary_data/Supplementary_Data_4_included_records.csv", "data/included_records.csv"),
    ("05_supplementary_data/Supplementary_Data_5_review_burden_by_operational_analysis_group.csv", "data/review_burden_by_operational_analysis_group.csv"),
    ("05_supplementary_data/Supplementary_Data_6_readiness_anchor_sources.csv", "data/readiness_anchor_sources.csv"),
    ("05_supplementary_data/Supplementary_Data_7_anchor_evidence_matrix.csv", "data/anchor_evidence_matrix.csv"),
    ("05_supplementary_data/Supplementary_Data_8_full_readiness_matrix.csv", "data/readiness_matrix.csv"),
    ("05_supplementary_data/Supplementary_Data_9_readiness_anchor_summary_by_use_case.csv", "data/readiness_anchor_summary_by_use_case.csv"),
    ("05_supplementary_data/Supplementary_Data_10_AI_only_include_audit.csv", "data/ai_only_include_audit.csv"),
    ("05_supplementary_data/Supplementary_Data_11_final_eligibility_verification.csv", "data/final_eligibility_verification.csv"),
    ("06_source_data/Figure1_PRISMA_flow_source_data.csv", "source_data/Figure1_PRISMA_flow_source_data.csv"),
    ("06_source_data/Figure2_readiness_map_source_data.csv", "source_data/Figure2_readiness_map_source_data.csv"),
    ("06_source_data/Supplementary_Figure_S1_publication_trends_source_data.csv", "source_data/Supplementary_Figure_S1_publication_trends_source_data.csv"),
    ("06_source_data/Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv", "source_data/Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv"),
    ("06_source_data/review_burden_by_year.csv", "source_data/review_burden_by_year.csv"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = []
    for submission_path, repository_path in FILE_MAP:
        path = ROOT / repository_path
        if not path.is_file():
            raise FileNotFoundError(path)
        rows.append(
            {
                "Submission_Path": submission_path,
                "Repository_Path": repository_path,
                "Bytes": path.stat().st_size,
                "SHA256": sha256(path),
            }
        )
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("Submission_Path", "Repository_Path", "Bytes", "SHA256"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT.name}: {len(rows)} authoritative CSV mappings")


if __name__ == "__main__":
    main()
