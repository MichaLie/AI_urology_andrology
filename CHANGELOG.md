# Changelog

## v1.3.0 — 23 August 2026

- Replaced the prior analytic corpus with the final 2,892-record corpus after corpus-wide rule-assisted eligibility verification, renal and nephrology boundary checking, an author-led rule-coverage check, and final PubMed language-metadata and case-report boundary checks.
- Added the complete 1,270-record final eligibility-verification table.
- Added triggering rule identifiers, evidence levels, and record-specific rationales to the final verification table.
- Applied 20 additional removals and four operational-analysis-group corrections identified by the retained-set rule-coverage check.
- Excluded 40 publications without an English code in official PubMed XML metadata under E09 and documented two retained case-report-labelled records with substantive AI validation.
- Recast the ten mutually exclusive groups as descriptive operational analysis groups, named `Search_Query_Tags` as the authoritative retrieval-provenance field, documented the 13 author-verified content corrections, renamed the former Governance group, and disclosed that the historical single-group assignment rule and random-audit seed/command were not retained.
- Added a frozen primary-source boundary-evidence table for 40 language exclusions, two case-report exceptions, and three full-text scope confirmations.
- Updated the screening database, included-record table, journal counts, publication trends, operational-analysis-group totals, PRISMA flow, and review-burden tables.
- Corrected review-type parsing to include Review, Systematic Review, Scoping Review, Meta-Analysis, and Network Meta-Analysis labels.
- Made Figure 2 bubble area proportional to the number of qualifying primary prospective or validation anchors.
- Harmonized Figure 3 with the readiness-tier table and separated contextual implementation exemplars in a dashed, non-ranked box.
- Added the empty Stage 6 axis position to Figure 2 and recast autonomous LLM advice as a cross-cutting safety boundary rather than a separately staged use case in Figure 3.
- Corrected three readiness stages, the prostate MRI qualifying-anchor count, and the placement of retrieval-grounded guideline support.
- Replaced legacy figure builders with the print-legible submission figure code.
- Added exact submission/repository checksum mapping, local release validation, Zenodo metadata, and v1.3.0 release notes.
- Added deterministic public archive reconstruction, per-file DOI propagation
  checks, spreadsheet-safe live CSV exports with raw JSONL provenance, and
  nonblank portable-figure validation.
- Hardened clean-room execution against Python cache artifacts, bound DOI
  checks to structured metadata types, added an explicit synchronized licence
  gate, preserved raw harvest text through screening, and blocked archive
  outputs from colliding with repository sources.
- Bound licence-file content by SPDX marker and SHA-256, required exact CFF DOI
  scalar values, and made archive/evidence sidecar writes atomic and resistant
  to symlink redirection.
- Required licence files to be regular in-repository files with exactly one
  SPDX marker and made both archive builders include the exact profile-bound
  licence bytes, keeping standalone and archived publication readiness aligned.

## v1.2.2 — 2 July 2026

- Archived the earlier minor-revision package based on the 3,352-record analytic corpus.
