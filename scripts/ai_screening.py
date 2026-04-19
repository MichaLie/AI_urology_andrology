#!/usr/bin/env python3
"""
AI-assisted screening for AI in urology and andrology.

Uses an LLM backend to screen title and abstract records against predefined
inclusion and exclusion criteria.
"""

import argparse
import csv
import json
import subprocess
import tempfile
import time
import sys
import os
from pathlib import Path

import pandas as pd
from anthropic import Anthropic

# ── Screening criteria (from the Methods section) ──────────────────────────

SCREENING_PROMPT = """You are an expert systematic reviewer screening records for a critical scoping review of artificial intelligence in urology and andrology.

## REVIEW SCOPE
The review covers AI applications in:
- Urological oncology (prostate, bladder, kidney cancer)
- Benign/functional urology (UTI, LUTS, OAB, neurourology, urodynamics)
- Operative urology (robotic surgery, surgical video analytics)
- Andrology and male sexual/reproductive health (semen analysis, male infertility, varicocele, erectile dysfunction, sexual medicine)
- Large language models / generative AI as applied to urology
- AI governance, reporting standards, and regulation relevant to urological AI

The review EXCLUDES:
- Urolithiasis / stone disease (covered by separate dedicated reviews)
- Studies outside urology or male sexual/reproductive health
- Pure engineering/computer science papers without a clinical use context
- Conference abstracts without sufficient clinical detail

## INCLUSION CRITERIA (include if ANY of these apply)
1. External or multicentre validation of an AI tool for a urological task
2. Comparison of AI against clinicians or standard care in urology
3. Prospective or "silent" clinical testing of AI in a urological setting
4. Human-AI interaction studies in urology
5. Workflow implementation of AI in urology
6. Patient-level or economic implications of urological AI
7. Systematic review or meta-analysis of AI in a urological domain
8. Reporting guideline, governance framework, or regulatory document relevant to AI in medicine/urology
9. Study addressing AI ethics, bias, fairness, or equity in urology
10. Study on LLMs/chatbots applied to urological patient education, clinical decision support, or documentation
11. Broad AI-in-urology review that provides important context or is widely cited

## EXCLUSION CRITERIA (exclude if ANY of these apply)
E1. Not about urology, andrology, or male sexual/reproductive health
E2. About urolithiasis/stone disease (excluded from this review's scope)
E3. Purely technical/engineering paper with no clinical context or intended clinical use
E4. Conference abstract only, without sufficient methodological detail
E5. Case report or case series with fewer than 10 patients and no AI validation
E6. Study predates 2020 AND is not foundational for a currently deployed system
E7. Duplicate or near-duplicate of another included study
E8. Non-English full text (if determinable from abstract)
E9. Performance metrics reported without enough information to understand the clinical task, comparator, or validation setting

## YOUR TASK
For each record, classify as:
- **INCLUDE**: Meets at least one inclusion criterion and no exclusion criteria
- **EXCLUDE**: Meets at least one exclusion criterion
- **UNCERTAIN**: Could go either way; needs human review

Respond in exactly this JSON format for each record:
{
  "decision": "INCLUDE" or "EXCLUDE" or "UNCERTAIN",
  "confidence": "high" or "medium" or "low",
  "inclusion_criteria_met": [list of criterion numbers, e.g. [1, 3]],
  "exclusion_criteria_met": [list of criterion codes, e.g. ["E1"]],
  "reasoning": "Brief 1-2 sentence justification"
}
"""

BATCH_USER_TEMPLATE = """Screen the following {n} records. Return a JSON array with one object per record, in the same order. Each object must have the fields: decision, confidence, inclusion_criteria_met, exclusion_criteria_met, reasoning.

{records}

Return ONLY the JSON array, no other text."""


def format_record_for_screening(row: pd.Series, idx: int) -> str:
    """Format a single record for the screening prompt."""
    abstract = str(row.get("Abstract", "")) if pd.notna(row.get("Abstract")) else "No abstract available"
    if abstract == "nan":
        abstract = "No abstract available"

    return (
        f"--- RECORD {idx} ---\n"
        f"PMID: {row['PMID']}\n"
        f"Title: {row['Title']}\n"
        f"Journal: {row.get('Journal', 'Unknown')}\n"
        f"Year: {row.get('Year', 'Unknown')}\n"
        f"Publication Type: {row.get('Publication_Type', 'Unknown')}\n"
        f"Domain Searches: {row.get('Domain_Searches', '')}\n"
        f"Abstract: {abstract}\n"
    )


def screen_batch(client: Anthropic, records_text: str, n: int) -> list[dict]:
    """Send a batch of records to Claude for screening."""
    user_msg = BATCH_USER_TEMPLATE.format(n=n, records=records_text)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SCREENING_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    # Parse JSON response
    text = response.content[0].text.strip()
    # Handle potential markdown code blocks
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        results = json.loads(text)
        if isinstance(results, list):
            return results
        else:
            return [results]
    except json.JSONDecodeError:
        print(f"  WARNING: Failed to parse JSON response, retrying...")
        # Try to extract JSON from the text
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return [{"decision": "UNCERTAIN", "confidence": "low",
                 "inclusion_criteria_met": [], "exclusion_criteria_met": [],
                 "reasoning": "Failed to parse AI response"} for _ in range(n)]


def screen_batch_codex(records_text: str, n: int) -> list[dict]:
    """Send a batch of records to the local Codex CLI for screening."""
    prompt = (
        f"{SCREENING_PROMPT}\n\n"
        f"{BATCH_USER_TEMPLATE.format(n=n, records=records_text)}"
    )

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as handle:
        output_file = handle.name

    try:
        result = subprocess.run(
            [
                "codex",
                "exec",
                prompt,
                "--skip-git-repo-check",
                "-C",
                str(Path(__file__).parent),
                "-s",
                "read-only",
                "-o",
                output_file,
                "--color",
                "never",
            ],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "codex exec failed")

        text = Path(output_file).read_text(encoding="utf-8").strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        results = json.loads(text)
        if isinstance(results, dict):
            results = [results]
        return results
    except Exception as exc:
        return [{"decision": "UNCERTAIN", "confidence": "low",
                 "inclusion_criteria_met": [], "exclusion_criteria_met": [],
                 "reasoning": f"Failed codex screening: {str(exc)[:120]}"} for _ in range(n)]
    finally:
        try:
            os.unlink(output_file)
        except OSError:
            pass


def normalize_decision(value: str) -> str:
    value = (value or "").strip().upper()
    if value in {"INCLUDE", "EXCLUDE", "UNCERTAIN"}:
        return value
    return "UNCERTAIN"


def normalize_confidence(value: str) -> str:
    value = (value or "").strip().lower()
    if value in {"high", "medium", "low"}:
        return value
    return "low"


def main():
    parser = argparse.ArgumentParser(
        description="AI-assisted screening of PubMed records"
    )
    parser.add_argument("--batch-size", type=int, default=15,
                        help="Records per API call (default: 15)")
    parser.add_argument("--max-records", type=int, default=0,
                        help="Max records to screen (0 = all)")
    parser.add_argument("--input", default="../data/screening_master.csv",
                        help="Input CSV from pubmed_harvest.py")
    parser.add_argument("--output", default="",
                        help="Output CSV path (default: overwrite the input CSV)")
    parser.add_argument("--backend", choices=["anthropic", "codex"], default="anthropic",
                        help="Screening backend to use")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = Path(__file__).parent / input_path

    output_path = Path(args.output) if args.output else input_path
    if not output_path.is_absolute():
        output_path = Path(__file__).parent / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("AI-Assisted Screening — AI in Urology and Andrology")
    print("=" * 70)

    # Load data
    df = pd.read_csv(input_path)
    for col in [
        "AI_Decision",
        "AI_Reasoning",
        "AI_Confidence",
        "Human_Decision",
        "Human_Reasoning",
        "Final_Decision",
        "Exclusion_Reason",
    ]:
        if col in df.columns:
            df[col] = df[col].astype("object")
    total = len(df)
    print(f"Loaded {total} records from {input_path}")

    # Find records that haven't been screened yet
    unscreened = df[df["AI_Decision"].isna() | (df["AI_Decision"] == "")]
    print(f"Already screened: {total - len(unscreened)}")
    print(f"Remaining to screen: {len(unscreened)}")

    if len(unscreened) == 0:
        print("All records already screened!")
        return

    # Limit if requested
    if args.max_records > 0:
        unscreened = unscreened.head(args.max_records)
        print(f"Processing first {len(unscreened)} unscreened records")

    if args.backend == "anthropic" and not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        raise SystemExit(
            "Anthropic authentication missing. Set ANTHROPIC_API_KEY "
            "or ANTHROPIC_AUTH_TOKEN before running ai_screening.py."
        )

    # Initialize Anthropic client
    client = Anthropic() if args.backend == "anthropic" else None

    # Process in batches
    batch_size = args.batch_size
    total_to_process = len(unscreened)
    processed = 0
    includes = 0
    excludes = 0
    uncertains = 0

    print(f"\nScreening {total_to_process} records in batches of {batch_size}...")
    print()

    indices = unscreened.index.tolist()

    for batch_start in range(0, total_to_process, batch_size):
        batch_end = min(batch_start + batch_size, total_to_process)
        batch_indices = indices[batch_start:batch_end]
        batch_df = df.loc[batch_indices]
        n = len(batch_df)

        # Format records
        records_text = "\n".join(
            format_record_for_screening(row, i + 1)
            for i, (_, row) in enumerate(batch_df.iterrows())
        )

        # Screen batch
        try:
            if args.backend == "codex":
                results = screen_batch_codex(records_text, n)
            else:
                results = screen_batch(client, records_text, n)

            # Apply results
            for i, (idx, _) in enumerate(batch_df.iterrows()):
                if i < len(results):
                    r = results[i]
                    decision = normalize_decision(r.get("decision", "UNCERTAIN"))
                    confidence = normalize_confidence(r.get("confidence", "low"))
                    df.at[idx, "AI_Decision"] = decision
                    df.at[idx, "AI_Reasoning"] = r.get("reasoning", "")
                    df.at[idx, "AI_Confidence"] = confidence

                    if decision == "INCLUDE":
                        includes += 1
                    elif decision == "EXCLUDE":
                        excludes += 1
                    else:
                        uncertains += 1

            processed += n

            # Progress
            pct = processed / total_to_process * 100
            print(
                f"  Batch {batch_start // batch_size + 1}: "
                f"{processed}/{total_to_process} ({pct:.0f}%) | "
                f"Inc={includes} Exc={excludes} Unc={uncertains}"
            )

            # Save progress after each batch
            df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  ERROR on batch starting at {batch_start}: {e}")
            # Mark batch as uncertain
            for idx, _ in batch_df.iterrows():
                df.at[idx, "AI_Decision"] = "UNCERTAIN"
                df.at[idx, "AI_Reasoning"] = f"Error: {str(e)[:100]}"
                df.at[idx, "AI_Confidence"] = "low"
                uncertains += 1
            processed += n
            df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
            time.sleep(2)

    # Final save
    df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)

    # Summary
    print()
    print("=" * 70)
    print("SCREENING SUMMARY")
    print("=" * 70)
    all_decisions = df["AI_Decision"].value_counts()
    for decision, count in all_decisions.items():
        print(f"  {decision:15s} {count:5d} ({count/total*100:.1f}%)")
    print(f"  {'TOTAL':15s} {total:5d}")
    print()

    # Domain breakdown for includes
    inc_df = df[df["AI_Decision"] == "INCLUDE"]
    if len(inc_df) > 0:
        print(f"Included records by domain:")
        domain_counts = inc_df["Domain_Searches"].str.split("; ").explode().value_counts()
        for domain, count in domain_counts.head(15).items():
            print(f"  {domain:35s} {count:4d}")

    print()
    print(f"Output saved to: {output_path}")
    print()
    print("Next steps:")
    print("  1. Run screening_analysis.py for PRISMA flow numbers")
    print("  2. Have MDs review INCLUDE + UNCERTAIN records")
    print("  3. Have MDs verify 20% random sample of EXCLUDE records")


if __name__ == "__main__":
    main()
