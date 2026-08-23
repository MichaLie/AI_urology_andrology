# Release notes — v1.3.0

Version `v1.3.0` is the reproducibility release corresponding to the final revised manuscript.

The central change is replacement of the earlier 3,352-record corpus with the final 2,892-record analytic corpus following a complete rule-assisted eligibility sensitivity workflow, including renal and nephrology boundary checking, an author-led rule-coverage check, and final PubMed language-metadata and case-report boundary checks. The release adds the 1,270-record final verification table and propagates its decisions through every corpus-dependent table and figure.

Key release totals are:

- 2,082 records retained outside the verification table;
- 797 verified records confirmed eligible;
- 13 operational-analysis-group corrections retained;
- 106 context-only records removed from analytic counts;
- 354 records excluded;
- 2,892 records in the final analytic corpus.

The retained-set check produced 20 further removals and four additional operational-analysis-group corrections relative to the preceding internal corpus build. A complete title-pattern language-boundary scan of the 2,932 provisional records then identified 44 bracket-initial titles. Four used radionuclide notation and remained eligible; official PubMed XML confirmed that the remaining 40 publications lacked an English language code. Thirteen were already represented in the verification table and 27 were newly added; all 40 were excluded under E09. Two case-report-labelled records were also added to the verification table and retained because their PubMed abstract or PMC full text documented substantive AI validation. Primary full text or publisher material was used for borderline records when title and abstract evidence was insufficient. The released verification table records the triggering rule identifier(s), evidence level, and record-specific rationale for every reviewed record. A separate frozen boundary-evidence table records the decisive extracted fields, primary locators, and author-held capture-file hashes for the 40 language decisions, two case-report exceptions, and three full-text scope confirmations; the raw XML captures are not redistributed in the public archive.

The final corpus contains 468 review-type records and 96 Comment, Letter, or Editorial records; 564 records carry either classification. Excluding the deliberately broad synthesis stratum, 205/2,628 records (7.8%) are review-type.

The ten retained groups are now named and documented as operational analysis groups. `Operational_Analysis_Group` is a descriptive summary variable initialized from the recorded primary search-stream assignment and corrected for 13 author-verified content mismatches. `Search_Query_Tags` is the authoritative retrieval-provenance field. Operational-group totals are not query-route shares, clinical-content prevalence estimates, or a formal clinical taxonomy. The prior `Governance` label is therefore reported as `Implementation/ethics/reporting search stream`. The historical single-primary-group assignment rule was not retained and cannot be reconstructed deterministically. The seed and exact command used for the historical random AI-exclusion audit sample were likewise not retained; sample membership and decisions remain recorded.

The readiness evidence remains based on 38 in-corpus anchors across 16 use cases. Eight extracorpus contextual exemplars are explicitly separated from corpus counts. Figure 2 uses prospective-or-validation anchor counts for bubble area and now displays the complete six-stage framework, with no mapped use case at Stage 6. Figure 3 distinguishes the four corpus-supported readiness tiers from a separate dashed contextual box; autonomous LLM advice is shown as a cross-cutting safety boundary rather than a separately staged area. A rule-consistency review corrected the stages for micro-ultrasound, renal radiomics, and retrieval-grounded guideline support, and corrected the prostate MRI qualifying-anchor count from three to two.

The eleven supplementary-data CSVs and five source-data CSVs correspond byte for byte to the journal-submission tables; `SUBMISSION_FILE_MAP.csv` documents their public repository paths and checksums.

Release hardening in `v1.3.0` also adds a self-contained deterministic archive
builder, raw-JSONL provenance plus spreadsheet-safe CSV views for live PubMed
and AI-screening outputs, adversarial formula-prefix tests, nonblank portable
PNG validation, and per-file validation of the reserved version-specific Zenodo
DOI across all required metadata files.

The final local hardening pass additionally prevents Python cache creation
during documented validation and rebuild commands, requires DOI-typed CFF and
top-level Zenodo version identifiers, validates one explicit author-approved
licence profile across every declaration, preserves raw harvested text through
the screening handoff, uses one shared formula-risk predicate, and rejects
release-archive outputs that resolve inside the source repository.
Licence-file bytes are bound by SHA-256 and SPDX markers, DOI values must be
exact structured scalars, and atomic sidecar writes reject pre-existing
symlinks before any source can be modified.
The licence gate also rejects redirected files and duplicate SPDX marker lines.
When an approved licence profile is supplied, both archive builders include every profile-bound licence file byte for byte and the clean-extraction regression validates the resulting archive under the same profile.
