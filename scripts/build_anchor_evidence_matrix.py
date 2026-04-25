#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
S5_PATH = ROOT / "data" / "included_records.csv"
TABLE1_PATH = ROOT / "data" / "readiness_matrix.csv"
OUT_PATH = ROOT / "data" / "anchor_evidence_matrix.csv"


METADATA: dict[str, dict[str, str]] = {
    "31926805": {
        "Design": "Diagnostic study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "32701148": {
        "Design": "Development and validation study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "33328045": {
        "Design": "Blinded clinical validation and deployment study",
        "Centres": "Multicentre",
        "Prospective": "Yes",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "Yes",
        "Patient_or_Economic_Endpoint": "No",
    },
    "33180129": {
        "Design": "AI-pathologist comparative evaluation study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "31926806": {
        "Design": "Population-based diagnostic study",
        "Centres": "Population-based cohort",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "33205846": {
        "Design": "Diagnostic pattern-recognition study",
        "Centres": "Single-centre",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "34079004": {
        "Design": "Blue-light cystoscopy classification study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "33787537": {
        "Design": "Multireader, multicase reader-assistance study",
        "Centres": "Single-centre multireader study",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "32759979": {
        "Design": "AI-assistance comparative study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "35602201": {
        "Design": "Prognostic validation study",
        "Centres": "Population-based cohort",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "Yes",
    },
    "35638089": {
        "Design": "Development and validation cohort study",
        "Centres": "Multicentre statewide collaborative",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "Yes",
    },
    "35021305": {
        "Design": "Predictive cohort study",
        "Centres": "Multi-institutional",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "34473310": {
        "Design": "Multicentre diagnostic study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "34463809": {
        "Design": "Standardized quantification validation study",
        "Centres": "Multicentre trial cohort",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "34968146": {
        "Design": "Comparative validation study against expert nephrometry",
        "Centres": "Single-centre",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "Yes",
    },
    "36867616": {
        "Design": "Development and external validation study",
        "Centres": "Development cohort plus external validation cohort",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "Yes",
    },
    "37227272": {
        "Design": "Multisite development, validation, and deployment study",
        "Centres": "Multisite",
        "Prospective": "Yes",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "Yes",
        "Patient_or_Economic_Endpoint": "Yes",
    },
    "37432899": {
        "Design": "Prospective real-time pilot study",
        "Centres": "Single-centre",
        "Prospective": "Yes",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "Yes",
        "Patient_or_Economic_Endpoint": "No",
    },
    "37039688": {
        "Design": "Interactive explainable reader-assistance study",
        "Centres": "Single-centre multireader study",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "36538386": {
        "Design": "Clinical validation study",
        "Centres": "Clinical validation cohort",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "37389608": {
        "Design": "Multicentre prognostic radiomics study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "Yes",
    },
    "38068407": {
        "Design": "Technical development study",
        "Centres": "Single-centre",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "38652944": {
        "Design": "Laboratory evaluation study",
        "Centres": "Single-centre laboratory cohort",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "38626440": {
        "Design": "Unsupervised phenotyping study",
        "Centres": "Observational cohort",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "Yes",
    },
    "38876123": {
        "Design": "International paired non-inferiority comparative study",
        "Centres": "International multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "39242047": {
        "Design": "External validation study with expert comparison",
        "Centres": "External validation cohort",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "Yes",
    },
    "38142209": {
        "Design": "Narrative translational review",
        "Centres": "Not applicable",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "41646097": {
        "Design": "Guideline-enhanced benchmark study",
        "Centres": "Single benchmark dataset",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "39729119": {
        "Design": "Comparative evaluation of AI-generated communication",
        "Centres": "Single-centre",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "38095671": {
        "Design": "Multicentre segmentation validation study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "38585210": {
        "Design": "Real-time segmentation technical study",
        "Centres": "Single-centre",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "41299699": {
        "Design": "Observational real-time workflow study",
        "Centres": "Single-centre workflow cohort",
        "Prospective": "Yes",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "Yes",
        "Patient_or_Economic_Endpoint": "No",
    },
    "40036728": {
        "Design": "Prospective clinical implementation study",
        "Centres": "Prospective implementation cohort",
        "Prospective": "Yes",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "Yes",
        "Patient_or_Economic_Endpoint": "No",
    },
    "39143247": {
        "Design": "Patient-perspectives study",
        "Centres": "Multicentre survey cohort",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "40512493": {
        "Design": "Multicentre comparative reader-assistance study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "40859774": {
        "Design": "Comparative diagnostic study",
        "Centres": "Comparative office-based cohort",
        "Prospective": "No",
        "Clinician_Comparator": "Yes",
        "External_or_Multicentre_Validation": "No",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "40640619": {
        "Design": "Phase-recognition study",
        "Centres": "18-centre educational network",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "No",
    },
    "40916621": {
        "Design": "Predictive cohort study",
        "Centres": "Multicentre",
        "Prospective": "No",
        "Clinician_Comparator": "No",
        "External_or_Multicentre_Validation": "Yes",
        "Workflow_Implementation": "No",
        "Patient_or_Economic_Endpoint": "Yes",
    },
}


def load_stage_map() -> dict[str, dict[str, str]]:
    with TABLE1_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {
            row["Clinical_Task"]: {
                "Principal_Limitation": row["Principal_Limitation"],
                "Final_Readiness_Stage_Assigned": row["Highest_Validation_Stage"],
            }
            for row in reader
        }


def main() -> None:
    stage_map = load_stage_map()

    with S5_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        priority_rows = [
            row
            for row in reader
            if row.get("Priority_Translational_Evidence") == "Yes"
        ]

    priority_rows.sort(
        key=lambda row: (
            row["Priority_Use_Case"],
            int(row["Year"]),
            row["First_Author"],
            row["Title"],
        )
    )

    output_rows: list[dict[str, str]] = []
    missing_pmids: list[str] = []

    for row in priority_rows:
        pmid = row["PMID"].strip()
        use_case = row["Priority_Use_Case"].strip()
        meta = METADATA.get(pmid)
        stage = stage_map.get(use_case)

        if not pmid or meta is None or stage is None:
            missing_pmids.append(pmid or f"{row['First_Author']} {row['Year']}")
            continue

        output_rows.append(
            {
                "Use_Case": use_case,
                "Study": f"{row['First_Author']} et al., {row['Year']}",
                "Title": row["Title"].strip(),
                "PMID": pmid,
                "DOI": row["DOI"].strip(),
                "Design": meta["Design"],
                "Centres": meta["Centres"],
                "Prospective": meta["Prospective"],
                "Clinician_Comparator": meta["Clinician_Comparator"],
                "External_or_Multicentre_Validation": meta["External_or_Multicentre_Validation"],
                "Workflow_Implementation": meta["Workflow_Implementation"],
                "Patient_or_Economic_Endpoint": meta["Patient_or_Economic_Endpoint"],
                "Principal_Limitation": stage["Principal_Limitation"],
                "Final_Readiness_Stage_Assigned": stage["Final_Readiness_Stage_Assigned"],
            }
        )

    if missing_pmids:
        raise SystemExit(f"Missing S8 metadata for: {missing_pmids}")

    fieldnames = [
        "Use_Case",
        "Study",
        "Title",
        "PMID",
        "DOI",
        "Design",
        "Centres",
        "Prospective",
        "Clinician_Comparator",
        "External_or_Multicentre_Validation",
        "Workflow_Implementation",
        "Patient_or_Economic_Endpoint",
        "Principal_Limitation",
        "Final_Readiness_Stage_Assigned",
    ]

    with OUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {OUT_PATH.relative_to(ROOT)} with {len(output_rows)} rows")


if __name__ == "__main__":
    main()
