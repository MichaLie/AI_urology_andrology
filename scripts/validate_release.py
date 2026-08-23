#!/usr/bin/env python3
"""Validate the locked v1.3.0 public reproducibility release.

This validator uses only the Python standard library. It checks corpus
arithmetic, cross-table propagation, source-data derivations, submission-file
checksums, public metadata, and the corrected Figure 3 classification contract.
The not-yet-reserved version DOI is reported as a separate external release
gate and does not make the offline candidate fail.
"""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
import os
import re
import struct
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

# Importing a local helper must not make an otherwise clean extracted release
# fail the validator's own cache-artifact check.
sys.dont_write_bytecode = True

from csv_safety import is_formula_like_text, regression_probes


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCE = ROOT / "source_data"
MAP_PATH = ROOT / "SUBMISSION_FILE_MAP.csv"
REVIEW_TYPES = {"Review", "Systematic Review", "Scoping Review", "Meta-Analysis", "Network Meta-Analysis"}
CORRESPONDENCE_TYPES = {"Comment", "Editorial", "Letter"}

EXPECTED_DATA = {
    "pubmed_search_strings.csv": 20,
    "screening_database.csv": 5923,
    "top_journals.csv": 25,
    "included_records.csv": 2892,
    "review_burden_by_operational_analysis_group.csv": 10,
    "readiness_anchor_sources.csv": 46,
    "anchor_evidence_matrix.csv": 38,
    "readiness_matrix.csv": 16,
    "readiness_anchor_summary_by_use_case.csv": 16,
    "ai_only_include_audit.csv": 305,
    "final_eligibility_verification.csv": 1270,
    "boundary_evidence.csv": 45,
}
EXPECTED_SOURCE = {
    "Figure1_PRISMA_flow_source_data.csv",
    "Figure2_readiness_map_source_data.csv",
    "Supplementary_Figure_S1_publication_trends_source_data.csv",
    "Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv",
    "review_burden_by_year.csv",
}
EXPECTED_OPERATIONAL_ANALYSIS_GROUPS = {
    "Andrology": 207,
    "Benign/Functional": 170,
    "Bladder Cancer": 422,
    "Broad Reviews": 264,
    "Implementation/ethics/reporting search stream": 268,
    "LLMs & GenAI": 176,
    "Prostate Imaging": 524,
    "Prostate Pathology": 303,
    "Renal/Kidney": 537,
    "Surgical AI": 21,
}

NON_ENGLISH_PMIDS = {
    "31802148", "32329274", "32821957", "33710363", "36073216", "36729176",
    "37198106", "37462961", "37850289", "38285173", "38599593", "38619521",
    "38639655", "38639663", "38702888", "38901984", "39046415", "39048694",
    "39103279", "39177349", "39394622", "39507988", "39563539", "39564838",
    "39939018", "40159133", "40192830", "40377545", "40377592", "40402304",
    "40553373", "40599296", "40659882", "40783914", "40783955", "40788246",
    "41328465", "41656806", "41667933", "41688286",
}
CASE_REPORT_BOUNDARY_PMIDS = {"36941148", "37998590"}
RADIONUCLIDE_BRACKET_PMIDS = {"37942630", "38965552", "39847533", "40935613"}
GENERAL_SCOPE_FULL_TEXT_PMIDS = {"36997578", "36997642", "40652109"}
LANGUAGE_BOUNDARY_SNAPSHOT_SHA256 = "e218af195c5cba319d2b16e69c1dc25e5f92409f8bbda75332302d915aba94ce"
EXPECTED_FULL_TEXT_SNAPSHOT_BY_PMID = {
    "37998590": "cef70914a57dee2721ae1b6661482d6f246fd5e18aeebf8ca48949eba2035e84",
    "36997578": "5979232c05764fd00598782f9fc2dc720f5e7b48934c346cc96a782a9fd217f5",
    "36997642": "f3e126964ede4e172315035830267fd675a5604545874fba1255dcaa1750d4f5",
    "40652109": "5979232c05764fd00598782f9fc2dc720f5e7b48934c346cc96a782a9fd217f5",
}
EXPECTED_OPERATIONAL_GROUP_CORRECTIONS = {
    "32676406": ("Andrology", "Renal/Kidney"),
    "32153047": ("Benign/Functional", "Prostate Pathology"),
    "34671856": ("Andrology", "Renal/Kidney"),
    "39123458": ("LLMs & GenAI", "Prostate Imaging"),
    "38792005": ("Prostate Imaging", "Renal/Kidney"),
    "40427144": ("Benign/Functional", "Renal/Kidney"),
    "40192862": ("Implementation/ethics/reporting search stream", "Benign/Functional"),
    "41381961": ("Implementation/ethics/reporting search stream", "Benign/Functional"),
    "41466327": ("Implementation/ethics/reporting search stream", "Renal/Kidney"),
    "41712191": ("Andrology", "Prostate Imaging"),
    "41932402": ("Andrology", "Prostate Imaging"),
    "41066017": ("Implementation/ethics/reporting search stream", "Benign/Functional"),
    "41519750": ("Implementation/ethics/reporting search stream", "Renal/Kidney"),
}
EXPECTED_AI_AUDIT_EXCLUSION_CODES = {
    "34762720": "E01_NON_UROLOGICAL",
    "35740526": "E01_NON_UROLOGICAL",
    "37621804": "E01_NON_UROLOGICAL",
    "39963119": "E01_NON_UROLOGICAL",
    "40739419": "E01_NON_UROLOGICAL",
    "40928376": "E01_NON_UROLOGICAL",
    "39034409": "E01_NON_UROLOGICAL",
    "37938381": "E01_NON_UROLOGICAL",
    "39328740": "E01_NON_UROLOGICAL",
    "41858507": "E01_NON_UROLOGICAL",
    "37784122": "E01_NON_UROLOGICAL",
    "38390732": "E01_NON_UROLOGICAL",
    "33904010": "E02_EMBRYOLOGY_ONLY",
    "36637586": "E02_EMBRYOLOGY_ONLY",
    "36810139": "E02_EMBRYOLOGY_ONLY",
    "38443941": "E02_EMBRYOLOGY_ONLY",
    "41219923": "E02_EMBRYOLOGY_ONLY",
    "41829403": "E02_EMBRYOLOGY_ONLY",
    "36066079": "E04_PRECLINICAL_NONHUMAN",
    "36502045": "E05_NO_SUBSTANTIVE_AI",
    "32521550": "E05_NO_SUBSTANTIVE_AI",
    "39094536": "E05_NO_SUBSTANTIVE_AI",
    "39727030": "E05_NO_SUBSTANTIVE_AI",
    "39505734": "E05_NO_SUBSTANTIVE_AI",
    "41658336": "E05_NO_SUBSTANTIVE_AI",
    "39950963": "E05_NO_SUBSTANTIVE_AI",
    "41925802": "E05_NO_SUBSTANTIVE_AI",
    "32480069": "E05_NO_SUBSTANTIVE_AI",
    "35082974": "E07_PUBLICATION_STATUS",
    "38090633": "E07_PUBLICATION_STATUS",
    "33328049": "E08_DUPLICATE",
}

ZENODO_CONCEPT_DOI = "10.5281/zenodo.20389926"
RETIRED_VERSION_DOI = "10.5281/zenodo.21127985"
REQUIRED_VERSION_DOI_FILES = ("README.md", "REPRODUCIBILITY.md", "CITATION.cff", ".zenodo.json")

# This contract is deliberately maintained by the release authors rather than
# regenerated by rebuild_all.py. It prevents an accidental edit to both a CSV
# and its checksum map from silently blessing a different research release.
EXPECTED_SUBMISSION_MAP = {
    "05_supplementary_data/Supplementary_Data_1_PubMed_search_strings.csv": ("data/pubmed_search_strings.csv", 4533, "3048633a0a9dff28aac806458fe488c1a2e0de8b47b61406f3b62c9699939c27"),
    "05_supplementary_data/Supplementary_Data_2_screening_database.csv": ("data/screening_database.csv", 2258851, "1527498a3c5cfd27b1e7436c13a50af6f08d492087d9b832b088f87d6c3d91e2"),
    "05_supplementary_data/Supplementary_Data_3_top25_journals.csv": ("data/top_journals.csv", 853, "6ed5a36030289945b95e28235e2ea06226099df6c884f096ef6dad5f4da894d0"),
    "05_supplementary_data/Supplementary_Data_4_included_records.csv": ("data/included_records.csv", 775687, "864bdb52b93b3023e32dca9e9a255fe1dfade1f6286a54e09210be43947a91c2"),
    "05_supplementary_data/Supplementary_Data_5_review_burden_by_operational_analysis_group.csv": ("data/review_burden_by_operational_analysis_group.csv", 699, "f9f2279dcb56644f139ce4d3f71a5635db5686508a092f8a4fa2a9253a151bd3"),
    "05_supplementary_data/Supplementary_Data_6_readiness_anchor_sources.csv": ("data/readiness_anchor_sources.csv", 11286, "4c452985d843ad8d2394e1850a2e2801a2477f9d7c7129b334846469b59b8406"),
    "05_supplementary_data/Supplementary_Data_7_anchor_evidence_matrix.csv": ("data/anchor_evidence_matrix.csv", 17349, "35297eb1ed38e1b6ab4777f21d38ec1e2119de1b5867e4688c26326296a1e652"),
    "05_supplementary_data/Supplementary_Data_8_full_readiness_matrix.csv": ("data/readiness_matrix.csv", 15398, "4a3237e0da2f718069caa621aab45bb5037d5ee266ae948e7a1961ed1283f4b4"),
    "05_supplementary_data/Supplementary_Data_9_readiness_anchor_summary_by_use_case.csv": ("data/readiness_anchor_summary_by_use_case.csv", 19833, "0fcc25562b80284cd415fc55c529ce427825532708dafca766fb88484bbee3b7"),
    "05_supplementary_data/Supplementary_Data_10_AI_only_include_audit.csv": ("data/ai_only_include_audit.csv", 178920, "0266e971084e15ec1930a114007425dc0ba0073e2fca3610f72d264062fd37f0"),
    "05_supplementary_data/Supplementary_Data_11_final_eligibility_verification.csv": ("data/final_eligibility_verification.csv", 771624, "a2e5e2f4b9e7567589f61af9e769030d8c1e42bd65753d64eb665875bc2d6c66"),
    "06_source_data/Figure1_PRISMA_flow_source_data.csv": ("source_data/Figure1_PRISMA_flow_source_data.csv", 3101, "5db8b31d4cb5e51e62380b79af51091684b23fa2184724820451ace67b81d15f"),
    "06_source_data/Figure2_readiness_map_source_data.csv": ("source_data/Figure2_readiness_map_source_data.csv", 15398, "4a3237e0da2f718069caa621aab45bb5037d5ee266ae948e7a1961ed1283f4b4"),
    "06_source_data/Supplementary_Figure_S1_publication_trends_source_data.csv": ("source_data/Supplementary_Figure_S1_publication_trends_source_data.csv", 456, "cfdf631825c82391c8362a75c71277701be554b8f06591ca23f33bce3b31561f"),
    "06_source_data/Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv": ("source_data/Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv", 699, "f9f2279dcb56644f139ce4d3f71a5635db5686508a092f8a4fa2a9253a151bd3"),
    "06_source_data/review_burden_by_year.csv": ("source_data/review_burden_by_year.csv", 465, "1e942a548d0e6dc0c7394c9edeab16e78cf38a92c9ad99e7d2ddb9ac2d2ab234"),
}
EXPECTED_UNMAPPED_DATA_HASHES = {
    "data/boundary_evidence.csv": "01e667f7d4bf6f640d3eabe66fd247f067920fbf1b08b37e5b04ffbfa8126e1e",
    "data/reporting_frameworks.csv": "4d1660add4b49d5d76d6820f344ff137f42d355fc1926f01262d97505edb66bf",
    "data/tiered_readiness_summary.csv": "82884dd13baafc7edcefbfd8df4e0bed7ecfa0018d24155a228a797a8b54a0f6",
}
EXPECTED_FIGURES = {
    "Figure1_PRISMA_flow.png": ((4200, 5400), "511ec8b42ae3260846cfa5f97fcbf72148ff33c6e76ded080f2fd3389621c08e"),
    "Figure2_readiness_map.png": ((4200, 4800), "a1b2fa77ae6169d3a93100d94052d91380e4a486a0abf16316f594e216977344"),
    "Figure3_translation_and_collaboration_models.png": ((4200, 4680), "7966b12d9ccf65a182c7360b4f444e324201d4de7f2b040b59ffde7bc8ebbd9b"),
    "Supplementary_Figure_S1_publication_trends.png": ((4200, 2880), "e32b2a8901e05d15e34584908ca568db27d351acee365cde5a05920b9edabc20"),
    "Supplementary_Figure_S2_review_burden.png": ((4200, 3060), "cb27e2f96ae34f32dba497d7be022c148ff39508bded90cef06d5249f52e5df8"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def zenodo_dois(text: str) -> list[str]:
    return sorted(set(re.findall(r"10\.5281/zenodo\.\d+", text)))


def yaml_scalar(value: str) -> str:
    """Decode the small quoted/unquoted scalar subset used by CFF metadata."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
        return value[1:-1]
    return value


def cff_identifier_entries(cff_text: str) -> list[dict[str, str]]:
    """Read identifier mappings from the top-level CFF identifiers sequence.

    This intentionally avoids treating an unrelated ``value:`` field as a DOI.
    It is a conservative parser for the simple CFF structure used in this
    release, not a general YAML implementation.
    """
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_identifiers = False
    for line in cff_text.splitlines():
        if not in_identifiers:
            if re.match(r"^identifiers:\s*(?:#.*)?$", line):
                in_identifiers = True
            continue
        if line.strip() and not line[0].isspace():
            break
        item_match = re.match(r"^\s*-\s*([A-Za-z][\w-]*):\s*(.*?)\s*$", line)
        if item_match:
            if current is not None:
                entries.append(current)
            current = {item_match.group(1): yaml_scalar(item_match.group(2))}
            continue
        field_match = re.match(r"^\s+([A-Za-z][\w-]*):\s*(.*?)\s*$", line)
        if field_match and current is not None:
            current[field_match.group(1)] = yaml_scalar(field_match.group(2))
    if current is not None:
        entries.append(current)
    return entries


def cff_doi_identifier_values(cff_text: str) -> list[str]:
    """Return complete DOI-typed CFF scalar values without substring extraction."""
    values: list[str] = []
    for entry in cff_identifier_entries(cff_text):
        if entry.get("type", "").strip().lower() == "doi":
            values.append(entry.get("value", "").strip())
    return sorted(set(values))


def cff_doi_identifiers(cff_text: str) -> list[str]:
    """Return only exact Zenodo DOI scalars from DOI-typed CFF identifiers."""
    return [
        value
        for value in cff_doi_identifier_values(cff_text)
        if re.fullmatch(r"10\.5281/zenodo\.\d+", value)
    ]


def evaluate_version_doi_gate(
    expected_doi: str,
    text_by_file: dict[str, str],
    cff_text: str,
    zenodo_metadata: dict,
) -> dict[str, object]:
    """Require one reserved version DOI in every mandated repository file."""
    doi_by_file = {name: zenodo_dois(text_by_file.get(name, "")) for name in REQUIRED_VERSION_DOI_FILES}
    version_dois_by_file = {
        name: [doi for doi in dois if doi != ZENODO_CONCEPT_DOI]
        for name, dois in doi_by_file.items()
    }
    cff_doi_values = cff_doi_identifier_values(cff_text)
    cff_declared_dois = cff_doi_identifiers(cff_text)
    cff_version_dois = [doi for doi in cff_declared_dois if doi != ZENODO_CONCEPT_DOI]
    cff_declares_expected = bool(expected_doi and cff_version_dois == [expected_doi])
    zenodo_top_level_doi = zenodo_metadata.get("doi")
    zenodo_declared_dois: list[str] = []
    if isinstance(zenodo_top_level_doi, str):
        zenodo_declared_dois.extend(zenodo_dois(zenodo_top_level_doi))
    for related in zenodo_metadata.get("related_identifiers", []):
        if isinstance(related, dict) and isinstance(related.get("identifier"), str):
            zenodo_declared_dois.extend(zenodo_dois(related["identifier"]))
    zenodo_declared_dois = sorted(set(zenodo_declared_dois))
    zenodo_version_dois = [doi for doi in zenodo_declared_dois if doi != ZENODO_CONCEPT_DOI]
    passed = (
        bool(expected_doi)
        and expected_doi != RETIRED_VERSION_DOI
        and all(version_dois_by_file[name] == [expected_doi] for name in REQUIRED_VERSION_DOI_FILES)
        and cff_declares_expected
        and isinstance(zenodo_top_level_doi, str)
        and zenodo_top_level_doi.strip() == expected_doi
        and zenodo_version_dois == [expected_doi]
    )
    return {
        "passed": passed,
        "status": "READY" if passed else "PENDING_APPROVAL_AND_NEW_ZENODO_VERSION_DOI",
        "expected_version_doi": expected_doi or None,
        "doi_by_required_file": doi_by_file,
        "version_dois_by_required_file": version_dois_by_file,
        "cff_doi_typed_values": cff_doi_values,
        "cff_structured_dois": cff_declared_dois,
        "cff_structured_version_dois": cff_version_dois,
        "cff_declares_expected_version_doi": cff_declares_expected,
        "zenodo_top_level_doi": zenodo_top_level_doi,
        "zenodo_top_level_declares_expected_version_doi": bool(
            expected_doi
            and isinstance(zenodo_top_level_doi, str)
            and zenodo_top_level_doi.strip() == expected_doi
        ),
        "zenodo_structured_dois": zenodo_declared_dois,
        "zenodo_structured_version_dois": zenodo_version_dois,
    }


def cff_license_values(cff_text: str) -> list[str]:
    """Read a top-level CFF license scalar, inline list, or block sequence."""
    lines = cff_text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^license:\s*(.*?)\s*$", line)
        if not match:
            continue
        inline = match.group(1)
        if inline:
            if inline.startswith("[") and inline.endswith("]"):
                return sorted(
                    {
                        yaml_scalar(item)
                        for item in inline[1:-1].split(",")
                        if yaml_scalar(item)
                    }
                )
            return [yaml_scalar(inline)]
        values: list[str] = []
        for continuation in lines[index + 1 :]:
            if continuation.strip() and not continuation[0].isspace():
                break
            item = re.match(r"^\s+-\s*(.*?)\s*$", continuation)
            if item and yaml_scalar(item.group(1)):
                values.append(yaml_scalar(item.group(1)))
        return sorted(set(values))
    return []


def markdown_license_section(readme_text: str) -> str:
    """Return the level-two License/Licence section, or an empty string."""
    match = re.search(
        r"^##\s+Licen[cs]e\b.*?(?=^##\s|\Z)",
        readme_text,
        flags=re.M | re.I | re.S,
    )
    return match.group(0) if match else ""


def build_license_file_evidence(
    file_bytes_by_path: dict[str, bytes],
    file_integrity_by_path: dict[str, dict[str, bool]] | None = None,
) -> dict[str, dict[str, object]]:
    """Describe exact licence-file bytes and declared SPDX markers."""
    file_integrity_by_path = file_integrity_by_path or {}
    evidence: dict[str, dict[str, object]] = {}
    for path, payload in sorted(file_bytes_by_path.items()):
        try:
            text = payload.decode("utf-8", errors="strict")
            utf8_valid = True
        except UnicodeDecodeError:
            text = ""
            utf8_valid = False
        markers = re.findall(
            r"^SPDX-License-Identifier:\s*([^\s]+)\s*$",
            text,
            flags=re.M | re.I,
        )
        integrity = file_integrity_by_path.get(path, {})
        evidence[path] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "utf8_valid": utf8_valid,
            "nonempty": bool(payload),
            "spdx_identifiers": markers,
            "regular_file_no_symlink": integrity.get("regular_file_no_symlink", True),
            "resolved_within_repository": integrity.get("resolved_within_repository", True),
        }
    return evidence


def evaluate_license_gate(
    expected_profile: object,
    license_file_evidence: dict[str, dict[str, object]],
    readme_text: str,
    cff_text: str,
    zenodo_metadata: dict,
) -> dict[str, object]:
    """Require one explicit, author-approved and synchronized licence profile."""
    required_keys = {"code_spdx", "data_spdx", "zenodo_license", "license_files"}
    profile_valid = isinstance(expected_profile, dict) and required_keys <= set(expected_profile)
    if profile_valid:
        expected_files_raw = expected_profile.get("license_files")
        profile_valid = (
            isinstance(expected_profile.get("code_spdx"), str)
            and bool(expected_profile["code_spdx"].strip())
            and isinstance(expected_profile.get("data_spdx"), str)
            and bool(expected_profile["data_spdx"].strip())
            and isinstance(expected_profile.get("zenodo_license"), str)
            and bool(expected_profile["zenodo_license"].strip())
            and isinstance(expected_files_raw, dict)
            and bool(expected_files_raw)
            and all(
                isinstance(path, str)
                and bool(path.strip())
                and isinstance(metadata, dict)
                and isinstance(metadata.get("spdx"), str)
                and bool(metadata["spdx"].strip())
                and isinstance(metadata.get("sha256"), str)
                and re.fullmatch(r"[0-9a-fA-F]{64}", metadata["sha256"].strip()) is not None
                for path, metadata in expected_files_raw.items()
            )
        )
    expected_files = (
        sorted(path.strip() for path in expected_profile["license_files"])
        if profile_valid
        else []
    )
    expected_file_metadata = (
        {
            path.strip(): {
                "spdx": metadata["spdx"].strip(),
                "sha256": metadata["sha256"].strip().lower(),
            }
            for path, metadata in expected_profile["license_files"].items()
        }
        if profile_valid
        else {}
    )
    expected_cff = (
        sorted({expected_profile["code_spdx"].strip(), expected_profile["data_spdx"].strip()})
        if profile_valid
        else []
    )
    section = markdown_license_section(readme_text)
    section_tokens = {
        token.rstrip(".")
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9.-]*", section)
    }
    cff_licenses = cff_license_values(cff_text)
    zenodo_license = zenodo_metadata.get("license")
    readme_identifiers_present = bool(
        profile_valid
        and all(identifier.lower() in {token.lower() for token in section_tokens} for identifier in expected_cff)
    )
    actual_files = sorted(license_file_evidence)
    profile_file_spdx = sorted(
        {metadata["spdx"] for metadata in expected_file_metadata.values()}
    )
    exact_file_set = bool(profile_valid and actual_files == expected_files)
    file_hashes_exact = bool(
        exact_file_set
        and all(
            license_file_evidence[path].get("sha256") == expected_file_metadata[path]["sha256"]
            for path in expected_files
        )
    )
    file_contents_valid = bool(
        exact_file_set
        and all(
            license_file_evidence[path].get("utf8_valid") is True
            and license_file_evidence[path].get("nonempty") is True
            and license_file_evidence[path].get("spdx_identifiers")
            == [expected_file_metadata[path]["spdx"]]
            for path in expected_files
        )
    )
    file_paths_valid = bool(
        exact_file_set
        and all(
            license_file_evidence[path].get("regular_file_no_symlink") is True
            and license_file_evidence[path].get("resolved_within_repository") is True
            for path in expected_files
        )
    )
    checks = {
        "expected_profile_valid": bool(profile_valid),
        "profile_file_spdx_matches_declared_terms": bool(
            profile_valid and profile_file_spdx == expected_cff
        ),
        "license_files_exact": exact_file_set,
        "license_files_are_regular_non_symlinks_within_repository": file_paths_valid,
        "license_file_hashes_exact": file_hashes_exact,
        "license_file_contents_and_spdx_markers_exact": file_contents_valid,
        "readme_license_section_synchronized": readme_identifiers_present,
        "citation_licenses_exact": bool(profile_valid and cff_licenses == expected_cff),
        "zenodo_license_exact": bool(
            profile_valid
            and isinstance(zenodo_license, str)
            and zenodo_license.strip().lower() == expected_profile["zenodo_license"].strip().lower()
        ),
    }
    passed = all(checks.values())
    return {
        "passed": passed,
        "status": "READY" if passed else "PENDING_AUTHOR_LICENSE_APPROVAL",
        "profile_name": expected_profile.get("name") if isinstance(expected_profile, dict) else None,
        "checks": checks,
        "expected_license_files": expected_files,
        "expected_license_file_metadata": expected_file_metadata,
        "actual_license_files": actual_files,
        "actual_license_file_evidence": license_file_evidence,
        "expected_citation_licenses": expected_cff,
        "actual_citation_licenses": cff_licenses,
        "expected_zenodo_license": (
            expected_profile.get("zenodo_license") if isinstance(expected_profile, dict) else None
        ),
        "actual_zenodo_license": zenodo_license,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, strict=True))


def publication_flags(row: dict[str, str]) -> tuple[bool, bool, bool]:
    tokens = {token.strip() for token in row["Publication_Type"].split(";") if token.strip()}
    review = bool(tokens & REVIEW_TYPES)
    correspondence = bool(tokens & CORRESPONDENCE_TYPES)
    return review, correspondence, review or correspondence


def burden_summary(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    output: dict[str, dict[str, float | int]] = {}
    for group, group_rows in grouped.items():
        reviews = correspondence = combined = 0
        for row in group_rows:
            is_review, is_correspondence, is_combined = publication_flags(row)
            reviews += int(is_review)
            correspondence += int(is_correspondence)
            combined += int(is_combined)
        total = len(group_rows)
        output[group] = {
            "total_records": total,
            "other_records": total - combined,
            "review_type_records": reviews,
            "correspondence_editorial_records": correspondence,
            "review_or_correspondence_editorial_records": combined,
            "review_type_pct": round(100 * reviews / total, 1),
            "correspondence_editorial_pct": round(100 * correspondence / total, 1),
            "review_or_correspondence_editorial_pct": round(100 * combined / total, 1),
        }
    return output


def normalize_burden(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, float | int]]:
    integer_fields = {
        "total_records",
        "other_records",
        "review_type_records",
        "correspondence_editorial_records",
        "review_or_correspondence_editorial_records",
    }
    percent_fields = {
        "review_type_pct",
        "correspondence_editorial_pct",
        "review_or_correspondence_editorial_pct",
    }
    return {
        row[key]: {
            field: int(row[field]) if field in integer_fields else float(row[field])
            for field in sorted(integer_fields | percent_fields)
        }
        for row in rows
    }


def inspect_png(path: Path) -> tuple[tuple[int, int] | None, list[str]]:
    """Parse every PNG chunk and verify its CRC rather than trusting a header."""
    payload = path.read_bytes()
    issues: list[str] = []
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return None, ["invalid signature"]
    position = 8
    dimensions = None
    idat_chunks: list[bytes] = []
    saw_iend = False
    image_header: tuple[int, int, int, int, int] | None = None
    while position + 12 <= len(payload):
        length = struct.unpack(">I", payload[position:position + 4])[0]
        chunk_type = payload[position + 4:position + 8]
        end = position + 12 + length
        if end > len(payload):
            issues.append("truncated chunk")
            break
        chunk = payload[position + 8:position + 8 + length]
        declared_crc = struct.unpack(">I", payload[position + 8 + length:end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk) & 0xFFFFFFFF
        if declared_crc != actual_crc:
            issues.append(f"CRC mismatch in {chunk_type.decode('ascii', 'replace')}")
        if chunk_type == b"IHDR":
            if dimensions is not None or length != 13:
                issues.append("invalid IHDR")
            else:
                dimensions = struct.unpack(">II", chunk[:8])
                width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
                image_header = (width, height, bit_depth, color_type, interlace)
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk)
        elif chunk_type == b"IEND":
            saw_iend = length == 0
            position = end
            break
        position = end
    if dimensions is None:
        issues.append("missing IHDR")
    if not idat_chunks:
        issues.append("missing IDAT")
    if not saw_iend:
        issues.append("missing IEND")
    if position != len(payload):
        issues.append("bytes after IEND or incomplete parse")
    if not issues and image_header is not None:
        width, height, bit_depth, color_type, interlace = image_header
        channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color_type)
        if bit_depth != 8 or channels is None or interlace != 0:
            issues.append(
                f"unsupported pixel format for nonblank validation: bit_depth={bit_depth}, "
                f"color_type={color_type}, interlace={interlace}"
            )
        else:
            try:
                decoded = zlib.decompress(b"".join(idat_chunks))
                stride = width * channels
                expected_length = height * (stride + 1)
                if len(decoded) != expected_length:
                    issues.append(
                        f"unexpected decoded length: {len(decoded)} != {expected_length}"
                    )
                else:
                    previous = bytearray(stride)
                    first_color: tuple[int, ...] | None = None
                    varied = False
                    offset = 0

                    def paeth(left: int, above: int, upper_left: int) -> int:
                        prediction = left + above - upper_left
                        left_distance = abs(prediction - left)
                        above_distance = abs(prediction - above)
                        upper_left_distance = abs(prediction - upper_left)
                        if left_distance <= above_distance and left_distance <= upper_left_distance:
                            return left
                        if above_distance <= upper_left_distance:
                            return above
                        return upper_left

                    for _ in range(height):
                        filter_type = decoded[offset]
                        raw = decoded[offset + 1:offset + 1 + stride]
                        offset += stride + 1
                        row = bytearray(stride)
                        for index, value in enumerate(raw):
                            left = row[index - channels] if index >= channels else 0
                            above = previous[index]
                            upper_left = previous[index - channels] if index >= channels else 0
                            if filter_type == 0:
                                predictor = 0
                            elif filter_type == 1:
                                predictor = left
                            elif filter_type == 2:
                                predictor = above
                            elif filter_type == 3:
                                predictor = (left + above) // 2
                            elif filter_type == 4:
                                predictor = paeth(left, above, upper_left)
                            else:
                                raise ValueError(f"unsupported PNG filter {filter_type}")
                            row[index] = (value + predictor) & 0xFF
                        color_channels = 1 if color_type in {0, 4} else 3
                        for index in range(0, stride, channels):
                            color = tuple(row[index:index + color_channels])
                            if first_color is None:
                                first_color = color
                            elif color != first_color:
                                varied = True
                                break
                        if varied:
                            break
                        previous = row
                    if not varied:
                        issues.append("image pixels are uniform/contentless")
            except (ValueError, zlib.error) as error:
                issues.append(f"pixel decode failed: {error}")
    return dimensions, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-figures",
        action="store_true",
        help="Fail unless all five reference-environment figure files are present and byte-exact.",
    )
    parser.add_argument(
        "--portable-figures",
        action="store_true",
        help="Require all five figures and validate PNG integrity/dimensions without host-specific byte hashes.",
    )
    args = parser.parse_args()
    if args.require_figures and args.portable_figures:
        parser.error("--require-figures and --portable-figures are mutually exclusive")
    checks: list[dict[str, object]] = []

    def add(name: str, passed: bool, detail: object) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    actual_data = {path.name for path in DATA.glob("*.csv")}
    expected_data_files = set(EXPECTED_DATA) | {"reporting_frameworks.csv", "tiered_readiness_summary.csv"}
    actual_source = {path.name for path in SOURCE.glob("*.csv")}
    add("Exact public data-table set", actual_data == expected_data_files, sorted(actual_data))
    add("Exact source-data table set", actual_source == EXPECTED_SOURCE, sorted(actual_source))

    tables = {name: read_csv(DATA / name) for name in EXPECTED_DATA}
    sources = {name: read_csv(SOURCE / name) for name in EXPECTED_SOURCE}
    for name, expected_count in EXPECTED_DATA.items():
        add(f"Row count: {name}", len(tables[name]) == expected_count, len(tables[name]))

    data2 = tables["screening_database.csv"]
    data4 = tables["included_records.csv"]
    data5 = tables["review_burden_by_operational_analysis_group.csv"]
    data6 = tables["readiness_anchor_sources.csv"]
    data7 = tables["anchor_evidence_matrix.csv"]
    data8 = tables["readiness_matrix.csv"]
    data9 = tables["readiness_anchor_summary_by_use_case.csv"]
    data10 = tables["ai_only_include_audit.csv"]
    data11 = tables["final_eligibility_verification.csv"]
    boundary_evidence = tables["boundary_evidence.csv"]

    for label, rows in (("Data 2", data2), ("Data 4", data4), ("Data 7", data7), ("Data 11", data11)):
        pmids = [row["PMID"] for row in rows]
        add(f"Unique numeric PMIDs: {label}", len(pmids) == len(set(pmids)) and all(pmid.isdigit() for pmid in pmids), {"rows": len(pmids), "unique": len(set(pmids))})

    data2_by = {row["PMID"]: row for row in data2}
    data4_by = {row["PMID"]: row for row in data4}
    included2 = {row["PMID"] for row in data2 if row["Analytic_Set_Decision"] == "INCLUDE"}
    stratum_mismatches = [
        pmid
        for pmid, row in data4_by.items()
        if data2_by[pmid]["Operational_Analysis_Group"] != row["Operational_Analysis_Group"]
    ]
    add(
        "Data 2 INCLUDE set equals Data 4 with identical operational analysis groups",
        included2 == set(data4_by) and not stratum_mismatches,
        {
            "Data2_INCLUDE": len(included2),
            "Data4": len(data4_by),
            "operational_analysis_group_mismatches": stratum_mismatches[:20],
        },
    )

    strata = dict(Counter(row["Operational_Analysis_Group"] for row in data4))
    add(
        "Final ten retained operational-analysis-group totals",
        strata == EXPECTED_OPERATIONAL_ANALYSIS_GROUPS,
        dict(sorted(strata.items())),
    )

    outcomes = Counter(row["Eligibility_Outcome"] for row in data11)
    expected_outcomes = Counter(
        {"INCLUDE": 797, "OPERATIONAL_ANALYSIS_GROUP_CORRECTION": 13, "CONTEXT_ONLY": 106, "EXCLUDE": 354}
    )
    add("Final eligibility-verification outcomes", outcomes == expected_outcomes, dict(outcomes))
    add(
        "Final-corpus arithmetic",
        2082 + outcomes["INCLUDE"] + outcomes["OPERATIONAL_ANALYSIS_GROUP_CORRECTION"] == 2892,
        {"outside_verification": 2082, **dict(outcomes)},
    )
    expected_data11_fields = {
        "PMID", "DOI", "First_Author", "Year", "Title", "Journal", "Publication_Type",
        "Original_Operational_Analysis_Group", "Eligibility_Outcome", "Eligibility_Code", "Final_Operational_Analysis_Group",
        "Analytic_Set_Decision", "Narrative_Context_Status", "Trigger_Rule_IDs", "Evidence_Level",
        "Eligibility_Rationale",
    }
    add("Data 11 field contract", set(data11[0]) == expected_data11_fields, sorted(data11[0]))
    data11_logic = []
    for row in data11:
        outcome = row["Eligibility_Outcome"]
        expected_analytic = "INCLUDE" if outcome in {"INCLUDE", "OPERATIONAL_ANALYSIS_GROUP_CORRECTION"} else "EXCLUDE"
        expected_context = "CONTEXT_ONLY" if outcome == "CONTEXT_ONLY" else "NOT_CONTEXT_ONLY"
        if (
            row["Analytic_Set_Decision"] != expected_analytic
            or row["Narrative_Context_Status"] != expected_context
            or not row["Trigger_Rule_IDs"].strip()
            or not row["Evidence_Level"].strip()
            or not row["Eligibility_Rationale"].strip()
            or row["Eligibility_Rationale"].strip().lower() in {
                "eligible and retained in the analytic corpus.",
                "retained in the analytic corpus.",
            }
        ):
            data11_logic.append(row["PMID"])
    add("Data 11 outcome/status/rule/evidence/rationale logic", not data11_logic, data11_logic[:20])
    data11_by = {row["PMID"]: row for row in data11}

    observed_group_corrections = {
        row["PMID"]: (
            row["Original_Operational_Analysis_Group"],
            row["Final_Operational_Analysis_Group"],
        )
        for row in data11
        if row["Eligibility_Outcome"] == "OPERATIONAL_ANALYSIS_GROUP_CORRECTION"
    }
    group_correction_issues = {
        pmid: {
            "observed": observed_group_corrections.get(pmid),
            "expected": expected,
            "code": data11_by.get(pmid, {}).get("Eligibility_Code"),
            "Data2": data2_by.get(pmid, {}).get("Operational_Analysis_Group"),
            "Data4": data4_by.get(pmid, {}).get("Operational_Analysis_Group"),
        }
        for pmid, expected in EXPECTED_OPERATIONAL_GROUP_CORRECTIONS.items()
        if (
            observed_group_corrections.get(pmid) != expected
            or data11_by.get(pmid, {}).get("Eligibility_Code") != "C01_OPERATIONAL_ANALYSIS_GROUP_CORRECTION"
            or data2_by.get(pmid, {}).get("Operational_Analysis_Group") != expected[1]
            or data4_by.get(pmid, {}).get("Operational_Analysis_Group") != expected[1]
        )
    }
    add(
        "Exact 13 operational-analysis-group corrections are propagated",
        observed_group_corrections == EXPECTED_OPERATIONAL_GROUP_CORRECTIONS and not group_correction_issues,
        {
            "observed": observed_group_corrections,
            "issues": group_correction_issues,
        },
    )
    correction_rationale_issues = {
        row["PMID"]: row["Eligibility_Rationale"]
        for row in data11
        if row["Eligibility_Outcome"] == "OPERATIONAL_ANALYSIS_GROUP_CORRECTION"
        and re.search(r"\b(?:domain|retrieval[-_ ]strat(?:um|a))\b", row["Eligibility_Rationale"], re.I)
    }
    add(
        "Operational-analysis-group correction rationales use current semantics",
        not correction_rationale_issues,
        correction_rationale_issues,
    )

    data10_exclusions = [row for row in data10 if row["Final_Eligibility_Status"] == "EXCLUDE"]
    missing_data10_codes = [row["PMID"] for row in data10_exclusions if not row["Final_Eligibility_Code"].strip()]
    data10_code_counts = Counter(row["Final_Eligibility_Code"] for row in data10_exclusions)
    expected_data10_code_counts = Counter(
        {
            "E01_NON_UROLOGICAL": 12,
            "E02_EMBRYOLOGY_ONLY": 6,
            "E04_PRECLINICAL_NONHUMAN": 1,
            "E05_NO_SUBSTANTIVE_AI": 15,
            "E07_PUBLICATION_STATUS": 3,
            "E08_DUPLICATE": 1,
            "E09_DATE_LANGUAGE_INDEXING": 4,
        }
    )
    data10_by_pmid = {row["PMID"]: row for row in data10}
    mapped_code_issues = {
        pmid: {
            "expected": code,
            "observed": data10_by_pmid.get(pmid, {}).get("Final_Eligibility_Code"),
        }
        for pmid, code in EXPECTED_AI_AUDIT_EXCLUSION_CODES.items()
        if data10_by_pmid.get(pmid, {}).get("Final_Eligibility_Code") != code
    }
    add(
        "Data 10 exclusion codes are complete and match the author-approved mapping",
        not missing_data10_codes
        and data10_code_counts == expected_data10_code_counts
        and not mapped_code_issues,
        {
            "missing": missing_data10_codes,
            "counts": dict(data10_code_counts),
            "mapping_issues": mapped_code_issues,
        },
    )

    observed_language_pmids = {
        row["PMID"]
        for row in data11
        if row["Eligibility_Code"] == "E09_DATE_LANGUAGE_INDEXING"
    }
    language_boundary_issues = {
        pmid: {
            "verification": data11_by.get(pmid),
            "screening_decision": data2_by.get(pmid, {}).get("Analytic_Set_Decision"),
            "in_data4": pmid in data4_by,
        }
        for pmid in NON_ENGLISH_PMIDS
        if (
            pmid not in data11_by
            or data11_by[pmid]["Eligibility_Outcome"] != "EXCLUDE"
            or data11_by[pmid]["Eligibility_Code"] != "E09_DATE_LANGUAGE_INDEXING"
            or data11_by[pmid]["Evidence_Level"] != "PUBMED_METADATA"
            or data2_by.get(pmid, {}).get("Analytic_Set_Decision") != "EXCLUDE"
            or pmid in data4_by
        )
    }
    add(
        "Exact 40-record PubMed language-boundary correction is propagated",
        observed_language_pmids == NON_ENGLISH_PMIDS and not language_boundary_issues,
        {
            "observed_count": len(observed_language_pmids),
            "missing_or_mispropagated": language_boundary_issues,
            "unexpected_pmids": sorted(observed_language_pmids - NON_ENGLISH_PMIDS),
        },
    )
    provisional_language_rows = {
        row["PMID"]: row
        for row in (
            data4
            + [row for row in data11 if row["Eligibility_Code"] == "E09_DATE_LANGUAGE_INDEXING"]
        )
    }
    bracket_initial_pmids = {
        pmid
        for pmid, row in provisional_language_rows.items()
        if row["Title"].lstrip().startswith("[")
    }
    add(
        "Final title-pattern language-boundary route is exactly reproducible",
        len(provisional_language_rows) == 2932
        and bracket_initial_pmids == NON_ENGLISH_PMIDS | RADIONUCLIDE_BRACKET_PMIDS,
        {
            "provisional_records": len(provisional_language_rows),
            "bracket_initial_count": len(bracket_initial_pmids),
            "language_candidates": sorted(bracket_initial_pmids & NON_ENGLISH_PMIDS),
            "radionuclide_titles": sorted(bracket_initial_pmids & RADIONUCLIDE_BRACKET_PMIDS),
            "unexpected": sorted(
                bracket_initial_pmids - NON_ENGLISH_PMIDS - RADIONUCLIDE_BRACKET_PMIDS
            ),
        },
    )

    case_boundary_issues = {
        pmid: {
            "verification": data11_by.get(pmid),
            "screening_decision": data2_by.get(pmid, {}).get("Analytic_Set_Decision"),
            "in_data4": pmid in data4_by,
        }
        for pmid in CASE_REPORT_BOUNDARY_PMIDS
        if (
            pmid not in data11_by
            or data11_by[pmid]["Eligibility_Outcome"] != "INCLUDE"
            or data11_by[pmid]["Analytic_Set_Decision"] != "INCLUDE"
            or "DEEP_SCOPE_PUBLICATION_STATUS" not in data11_by[pmid]["Trigger_Rule_IDs"]
            or data11_by[pmid]["Evidence_Level"] not in {"PUBMED_ABSTRACT", "PMC_FULL_TEXT"}
            or data2_by.get(pmid, {}).get("Analytic_Set_Decision") != "INCLUDE"
            or pmid not in data4_by
        )
    }
    add(
        "Two case-report boundary records retain substantive validation evidence",
        not case_boundary_issues,
        case_boundary_issues,
    )

    boundary_fields = {
        "Evidence_Type",
        "PMID",
        "PubMed_Language_Values",
        "English_Code_Present",
        "PubMed_Publication_Types",
        "Eligibility_Outcome",
        "Eligibility_Code",
        "Primary_Evidence_Type",
        "Primary_Evidence_Locator",
        "Evidence_Accessed_UTC",
        "Evidence_Snapshot_SHA256",
        "Evidence_Rationale",
    }
    boundary_by_type = Counter(row["Evidence_Type"] for row in boundary_evidence)
    boundary_by_pmid = {row["PMID"]: row for row in boundary_evidence}
    language_boundary_rows = {
        row["PMID"]: row
        for row in boundary_evidence
        if row["Evidence_Type"] == "LANGUAGE_BOUNDARY"
    }
    case_boundary_rows = {
        row["PMID"]: row
        for row in boundary_evidence
        if row["Evidence_Type"] == "CASE_REPORT_EXCEPTION"
    }
    scope_boundary_rows = {
        row["PMID"]: row
        for row in boundary_evidence
        if row["Evidence_Type"] == "GENERAL_SCOPE_FULL_TEXT_CONFIRMATION"
    }
    boundary_row_issues = [
        row["PMID"]
        for row in boundary_evidence
        if (
            not row["PMID"].isdigit()
            or not row["Primary_Evidence_Locator"].startswith("https://")
            or not re.fullmatch(r"[0-9a-f]{64}", row["Evidence_Snapshot_SHA256"])
            or not row["Evidence_Accessed_UTC"].strip()
            or not row["Evidence_Rationale"].strip()
        )
    ]
    language_evidence_issues = {
        pmid: row
        for pmid, row in language_boundary_rows.items()
        if (
            row["English_Code_Present"] != "NO"
            or row["Eligibility_Outcome"] != "EXCLUDE"
            or row["Eligibility_Code"] != "E09_DATE_LANGUAGE_INDEXING"
            or row["Primary_Evidence_Type"] != "PUBMED_XML_METADATA"
            or row["Evidence_Snapshot_SHA256"] != LANGUAGE_BOUNDARY_SNAPSHOT_SHA256
        )
    }
    full_text_hash_issues = {
        pmid: {
            "expected": expected_hash,
            "observed": boundary_by_pmid.get(pmid, {}).get("Evidence_Snapshot_SHA256"),
            "evidence_type": boundary_by_pmid.get(pmid, {}).get("Primary_Evidence_Type"),
        }
        for pmid, expected_hash in EXPECTED_FULL_TEXT_SNAPSHOT_BY_PMID.items()
        if (
            boundary_by_pmid.get(pmid, {}).get("Evidence_Snapshot_SHA256") != expected_hash
            or boundary_by_pmid.get(pmid, {}).get("Primary_Evidence_Type") != "PMC_FULL_TEXT"
        )
    }
    add(
        "Frozen boundary-evidence table matches the 40+2+3 primary-source contract",
        set(boundary_evidence[0]) == boundary_fields
        and len(boundary_by_pmid) == 45
        and boundary_by_type
        == Counter(
            {
                "LANGUAGE_BOUNDARY": 40,
                "CASE_REPORT_EXCEPTION": 2,
                "GENERAL_SCOPE_FULL_TEXT_CONFIRMATION": 3,
            }
        )
        and set(language_boundary_rows) == NON_ENGLISH_PMIDS
        and set(case_boundary_rows) == CASE_REPORT_BOUNDARY_PMIDS
        and set(scope_boundary_rows) == GENERAL_SCOPE_FULL_TEXT_PMIDS
        and not boundary_row_issues
        and not language_evidence_issues
        and not full_text_hash_issues,
        {
            "types": dict(boundary_by_type),
            "row_issues": boundary_row_issues,
            "language_issues": language_evidence_issues,
            "full_text_hash_issues": full_text_hash_issues,
        },
    )

    split6 = Counter(row["In_Analytic_Set"] for row in data6)
    add("Readiness-source corpus/context split", split6 == Counter({"Yes": 38, "No": 8}), dict(split6))
    missing_anchors = [row["PMID"] for row in data7 if row["PMID"] not in data4_by or row["In_Analytic_Set"] != "Yes"]
    add("All 38 in-corpus readiness anchors remain in Data 4", not missing_anchors, missing_anchors)

    bubbles: Counter[str] = Counter()
    for row in data7:
        if row["Prospective"] == "Yes" or row["External_or_Multicentre_Validation"] == "Yes":
            bubbles[row["Use_Case"]] += 1
    expected_bubbles = {row["Clinical_Task"]: int(row["Prospective_or_Validation_Study_Count"]) for row in data8}
    bubble_issues = {task: {"derived": bubbles[task], "reported": expected_bubbles.get(task)} for task in set(bubbles) | set(expected_bubbles) if bubbles[task] != expected_bubbles.get(task)}
    add("Figure 2 bubble counts derive from the 38 anchors", not bubble_issues, bubble_issues)
    add("Figure 2 source is byte-identical to readiness matrix", (SOURCE / "Figure2_readiness_map_source_data.csv").read_bytes() == (DATA / "readiness_matrix.csv").read_bytes(), {"data": sha256(DATA / "readiness_matrix.csv"), "source": sha256(SOURCE / "Figure2_readiness_map_source_data.csv")})
    data9_counts = {row["Use_Case"]: int(row["Prospective_or_Validation_Study_Count"]) for row in data9}
    add("Data 9 bubble totals equal Data 8", data9_counts == expected_bubbles, data9_counts)

    derived_stratum_burden = burden_summary(data4, "Operational_Analysis_Group")
    reported_stratum_burden = normalize_burden(data5, "Operational_Analysis_Group")
    add(
        "Operational-analysis-group review burden independently derives from Data 4",
        derived_stratum_burden == reported_stratum_burden,
        {"derived": derived_stratum_burden, "reported": reported_stratum_burden},
    )
    add(
        "Figure S2 source is byte-identical to Data 5",
        (SOURCE / "Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv").read_bytes()
        == (DATA / "review_burden_by_operational_analysis_group.csv").read_bytes(),
        {
            "data": sha256(DATA / "review_burden_by_operational_analysis_group.csv"),
            "source": sha256(SOURCE / "Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv"),
        },
    )
    derived_year_burden = burden_summary(data4, "Year")
    reported_year_burden = normalize_burden(sources["review_burden_by_year.csv"], "Year")
    add("Annual review burden independently derives from Data 4", derived_year_burden == reported_year_burden, reported_year_burden)

    totals = {
        "review": sum(value["review_type_records"] for value in derived_stratum_burden.values()),
        "correspondence": sum(value["correspondence_editorial_records"] for value in derived_stratum_burden.values()),
        "combined": sum(value["review_or_correspondence_editorial_records"] for value in derived_stratum_burden.values()),
    }
    add("Corrected review-burden totals", totals == {"review": 468, "correspondence": 96, "combined": 564}, totals)

    trend_rows = sources["Supplementary_Figure_S1_publication_trends_source_data.csv"]
    trend_totals = {
        stratum: sum(int(row[stratum]) for row in trend_rows)
        for stratum in EXPECTED_OPERATIONAL_ANALYSIS_GROUPS
    }
    add(
        "Publication-trend totals equal Data 4 operational analysis groups",
        trend_totals == EXPECTED_OPERATIONAL_ANALYSIS_GROUPS
        and sum(int(row["Total"]) for row in trend_rows) == 2892,
        trend_totals,
    )

    flow = {row["Metric_Key"]: int(row["Value"]) for row in sources["Figure1_PRISMA_flow_source_data.csv"]}
    flow_ok = (
        flow["query_union_unique_records"] - flow["prescreen_relevance_exclusions"] == flow["records_screened"] == 5923
        and flow["eligibility_candidates_initial_rules"]
        + flow["eligibility_candidates_second_pass"]
        + flow["eligibility_candidates_renal_boundary_pass"]
        + flow["eligibility_candidates_language_boundary_pass"]
        + flow["eligibility_candidates_case_report_boundary_pass"]
        == flow["eligibility_candidates_flagged"] == 1270
        and flow["eligibility_candidates_context_only"]
        + flow["eligibility_candidates_excluded"]
        == flow["eligibility_records_removed_from_analytic_set"] == 460
        and flow["eligibility_candidates_not_flagged"]
        + flow["eligibility_candidates_confirmed_include"]
        + flow["eligibility_candidates_operational_analysis_group_corrected"]
        == flow["final_analytic_corpus"] == 2892
    )
    add("PRISMA flow arithmetic", flow_ok, flow)

    formula_hits = []
    for path in sorted(DATA.glob("*.csv")) + sorted(SOURCE.glob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row_number, row in enumerate(csv.reader(handle), start=1):
                for column_number, value in enumerate(row, start=1):
                    candidate = value.lstrip("\t\r\n ")
                    if is_formula_like_text(value):
                        formula_hits.append((path.name, row_number, column_number, candidate[:80]))
    add("No spreadsheet formula-injection strings", not formula_hits, formula_hits[:20])
    csv_safety_checks = regression_probes()
    add(
        "Live-output CSV formula neutralization passes adversarial probes",
        all(csv_safety_checks.values()),
        csv_safety_checks,
    )

    map_rows = read_csv(MAP_PATH)
    map_issues: list[object] = []
    map_contract = {}
    for row in map_rows:
        if set(row) != {"Submission_Path", "Repository_Path", "Bytes", "SHA256"}:
            map_issues.append({"schema": sorted(row)})
            continue
        map_contract[row["Submission_Path"]] = (row["Repository_Path"], int(row["Bytes"]), row["SHA256"])
        path = ROOT / row["Repository_Path"]
        if not path.is_file() or str(path.stat().st_size) != row["Bytes"] or sha256(path) != row["SHA256"]:
            map_issues.append(row["Repository_Path"])
    add(
        "Submission/repository map equals the author-maintained release contract",
        map_contract == EXPECTED_SUBMISSION_MAP and not map_issues,
        {"rows": len(map_rows), "issues": map_issues, "contract_equal": map_contract == EXPECTED_SUBMISSION_MAP},
    )
    unmapped_issues = {
        relative: {"expected": expected, "actual": sha256(ROOT / relative) if (ROOT / relative).is_file() else None}
        for relative, expected in EXPECTED_UNMAPPED_DATA_HASHES.items()
        if not (ROOT / relative).is_file() or sha256(ROOT / relative) != expected
    }
    add("Unmapped main-text exports match the locked release contract", not unmapped_issues, unmapped_issues)

    data11_metadata_issues = []
    for row in data11:
        source = data2_by.get(row["PMID"])
        if source is None:
            data11_metadata_issues.append((row["PMID"], "missing from Data 2"))
            continue
        for field in ("DOI", "First_Author", "Year", "Title", "Journal", "Publication_Type"):
            if row[field] != source[field]:
                data11_metadata_issues.append((row["PMID"], field))
    add("Data 11 shared bibliographic fields equal Data 2", not data11_metadata_issues, data11_metadata_issues[:20])

    figure3_builder = (ROOT / "scripts" / "build_main_figures.py").read_text(encoding="utf-8")
    figure3_phrases = (
        "Contextual implementation exemplars",
        "not assigned to a corpus-supported readiness tier",
        "Promising adjuncts",
        "Functional-urology and neurourology prediction",
        "ED/sexual-function prediction",
        "Exploratory or not ready for routine deployment",
        "Staged use cases: renal radiomics; retrieval-grounded guideline support.",
        "autonomous LLM advice",
        "Cross-cutting safety boundary (not separately staged)",
        "Sperm-retrieval prediction",
        "Laboratory and counselling",
        "supports pre-procedural counselling",
    )
    figure3_order = [
        figure3_builder.index("Supervised implementation-planning candidates"),
        figure3_builder.index("Near-implementation candidates"),
        figure3_builder.index("Promising adjuncts"),
        figure3_builder.index("Contextual implementation exemplars"),
        figure3_builder.index("Exploratory or not ready for routine deployment"),
    ]
    add("Figure 3 builder follows Table 2, separates contextual exemplars, and distinguishes counselling", all(phrase in figure3_builder for phrase in figure3_phrases) and figure3_order == sorted(figure3_order) and 'linestyle="--"' in figure3_builder and "Earlier-stage or contextual areas" not in figure3_builder and "not readiness-ranked" not in figure3_builder, {"phrases": {phrase: phrase in figure3_builder for phrase in figure3_phrases}, "order": figure3_order})
    tier_rows = {row["Tier"]: row["Use_cases"] for row in read_csv(DATA / "tiered_readiness_summary.csv")}
    add(
        "Tiered summary matches the Figure 3 classification contract",
        len(tier_rows) == 5
        and "functional urology and neurourology prediction" in tier_rows.get("Promising adjuncts", "")
        and "erectile dysfunction (ED) and sexual-function outcome prediction" in tier_rows.get("Promising adjuncts", "")
        and "Multidisciplinary team (MDT) and pathway triage" in tier_rows.get("Contextual implementation exemplars", "")
        and "ambient documentation support" in tier_rows.get("Contextual implementation exemplars", "")
        and "Renal radiomics" in tier_rows.get("Exploratory or not ready for routine deployment", "")
        and "retrieval-grounded guideline support" in tier_rows.get("Exploratory or not ready for routine deployment", "")
        and "autonomous large language model (LLM) advice" not in " ".join(tier_rows.values()),
        tier_rows,
    )

    figure2_builder = (ROOT / "scripts" / "build_main_figures.py").read_text(encoding="utf-8")
    add(
        "Figure 2 builder exposes the complete six-stage axis",
        "set_xticks([1, 2, 3, 4, 5, 6])" in figure2_builder
        and "ax.text(6.88" in figure2_builder,
        {
            "stage_6_tick": "set_xticks([1, 2, 3, 4, 5, 6])" in figure2_builder,
            "consequence_column_after_stage_6": "ax.text(6.88" in figure2_builder,
        },
    )

    readiness_by_task = {row["Clinical_Task"]: row for row in data8}
    corrected_readiness = {
        "Micro-ultrasound lesion localization": ("2", "0"),
        "Renal radiomics and renal-mass prediction": ("3", "1"),
        "Retrieval-grounded guideline support": ("1", "0"),
        "Prostate MRI reader assistance": ("5", "2"),
    }
    readiness_issues = {
        task: {
            "stage": readiness_by_task.get(task, {}).get("Highest_Validation_Stage"),
            "bubble": readiness_by_task.get(task, {}).get("Prospective_or_Validation_Study_Count"),
            "expected": expected,
        }
        for task, expected in corrected_readiness.items()
        if task not in readiness_by_task
        or (
            readiness_by_task[task]["Highest_Validation_Stage"],
            readiness_by_task[task]["Prospective_or_Validation_Study_Count"],
        ) != expected
    }
    add("Corrected readiness stages and prostate MRI bubble count are locked", not readiness_issues, readiness_issues)
    add(
        "Retrieval-grounded guideline support is exploratory only",
        "retrieval-grounded guideline support" not in tier_rows.get("Promising adjuncts", "").lower()
        and "retrieval-grounded guideline support" in tier_rows.get("Exploratory or not ready for routine deployment", "").lower(),
        tier_rows,
    )

    figure_root = ROOT / "figures"
    existing_figures = {path.name for path in figure_root.glob("*.png")} if figure_root.exists() else set()
    figure_issues = []
    figures_required = args.require_figures or args.portable_figures
    if figures_required and existing_figures != set(EXPECTED_FIGURES):
        figure_issues.append({"actual": sorted(existing_figures), "expected": sorted(EXPECTED_FIGURES)})
    if existing_figures:
        if existing_figures != set(EXPECTED_FIGURES):
            figure_issues.append({"actual": sorted(existing_figures), "expected": sorted(EXPECTED_FIGURES)})
        for name, (expected_dimensions, expected_hash) in EXPECTED_FIGURES.items():
            path = figure_root / name
            if not path.is_file():
                continue
            dimensions, png_issues = inspect_png(path)
            actual_hash = sha256(path)
            hash_mismatch = args.require_figures and actual_hash != expected_hash
            if png_issues or dimensions != expected_dimensions or hash_mismatch:
                figure_issues.append({"name": name, "dimensions": dimensions, "expected_dimensions": expected_dimensions, "sha256": actual_hash, "expected_sha256": expected_hash if args.require_figures else None, "png_issues": png_issues})
    add(
        "Generated figures satisfy the selected integrity mode",
        not figure_issues,
        {
            "mode": "reference-byte-exact" if args.require_figures else "portable-integrity-and-dimensions" if args.portable_figures else "validate-if-present",
            "required": figures_required,
            "present": sorted(existing_figures),
            "issues": figure_issues,
        },
    )

    public_text_paths = [ROOT / "README.md", ROOT / "REPRODUCIBILITY.md", ROOT / "CITATION.cff", ROOT / ".zenodo.json", ROOT / "CHANGELOG.md", ROOT / "RELEASE_NOTES_v1.3.0.md"]
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_text_paths)
    add(
        "Public metadata identifies v1.3.0 and the 2,892/1,270 release state",
        "v1.3.0" in public_text and "2,892" in public_text and "1,270" in public_text,
        {
            "v1.3.0": "v1.3.0" in public_text,
            "2,892": "2,892" in public_text,
            "1,270": "1,270" in public_text,
        },
    )
    operational_group_phrases = {
        "operational analysis groups": "operational analysis groups" in public_text.lower(),
        "initialized from recorded primary search stream": bool(
            re.search(r"initialized from the recorded primary search-stream assignment", public_text, re.I)
        ),
        "13 author-verified content mismatches": "13 author-verified content mismatches" in public_text.lower(),
        "Search_Query_Tags is authoritative": bool(
            re.search(r"Search_Query_Tags.{0,100}authoritative retrieval-provenance field", public_text, re.I | re.S)
        ),
        "not query-route shares": "not query-route shares" in public_text.lower()
        or "neither query-route shares" in public_text.lower(),
        "not a formal clinical taxonomy": "formal clinical taxonomy" in public_text.lower(),
        "historical assignment rule not retained": bool(
            re.search(
                r"(?:historical|original).{0,100}(?:assignment rule|single-group assignment).{0,100}(?:not retained|not reconstructible|could not be reconstructed)",
                public_text,
                re.I | re.S,
            )
        ),
        "sampling seed not retained": bool(
            re.search(r"(?:random|audit).{0,100}(?:seed|command).{0,100}(?:not retained|not reconstructible)", public_text, re.I | re.S)
        ),
    }
    misleading_group_terms = {
        term: term in public_text.lower()
        for term in (
            "retrieval_stratum",
            "retrieval stratum",
            "retrieval-stratum",
            "operational retrieval strata",
            "search-route provenance",
        )
    }
    add(
        "Public documentation states operational-analysis-group and sampling provenance limits",
        all(operational_group_phrases.values()) and not any(misleading_group_terms.values()),
        {
            "required_phrases": operational_group_phrases,
            "misleading_terms": misleading_group_terms,
        },
    )
    language_route_phrases = {
        "complete title-pattern scan": "complete title-pattern language-boundary scan" in public_text.lower(),
        "44 bracket-initial titles": "44 bracket-initial titles" in public_text.lower(),
        "four radionuclide titles retained": "four used radionuclide notation and remained eligible" in public_text.lower(),
        "40 PubMed XML candidates": bool(
            re.search(r"official PubMed XML.{0,160}(?:remaining|other) 40", public_text, re.I | re.S)
        ),
        "raw captures disclosed as author-held": "author-held quality-control artifacts" in public_text.lower()
        and "not part of the public archive" in public_text.lower(),
        "raw capture topology stated exactly": "one pubmed xml metadata capture and three pmc full-text xml capture files"
        in public_text.lower(),
    }
    unsupported_language_claims = {
        phrase: phrase.lower() in public_text.lower()
        for phrase in (
            "official PubMed XML language metadata were checked for all 2,932",
            "official PubMed XML language metadata were checked across the 2,932-record provisional corpus",
        )
    }
    add(
        "Public documentation reports the evidenced language-boundary route and snapshot availability",
        all(language_route_phrases.values()) and not any(unsupported_language_claims.values()),
        {
            "required": language_route_phrases,
            "unsupported_claims": unsupported_language_claims,
        },
    )
    current_files = [ROOT / name for name in REQUIRED_VERSION_DOI_FILES]
    current_text_by_file = {path.name: path.read_text(encoding="utf-8") for path in current_files}
    current_text = "\n".join(current_text_by_file.values())
    old_final_corpus_claim = bool(re.search(r"(?:final analytic (?:set|corpus).{0,30}3,352|3,352 published journal records)", current_text, re.I | re.S))
    add("Current release metadata contains no v1.2.2 final-corpus claim or old version DOI", not old_final_corpus_claim and "v1.2.2" not in current_text and "10.5281/zenodo.21127985" not in current_text, {"old_final_corpus_claim": old_final_corpus_claim, "old_version": "v1.2.2" in current_text, "old_doi": "10.5281/zenodo.21127985" in current_text})
    cff_text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    zenodo_metadata = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    add("Citation and Zenodo metadata version agreement", re.search(r'^version:\s*["\']?1\.3\.0["\']?$', cff_text, re.M) is not None and zenodo_metadata.get("version") == "v1.3.0", {"cff": bool(re.search(r'^version:\s*["\']?1\.3\.0["\']?$', cff_text, re.M)), "zenodo": zenodo_metadata.get("version")})
    fake_doi = "10.5281/zenodo.99999999"
    partial_propagation_probe = evaluate_version_doi_gate(
        fake_doi,
        {name: fake_doi if name == "README.md" else "" for name in REQUIRED_VERSION_DOI_FILES},
        "",
        {},
    )
    add(
        "Version DOI gate rejects partial metadata propagation",
        not partial_propagation_probe["passed"],
        partial_propagation_probe,
    )
    url_typed_doi_probe = evaluate_version_doi_gate(
        fake_doi,
        {name: fake_doi for name in REQUIRED_VERSION_DOI_FILES},
        f'identifiers:\n  - type: url\n    value: "{fake_doi}"\n',
        {"doi": fake_doi, "related_identifiers": []},
    )
    add(
        "Version DOI gate rejects a URL-typed CFF lookalike",
        not url_typed_doi_probe["passed"],
        url_typed_doi_probe,
    )
    related_only_doi_probe = evaluate_version_doi_gate(
        fake_doi,
        {name: fake_doi for name in REQUIRED_VERSION_DOI_FILES},
        f'identifiers:\n  - type: doi\n    value: "{fake_doi}"\n',
        {
            "related_identifiers": [
                {"identifier": fake_doi, "relation": "isSupplementTo"}
            ]
        },
    )
    add(
        "Version DOI gate requires the top-level Zenodo DOI",
        not related_only_doi_probe["passed"],
        related_only_doi_probe,
    )
    embedded_cff_doi_probe = evaluate_version_doi_gate(
        fake_doi,
        {name: fake_doi for name in REQUIRED_VERSION_DOI_FILES},
        f'identifiers:\n  - type: doi\n    value: "not-a-doi {fake_doi} trailing-text"\n',
        {"doi": fake_doi, "related_identifiers": []},
    )
    add(
        "Version DOI gate rejects embedded or trailing CFF DOI text",
        not embedded_cff_doi_probe["passed"],
        embedded_cff_doi_probe,
    )
    code_license_probe = b"SPDX-License-Identifier: MIT\nMIT License regression fixture.\n"
    data_license_probe = b"SPDX-License-Identifier: CC-BY-4.0\nCC BY 4.0 regression fixture.\n"
    synchronized_license_evidence = build_license_file_evidence(
        {"LICENSE-CODE": code_license_probe, "LICENSE-DATA": data_license_probe}
    )
    license_profile_probe = {
        "name": "regression-only",
        "code_spdx": "MIT",
        "data_spdx": "CC-BY-4.0",
        "zenodo_license": "cc-by-4.0",
        "license_files": {
            "LICENSE-CODE": {
                "spdx": "MIT",
                "sha256": hashlib.sha256(code_license_probe).hexdigest(),
            },
            "LICENSE-DATA": {
                "spdx": "CC-BY-4.0",
                "sha256": hashlib.sha256(data_license_probe).hexdigest(),
            },
        },
    }
    synchronized_license_probe = evaluate_license_gate(
        license_profile_probe,
        synchronized_license_evidence,
        "## License\n\nCode: MIT. Data: CC-BY-4.0.\n",
        "license:\n  - MIT\n  - CC-BY-4.0\n",
        {"license": "cc-by-4.0"},
    )
    contradictory_code_probe = b"SPDX-License-Identifier: GPL-3.0-only\nContradictory fixture.\n"
    contradictory_profile_probe = json.loads(json.dumps(license_profile_probe))
    contradictory_profile_probe["license_files"]["LICENSE-CODE"]["sha256"] = (
        hashlib.sha256(contradictory_code_probe).hexdigest()
    )
    contradictory_license_probe = evaluate_license_gate(
        contradictory_profile_probe,
        build_license_file_evidence(
            {"LICENSE-CODE": contradictory_code_probe, "LICENSE-DATA": data_license_probe}
        ),
        "## License\n\nCode: MIT. Data: CC-BY-4.0.\n",
        "license:\n  - MIT\n  - CC-BY-4.0\n",
        {"license": "cc-by-4.0"},
    )
    add(
        "License gate accepts only a synchronized approved-profile mock",
        synchronized_license_probe["passed"] and not contradictory_license_probe["passed"],
        {
            "synchronized": synchronized_license_probe,
            "contradictory": contradictory_license_probe,
        },
    )

    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    protective_ignores = {".env", ".env.*", ".secrets", ".secrets.*", "harvest_runs/", "*.run.json", "*.raw.jsonl"}
    actual_ignores = {
        line.strip()
        for line in gitignore_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    add(
        "Sensitive/runtime artifacts are excluded from release discovery",
        protective_ignores <= actual_ignores,
        {"required": sorted(protective_ignores), "missing": sorted(protective_ignores - actual_ignores)},
    )
    screening_text = (ROOT / "scripts" / "ai_screening.py").read_text(encoding="utf-8")
    harvest_text = (ROOT / "scripts" / "pubmed_harvest.py").read_text(encoding="utf-8")
    add(
        "Screening script has no nonexistent analysis-script handoff",
        "screening_analysis.py" not in screening_text
        and "Historical PRISMA decisions are not regenerated by this script." in screening_text,
        {"obsolete_reference": "screening_analysis.py" in screening_text},
    )
    add(
        "Live-output scripts preserve canonical raw JSONL and emit spreadsheet-safe CSV views",
        all(
            token in script_text
            for script_text in (screening_text, harvest_text)
            for token in ("spreadsheet_safe_dataframe", "raw.jsonl")
        )
        and "load_screening_input" in screening_text
        and "--allow-csv-only-input" in screening_text,
        {
            "screening_has_safety_helper": "spreadsheet_safe_dataframe" in screening_text,
            "screening_has_raw_jsonl": "raw.jsonl" in screening_text,
            "harvest_has_safety_helper": "spreadsheet_safe_dataframe" in harvest_text,
            "harvest_has_raw_jsonl": "raw.jsonl" in harvest_text,
            "screening_prefers_raw_companion": "load_screening_input" in screening_text,
            "csv_only_requires_override": "--allow-csv-only-input" in screening_text,
        },
    )
    add(
        "Citation metadata does not predeclare a release date",
        re.search(r"^date-released\s*:", cff_text, re.M) is None,
        {"date_released_present": re.search(r"^date-released\s*:", cff_text, re.M) is not None},
    )

    forbidden_artifacts = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.name == ".DS_Store"
        or path.name.startswith("._")
        or any(part in {"__pycache__", ".pytest_cache"} for part in path.relative_to(ROOT).parts)
    ]
    add("No macOS residue or cache artifacts", not forbidden_artifacts, forbidden_artifacts)

    expected_doi = os.environ.get("TAU_EXPECTED_ZENODO_DOI", "").strip()
    doi_gate = evaluate_version_doi_gate(expected_doi, current_text_by_file, cff_text, zenodo_metadata)
    license_paths = sorted(
        path
        for path in ROOT.rglob("*")
        if (path.is_file() or path.is_symlink())
        and (
            path.name.upper().startswith("LICENSE")
            or path.name.upper().startswith("COPYING")
        )
    )
    repository_root_resolved = ROOT.resolve()
    license_integrity = {
        str(path.relative_to(ROOT)): {
            "regular_file_no_symlink": path.is_file() and not path.is_symlink(),
            "resolved_within_repository": path_is_within(
                path.resolve(strict=False), repository_root_resolved
            ),
        }
        for path in license_paths
    }
    license_file_evidence = build_license_file_evidence(
        {
            str(path.relative_to(ROOT)): (
                path.read_bytes()
                if license_integrity[str(path.relative_to(ROOT))]["regular_file_no_symlink"]
                and license_integrity[str(path.relative_to(ROOT))]["resolved_within_repository"]
                else b""
            )
            for path in license_paths
        },
        license_integrity,
    )
    expected_license_profile_raw = os.environ.get("TAU_EXPECTED_LICENSE_PROFILE", "").strip()
    try:
        expected_license_profile = (
            json.loads(expected_license_profile_raw) if expected_license_profile_raw else None
        )
    except json.JSONDecodeError:
        expected_license_profile = None
    license_gate = evaluate_license_gate(
        expected_license_profile,
        license_file_evidence,
        current_text_by_file["README.md"],
        cff_text,
        zenodo_metadata,
    )
    external_gate_passed = bool(doi_gate["passed"] and license_gate["passed"])
    pending_statuses = [
        gate["status"]
        for gate in (doi_gate, license_gate)
        if not gate["passed"]
    ]
    external_gate = {
        "passed": external_gate_passed,
        "status": "READY" if external_gate_passed else " + ".join(pending_statuses),
        "expected_version_doi": expected_doi or None,
        "cited_zenodo_dois": zenodo_dois(current_text),
        "doi_gate": doi_gate,
        "license_gate": license_gate,
        "remote_actions_performed": False,
    }
    local_passed = all(check["passed"] for check in checks)
    report = {
        "local_release_passed": local_passed,
        "publication_ready": local_passed and external_gate["passed"],
        "external_release_gate": external_gate,
        "checks_passed": sum(check["passed"] for check in checks),
        "checks_total": len(checks),
        "failed_checks": [check for check in checks if not check["passed"]],
        "checks": checks,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if local_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
