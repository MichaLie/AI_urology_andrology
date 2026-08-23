#!/usr/bin/env python3
"""
PubMed harvest pipeline for AI in urology and andrology.

Runs prespecified PubMed Boolean queries via NCBI Entrez, pulls metadata,
de-duplicates records, optionally cross-references an existing reference list,
and writes a screening-ready CSV.
"""

import argparse
import csv
import hashlib
import json
import platform
import time
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

# Fix macOS SSL certificate issue
try:
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
except ImportError:
    pass

from Bio import Entrez, Medline
import pandas as pd

from csv_safety import spreadsheet_safe_dataframe

# ── Configuration ──────────────────────────────────────────────────────────

DATE_FROM = "2020/01/01"
DATE_TO = "2026/04/04"
QUERY_PAGE_SIZE = 500

# Domain-specific search queries matching the Methods section
DOMAIN_QUERIES = {
    "prostate_mri": (
        '("artificial intelligence" OR "machine learning" OR "deep learning" '
        'OR "neural network" OR "computer vision" OR "radiomics") '
        'AND ("prostate MRI" OR "prostate magnetic resonance imaging" '
        'OR "prostate mpMRI" OR "PI-RADS")'
    ),
    "prostate_pathology": (
        '("artificial intelligence" OR "machine learning" OR "deep learning" '
        'OR "neural network") AND ("prostate pathology" OR "prostate biopsy" '
        'OR "Gleason grading" OR "prostate histopathology" OR "digital pathology"'
        ' OR "whole slide image") AND prostate'
    ),
    "stimulated_raman_histology": (
        '("stimulated Raman histology" OR "stimulated Raman scattering") '
        'AND prostate'
    ),
    "bladder_cystoscopy": (
        '("artificial intelligence" OR "deep learning" OR "machine learning" '
        'OR "computer vision") AND ("cystoscopy" OR "bladder cancer" '
        'OR "urothelial carcinoma" OR "TURBT")'
    ),
    "psma_pet": (
        '("artificial intelligence" OR "deep learning" OR "machine learning" '
        'OR "radiomics") AND ("PSMA PET" OR "PSMA-PET" OR "68Ga-PSMA" '
        'OR "18F-PSMA" OR "DCFPyL")'
    ),
    "renal_kidney": (
        '("artificial intelligence" OR "machine learning" OR "deep learning" '
        'OR "radiomics") AND ("renal cell carcinoma" OR "kidney cancer" '
        'OR "renal mass" OR "nephrometry")'
    ),
    "micro_ultrasound": (
        '("artificial intelligence" OR "deep learning") '
        'AND ("micro-ultrasound" OR "micro ultrasound" OR "ExactVu")'
    ),
    "uti_triage": (
        '("artificial intelligence" OR "machine learning") '
        'AND ("urinary tract infection" OR "urine culture" '
        'OR "antimicrobial stewardship") AND urinary'
    ),
    "functional_urology": (
        '("artificial intelligence" OR "machine learning" OR "deep learning") '
        'AND ("lower urinary tract symptoms" OR "overactive bladder" '
        'OR "functional urology" OR "neurourology" OR "urodynamics" '
        'OR "detrusor" OR "neurogenic bladder")'
    ),
    "surgical_video": (
        '("artificial intelligence" OR "deep learning" OR "computer vision") '
        'AND ("robotic prostatectomy" OR "surgical video" OR "robotic surgery" '
        'OR "surgical skills" OR "surgical training") AND urology'
    ),
    "semen_analysis": (
        '("artificial intelligence" OR "machine learning" OR "deep learning") '
        'AND ("semen analysis" OR "sperm morphology" OR "sperm motility" '
        'OR "sperm selection" OR "ICSI")'
    ),
    "male_infertility": (
        '("artificial intelligence" OR "machine learning") '
        'AND ("male infertility" OR "varicocele" OR "azoospermia" '
        'OR "testicular sperm")'
    ),
    "erectile_dysfunction": (
        '("artificial intelligence" OR "machine learning") '
        'AND ("erectile dysfunction" OR "sexual function" '
        'OR "sexual medicine" OR "penile")'
    ),
    "andrology_broad": (
        '("artificial intelligence" OR "machine learning") AND andrology'
    ),
    "llm_urology": (
        '("large language model" OR "ChatGPT" OR "GPT-4" OR "generative AI" '
        'OR "DeepSeek") AND ("urology" OR "prostate cancer" OR "bladder cancer" '
        'OR "kidney cancer" OR "erectile dysfunction" OR "infertility")'
    ),
    "rag_scribes": (
        '("retrieval-augmented generation" OR "RAG" OR "ambient scribe" '
        'OR "AI documentation" OR "AI scribe") AND ("urology" OR "medicine")'
    ),
    "reporting_guidelines": (
        '("STREAM-URO" OR "TRIPOD+AI" OR "TRIPOD-AI" OR "PROBAST+AI" '
        'OR "PROBAST-AI" OR "STARD-AI" OR "QUADAS-AI" OR "DECIDE-AI" '
        'OR "SPIRIT-AI" OR "CONSORT-AI" OR "CLAIM" OR "FUTURE-AI") '
        'AND "artificial intelligence"'
    ),
    "ai_urology_broad": (
        '("artificial intelligence" OR "machine learning" OR "deep learning") '
        'AND urology AND (review[pt] OR systematic review[pt] OR meta-analysis[pt])'
    ),
    "ai_urology_implementation": (
        '("artificial intelligence" OR "machine learning") AND urology '
        'AND ("implementation" OR "deployment" OR "clinical practice" '
        'OR "real-world")'
    ),
    "ai_urology_ethics": (
        '("artificial intelligence") AND urology '
        'AND ("ethics" OR "bias" OR "fairness" OR "equity" OR "regulation")'
    ),
}


def search_pubmed(query: str, email: str, page_size: int = QUERY_PAGE_SIZE) -> tuple[list[str], int]:
    """Run a paginated PubMed search and return all matching PMIDs plus total count."""
    Entrez.email = email
    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        datetype="pdat",
        mindate=DATE_FROM,
        maxdate=DATE_TO,
        retmax=0,
        sort="relevance",
    )
    record = Entrez.read(handle)
    handle.close()
    count = int(record["Count"])
    pmids: list[str] = []
    for start in range(0, count, page_size):
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            datetype="pdat",
            mindate=DATE_FROM,
            maxdate=DATE_TO,
            retmax=page_size,
            retstart=start,
            sort="relevance",
        )
        page = Entrez.read(handle)
        handle.close()
        pmids.extend(page["IdList"])
        if start + page_size < count:
            time.sleep(0.2)
    pmids = sorted(set(pmids), key=int)
    return pmids, count


def fetch_metadata(pmids: list[str], email: str) -> list[dict]:
    """Fetch article metadata for a list of PMIDs."""
    if not pmids:
        return []

    Entrez.email = email
    records = []

    # Fetch in batches of 200
    for i in range(0, len(pmids), 200):
        batch = pmids[i : i + 200]
        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(batch),
            rettype="medline",
            retmode="text",
        )
        batch_records = list(Medline.parse(handle))
        handle.close()
        records.extend(batch_records)
        if i + 200 < len(pmids):
            time.sleep(0.4)  # Rate limiting

    return records


def parse_record(record: dict) -> dict:
    """Extract relevant fields from a Medline record."""
    # Get DOI from article identifiers
    doi = ""
    aid_list = record.get("AID", [])
    for aid in aid_list:
        if "[doi]" in aid:
            doi = aid.replace(" [doi]", "")
            break

    # Get first author
    authors = record.get("AU", [])
    first_author = authors[0] if authors else ""

    return {
        "PMID": record.get("PMID", ""),
        "DOI": doi,
        "First_Author": first_author,
        "Authors_All": "; ".join(authors),
        "Year": record.get("DP", "")[:4],
        "Title": record.get("TI", ""),
        "Abstract": record.get("AB", ""),
        "Journal": record.get("JT", ""),
        "Journal_Abbrev": record.get("TA", ""),
        "Publication_Type": "; ".join(record.get("PT", [])),
        "MeSH_Terms": "; ".join(record.get("MH", [])),
    }


def load_existing_references(csv_path: str) -> dict:
    """Load an optional prior reference list and return DOI -> info mapping."""
    existing = {}
    try:
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            doi = str(row.get("DOI", "")).strip().lower()
            if doi and doi != "nan":
                existing[doi] = {
                    "filename": str(row.get("Filename", "")),
                    "in_reference_set": str(row.get("In_Reference_Set", "No")),
                    "pdf_available": str(row.get("PDF_Available", "No")),
                }
    except FileNotFoundError:
        print(f"  Warning: {csv_path} not found, skipping cross-reference")
    return existing


def main():
    parser = argparse.ArgumentParser(
        description="Harvest PubMed records for AI in Urology scoping review"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email for NCBI Entrez (required by NCBI policy)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent.parent / "harvest_runs"),
        help="Parent directory for a new timestamped, atomic harvest snapshot",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=QUERY_PAGE_SIZE,
        help="PubMed pagination size per request (default: 500)",
    )
    args = parser.parse_args()

    retrieved_at = datetime.now(timezone.utc)
    run_id = retrieved_at.strftime("pubmed_%Y%m%dT%H%M%S%fZ")
    output_parent = Path(args.output_dir).resolve()
    output_parent.mkdir(parents=True, exist_ok=True)
    temporary_dir = output_parent / f".{run_id}.tmp"
    final_dir = output_parent / run_id
    temporary_dir.mkdir()
    existing_refs_path = output_parent / "references_list.csv"
    output_csv = temporary_dir / "screening_master.csv"
    raw_jsonl_path = temporary_dir / "screening_master.raw.jsonl"
    log_path = temporary_dir / "harvest_log.txt"
    manifest_path = temporary_dir / "harvest_manifest.json"

    print("=" * 70)
    print("PubMed Harvest Pipeline — AI in Urology and Andrology")
    print("=" * 70)
    print(f"Date range: {DATE_FROM} to {DATE_TO}")
    print(f"Email: {args.email}")
    print(f"Domains: {len(DOMAIN_QUERIES)}")
    print(f"Pagination: uncapped retrieval in pages of {args.page_size}")
    print(f"Output snapshot: {final_dir}")
    print()

    # Load existing references for cross-referencing
    print("Loading existing references...")
    existing_refs = load_existing_references(str(existing_refs_path))
    print(f"  Found {len(existing_refs)} existing references with DOIs")
    print()

    # Run all domain searches
    all_pmids = set()
    pmid_domains = defaultdict(set)  # PMID -> set of domains
    domain_stats = {}

    for domain, query in DOMAIN_QUERIES.items():
        print(f"Searching [{domain}]...")
        try:
            pmids, total_count = search_pubmed(query, args.email, page_size=args.page_size)
            domain_stats[domain] = {
                "status": "COMPLETE",
                "query": query,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "total_count": total_count,
                "retrieved": len(pmids),
                "pmids": pmids,
            }
            for pmid in pmids:
                pmid_domains[pmid].add(domain)
            all_pmids.update(pmids)
            print(f"  Total hits: {total_count}, Retrieved: {len(pmids)}")
            time.sleep(0.4)  # Rate limiting between searches
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            domain_stats[domain] = {
                "status": "FAILED",
                "query": query,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "error": str(e),
                "total_count": None,
                "retrieved": 0,
                "pmids": [],
            }

    failed_queries = [domain for domain, stats in domain_stats.items() if stats["status"] != "COMPLETE"]
    if failed_queries:
        manifest_path.write_text(json.dumps({
            "status": "FAILED_INCOMPLETE_QUERY_SET",
            "retrieved_at_utc": retrieved_at.isoformat(),
            "date_from": DATE_FROM,
            "date_to": DATE_TO,
            "failed_queries": failed_queries,
            "queries": domain_stats,
        }, indent=2) + "\n", encoding="utf-8")
        failed_dir = output_parent / f"{run_id}-FAILED"
        os.replace(temporary_dir, failed_dir)
        print(f"Harvest failed; diagnostic snapshot: {failed_dir}", file=sys.stderr)
        return 1

    print()
    print(f"Total unique PMIDs across all domains: {len(all_pmids)}")
    print()

    # Fetch metadata for all unique PMIDs
    print("Fetching metadata for all records...")
    pmid_list = sorted(all_pmids)
    all_records = fetch_metadata(pmid_list, args.email)
    print(f"  Fetched metadata for {len(all_records)} records")
    print()
    fetched_pmids = {record.get("PMID", "") for record in all_records}
    missing_metadata = sorted(set(pmid_list) - fetched_pmids, key=int)
    if missing_metadata:
        manifest_path.write_text(json.dumps({
            "status": "FAILED_INCOMPLETE_METADATA",
            "retrieved_at_utc": retrieved_at.isoformat(),
            "missing_pmids": missing_metadata,
            "queries": domain_stats,
        }, indent=2) + "\n", encoding="utf-8")
        failed_dir = output_parent / f"{run_id}-FAILED"
        os.replace(temporary_dir, failed_dir)
        print(f"Metadata retrieval was incomplete; diagnostic snapshot: {failed_dir}", file=sys.stderr)
        return 1

    # Parse and enrich records
    print("Parsing and enriching records...")
    rows = []
    for record in all_records:
        parsed = parse_record(record)
        pmid = parsed["PMID"]

        # Add domain info
        domains = pmid_domains.get(pmid, set())
        parsed["Domain_Searches"] = "; ".join(sorted(domains))
        parsed["Num_Domain_Hits"] = len(domains)

        # Cross-reference with existing collection
        doi_lower = parsed["DOI"].strip().lower()
        if doi_lower in existing_refs:
            ref_info = existing_refs[doi_lower]
            parsed["Already_Collected"] = "Yes"
            parsed["Already_In_Reference_Set"] = ref_info["in_reference_set"]
            parsed["Existing_Filename"] = ref_info["filename"]
        else:
            parsed["Already_Collected"] = "No"
            parsed["Already_In_Reference_Set"] = "No"
            parsed["Existing_Filename"] = ""

        # Screening columns (to be filled by AI/human)
        parsed["AI_Decision"] = ""
        parsed["AI_Reasoning"] = ""
        parsed["AI_Confidence"] = ""
        parsed["Human_Decision"] = ""
        parsed["Human_Reasoning"] = ""
        parsed["Final_Decision"] = ""
        parsed["Exclusion_Reason"] = ""

        rows.append(parsed)

    # Sort: prior-reference records first, then already-collected records, then by domain hits desc.
    rows.sort(
        key=lambda r: (
            r["Already_In_Reference_Set"] != "No",
            r["Already_Collected"] == "Yes",
            r["Num_Domain_Hits"],
        ),
        reverse=True,
    )

    # Write master CSV
    if rows:
        fieldnames = [
            "PMID", "DOI", "First_Author", "Year", "Title", "Abstract",
            "Journal", "Journal_Abbrev", "Publication_Type", "MeSH_Terms",
            "Authors_All", "Domain_Searches", "Num_Domain_Hits",
            "Already_Collected", "Already_In_Reference_Set", "Existing_Filename",
            "AI_Decision", "AI_Reasoning", "AI_Confidence",
            "Human_Decision", "Human_Reasoning",
            "Final_Decision", "Exclusion_Reason",
        ]
        df_out = pd.DataFrame(rows, columns=fieldnames)
        # JSONL is the canonical, unmodified provenance record. The CSV is a
        # spreadsheet-facing view with formula-like text cells neutralized.
        df_out.to_json(raw_jsonl_path, orient="records", lines=True, force_ascii=False)
        safe_df, csv_safety = spreadsheet_safe_dataframe(df_out)
        safe_df.to_csv(output_csv, index=False, quoting=csv.QUOTE_ALL)
        print(f"Written {len(rows)} records to {output_csv}")
        print(f"Canonical raw records written to {raw_jsonl_path}")
        print(f"Spreadsheet-safety escapes applied: {csv_safety['escaped_cells']}")
    else:
        print("WARNING: No records found!")

    # Write harvest log
    with open(log_path, "w") as f:
        f.write("PubMed Harvest Log\n")
        f.write(f"Retrieved at UTC: {retrieved_at.isoformat()}\n")
        f.write(f"Date range: {DATE_FROM} to {DATE_TO}\n")
        f.write(f"Total unique PMIDs: {len(all_pmids)}\n")
        f.write(f"Metadata fetched: {len(all_records)}\n\n")
        f.write("Domain-by-domain results:\n")
        f.write("-" * 60 + "\n")
        total_hits = 0
        for domain, stats in domain_stats.items():
            f.write(
                f"  {domain:30s}  hits={stats['total_count']:6d}  "
                f"retrieved={stats['retrieved']:4d}\n"
            )
            total_hits += stats['total_count']
        f.write("-" * 60 + "\n")
        f.write(f"  {'TOTAL (before dedup)':30s}  hits={total_hits:6d}\n")
        f.write(f"  {'UNIQUE PMIDs':30s}       ={len(all_pmids):6d}\n\n")

        # Cross-reference stats
        already_collected = sum(1 for r in rows if r["Already_Collected"] == "Yes")
        already_in_reference_set = sum(1 for r in rows if r["Already_In_Reference_Set"] != "No")
        f.write(f"Cross-reference with existing collection:\n")
        f.write(f"  Already collected: {already_collected}\n")
        f.write(f"  Already in prior reference set: {already_in_reference_set}\n")
        f.write(f"  New (not in collection): {len(rows) - already_collected}\n")

    try:
        import Bio
        import certifi
        dependency_versions = {"biopython": Bio.__version__, "pandas": pd.__version__, "certifi": certifi.__version__}
    except Exception:
        dependency_versions = {"biopython": "unknown", "pandas": pd.__version__, "certifi": "unknown"}
    manifest = {
        "status": "COMPLETE",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "date_from": DATE_FROM,
        "date_to": DATE_TO,
        "page_size": args.page_size,
        "total_query_hits": sum(int(stats["total_count"]) for stats in domain_stats.values()),
        "unique_pmids": len(all_pmids),
        "metadata_rows": len(rows),
        "queries": domain_stats,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "dependencies": dependency_versions,
        },
        "outputs": {
            "screening_master.csv": {"sha256": hashlib.sha256(output_csv.read_bytes()).hexdigest(), "rows": len(rows)},
            "screening_master.raw.jsonl": {"sha256": hashlib.sha256(raw_jsonl_path.read_bytes()).hexdigest(), "rows": len(rows)},
            "harvest_log.txt": {"sha256": hashlib.sha256(log_path.read_bytes()).hexdigest()},
        },
        "csv_safety": csv_safety,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary_dir, final_dir)

    print(f"Written harvest log to {log_path}")

    # Summary
    already_collected = sum(1 for r in rows if r["Already_Collected"] == "Yes")
    already_in_reference_set = sum(1 for r in rows if r["Already_In_Reference_Set"] != "No")
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Domains searched:          {len(DOMAIN_QUERIES)}")
    print(f"  Unique records:            {len(rows)}")
    print(f"  Already in collection:     {already_collected}")
    print(f"  Already in reference set:  {already_in_reference_set}")
    print(f"  New records to screen:     {len(rows) - already_collected}")
    print()
    print(f"Output: {final_dir / output_csv.name}")
    print(f"Log:    {final_dir / log_path.name}")
    print()
    print("Next step: Run ai_screening.py to perform AI-assisted screening")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
